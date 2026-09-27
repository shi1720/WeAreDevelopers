"""Recurring amendment contract: identity, exclusions, retries and atomic failure."""
import unittest
from independent_series import IndependentSeries


class IndependentSeriesAmend(IndependentSeries):
    def amend_path(self,s): return '/series/'+s['series_id']+'/amend'

    def test_collective_change_is_not_exception_and_roundtrips(self):
        anchor=self.create(); s=self.adopt(anchor)
        body={'expected_revision':1,'from_index':0,'local_time':'20:00'}
        result=self.expect(201,'POST',self.amend_path(s),body,self.a,'amend')
        self.assertEqual(result['revision'],2)
        for old,new in zip(s['occurrences'],result['occurrences']):
            self.assertFalse(new['exception'])
            self.assertEqual(new['reference'],old['reference'])
            self.assertEqual(new['reservation']['starts_at_local'],old['reservation']['starts_at_local'][:11]+'20:00')
            self.assertEqual(new['reservation']['revision'],2)
            self.assertEqual(self.history(new['reservation'])[-1]['event'],'changed')
        exported=self.snapshot(); self.expect(204,'POST','/_test/import',exported)
        self.assertEqual(result,self.current(s))
        self.assertEqual(result,self.expect(200,'POST',self.amend_path(s),body,self.a,'amend'))
        self.assertEqual(anchor,self.expect(200,'POST','/reservations',self.booking(),self.a,'create'))

    def test_skip_permanent_exception_and_cancelled_then_empty_noop(self):
        s=self.adopt(self.create())
        refs=[o['reference'] for o in s['occurrences']]
        self.expect(200,'PATCH','/reservations/'+refs[1],{'party_size':1},self.a)
        self.expect(200,'POST','/reservations/'+refs[2]+'/cancel',{},self.a)
        current=self.current(s)
        result=self.expect(201,'POST',self.amend_path(s),{'expected_revision':3,'from_index':0,'local_time':'20:00'},self.a,'a')
        self.assertEqual(result['revision'],4)
        self.assertEqual(result['occurrences'][1:],current['occurrences'][1:])
        before=self.snapshot()
        empty=self.expect(201,'POST',self.amend_path(s),{'expected_revision':4,'from_index':1,'local_time':'21:00'},self.a,'empty')
        self.assertEqual(empty,result)
        noop=self.expect(201,'POST',self.amend_path(s),{'expected_revision':4,'from_index':0,'local_time':'20:00'},self.a,'noop')
        self.assertEqual(noop,result)

    def test_conflict_rollback_and_same_key_retry(self):
        s=self.adopt(self.create())
        blocker=self.create(key='block',local='2032-07-01T20:00')
        body={'expected_revision':1,'from_index':0,'local_time':'20:00'}
        before=self.snapshot()
        self.expect(409,'POST',self.amend_path(s),body,self.a,'a','table_unavailable')
        self.assertTrue(before==self.snapshot())
        self.expect(200,'POST','/reservations/'+blocker['reference']+'/cancel',{},self.a)
        self.expect(201,'POST',self.amend_path(s),body,self.a,'a')

    def test_validation_permissions_and_fifty_revision_contenders(self):
        s=self.adopt(self.create()); path=self.amend_path(s)
        body={'expected_revision':1,'from_index':0,'local_time':'20:00'}
        self.expect(401,'POST',path,body,key='a',code='unauthenticated')
        self.expect(404,'POST',path,body,self.b,'a','not_found')
        for field,values in {'expected_revision':[True,0,-1,'1'], 'from_index':[False,-1,3,'0'], 'local_time':['2:00','24:00','20:00:00',True]}.items():
            for value in values:
                self.expect(422,'POST',path,dict(body,**{field:value}),self.a,'a','validation_failed')
        results=self.concurrent(50,lambda i:self.request('POST',path,body,self.a,'race-'+str(i)))
        self.assertEqual(sum(s==201 for s,b in results),1)
        self.assertTrue(all(s==201 or (s==409 and b['error']['code']=='stale_revision') for s,b in results))
        self.assertEqual(self.current(s)['revision'],2)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IndependentSeriesAmend(name) for name in IndependentSeriesAmend.__dict__ if name.startswith('test_'))
