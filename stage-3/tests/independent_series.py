"""Recurring agreements: spec-derived identity, rollback and revision checks."""
import calendar
import copy
from datetime import date,timedelta
import unittest
from independent_policies import IndependentPolicies,policy_fixture


class IndependentSeries(IndependentPolicies):
    def adopt(self,anchor,count=3,interval=1,key='series'):
        return self.expect(201,'POST','/series',dict(anchor_reference=anchor['reference'],count=count,interval_weeks=interval),self.a,key)

    def current(self,series):
        return self.expect(200,'GET','/series/'+series['series_id'],token=self.a)

    def test_anchor_identity_history_and_max_count_interval(self):
        anchor=self.create(); history=self.history(anchor)
        result=self.adopt(anchor,12,4)
        self.assertEqual(result['revision'],1)
        self.assertEqual(result['interval_weeks'],4)
        self.assertEqual(len(result['occurrences']),12)
        self.assertEqual(result['occurrences'][0]['reservation'],anchor)
        self.assertEqual(self.history(anchor),history)
        self.assertEqual(len({o['reference'] for o in result['occurrences']}),12)
        for i,occ in enumerate(result['occurrences']):
            self.assertEqual(occ['index'],i); self.assertFalse(occ['exception'])
            self.assertEqual(occ['reservation']['starts_at_local'],str(date(2032,6,17)+timedelta(days=i*28))+'T18:00')
            self.assertEqual(occ['reservation']['revision'],1)
            self.assertEqual(len(self.history(occ['reservation'])),1)
        self.assertEqual(anchor,self.expect(200,'POST','/reservations',self.booking(),self.a,'create'))
        for token in (None,self.b):
            self.expect(404,'GET','/series/'+result['series_id'],token=token,code='not_found')

    def test_occurrence_exceptions_cancel_and_original_series_receipt(self):
        anchor=self.create(); result=self.adopt(anchor)
        ref=result['occurrences'][1]['reference']; path='/reservations/'+ref
        self.expect(200,'PATCH',path,{'party_size':2},self.a)
        self.assertEqual(self.current(result)['revision'],1)
        self.expect(200,'PATCH',path,{'party_size':1},self.a)
        now=self.current(result); self.assertEqual(now['revision'],2)
        self.assertTrue(now['occurrences'][1]['exception'])
        self.expect(200,'PATCH',path,{'party_size':2},self.a)
        self.assertTrue(self.current(result)['occurrences'][1]['exception'])
        self.expect(200,'POST','/reservations/'+anchor['reference']+'/cancel',{},self.a)
        now=self.current(result); self.assertEqual(now['revision'],4)
        self.assertFalse(now['occurrences'][0]['exception'])
        self.assertEqual(now['occurrences'][2]['reservation']['status'],'confirmed')
        self.expect(200,'POST','/reservations/'+anchor['reference']+'/cancel',{},self.a)
        self.assertEqual(now,self.current(result))
        body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
        self.assertEqual(result,self.expect(200,'POST','/series',body,self.a,'series'))

    def test_adoption_validation_permissions_and_failed_keys(self):
        anchor=self.create(); body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
        self.expect(401,'POST','/series',body,key='s',code='unauthenticated')
        self.expect(404,'POST','/series',body,self.b,'s','not_found')
        before=self.snapshot()
        for field,values in [('count',[True,1,13,'3',3.5]),('interval_weeks',[False,0,5,'1',1.5])]:
            for value in values:
                self.expect(422,'POST','/series',dict(body,**{field:value}),self.a,'s','validation_failed')
                self.assertTrue(before==self.snapshot())
        self.adopt(anchor,key='s')
        self.expect(409,'POST','/series',body,self.a,'new','already_in_series')

    def test_occurrence_policy_selection_and_full_failure_rollback(self):
        anchor=self.create(); self.publish(date='2032-06-24',reservation_duration_minutes=120)
        blocker=self.create(key='blocker',local='2032-07-01T18:00')
        before=self.snapshot()
        self.expect(409,'POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),self.a,'s','table_unavailable')
        self.assertTrue(before==self.snapshot())
        self.expect(200,'POST','/reservations/'+blocker['reference']+'/cancel',{},self.a)
        series=self.adopt(anchor,key='s')
        self.assertEqual([o['reservation']['accepted_terms']['policy_version'] for o in series['occurrences']],[0,1,1])
        self.assertEqual(series['occurrences'][0]['reservation'],anchor)

    def test_recurring_gap_rollback_and_first_fold(self):
        for month,clock,expect_error in [(3,'02:30',True),(11,'01:30',False)]:
            fixture=policy_fixture(); fixture['restaurants'][0]['timezone']='America/New_York'
            self.reset(fixture); self.a,self.b=self.login(),self.login('bea@example.test')
            sundays=[w[calendar.SUNDAY] for w in calendar.monthcalendar(2032,month) if w[calendar.SUNDAY]]
            transition=date(2032,month,sundays[1 if month==3 else 0]); start=transition-timedelta(days=7)
            anchor=self.create(local=str(start)+'T'+clock); before=self.snapshot()
            if expect_error:
                self.expect(422,'POST','/series',dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1),self.a,'s','invalid_local_time')
                self.assertTrue(before==self.snapshot())
            else:
                series=self.adopt(anchor,count=2,key='s')
                self.assertTrue(series['occurrences'][1]['reservation']['starts_at'].endswith('-04:00'))

    def test_collective_moves_once_per_series_and_rollback(self):
        anchor=self.create(); series=self.adopt(anchor)
        occurrences=series['occurrences']
        moves={'moves':[{'reference':o['reference'],'table_id':'table-a','expected_revision':1} for o in occurrences[:2]]}
        changed=self.expect(201,'POST','/reservation-moves',moves,self.a,'moves')
        now=self.current(series); self.assertEqual(now['revision'],2)
        self.assertEqual([o['exception'] for o in now['occurrences']],[True,True,False])
        self.assertEqual([o['reservation']['revision'] for o in now['occurrences']],[2,2,1])
        self.assertEqual(changed,self.expect(200,'POST','/reservation-moves',moves,self.a,'moves'))
        self.assertEqual(now,self.current(series))
        bad={'moves':[{'reference':occurrences[0]['reference'],'party_size':1,'expected_revision':2},
                      {'reference':occurrences[1]['reference'],'party_size':1,'expected_revision':1}]}
        before=self.snapshot()
        self.expect(409,'POST','/reservation-moves',bad,self.a,'failed','stale_revision')
        self.assertTrue(before==self.snapshot())
        exported=self.snapshot()
        self.reset(); self.expect(204,'POST','/_test/import',exported)
        self.assertEqual(now,self.current(series))
        self.assertEqual(changed,self.expect(200,'POST','/reservation-moves',moves,self.a,'moves'))


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IndependentSeries(name) for name in IndependentSeries.__dict__ if name.startswith('test_'))
