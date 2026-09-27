"""Additional contract transitions after complete source review."""
from datetime import datetime,timedelta,timezone
import unittest
from independent_series import IndependentSeries
from independent_policies import policy_fixture

class IndependentDeep(IndependentSeries):
    def test_accepted_cutoff_survives_policy_replacement(self):
        day=(datetime.now(timezone.utc)+timedelta(days=1)).date().isoformat()
        for original,new,expected in [(10080,0,409),(0,10080,200)]:
            fixture=policy_fixture();fixture['restaurants'][0]['cancellation_cutoff_minutes']=original
            self.reset(fixture);self.a,self.b=self.login(),self.login('bea@example.test')
            r=self.create(local=day+'T18:00');self.publish(date=day,cancellation_cutoff_minutes=new)
            path='/reservations/'+r['reference']
            if expected==409:
                self.expect(409,'PATCH',path,{'party_size':1},self.a,code='cutoff_passed')
            self.expect(expected,'POST',path+'/cancel',{},self.a,code='cutoff_passed' if expected==409 else None)

    def test_restaurant_and_multiple_series_counters_once(self):
        def rev():return self.snapshot()['state']['restaurant_revisions']['r-independent']
        self.assertEqual(rev(),0)
        a=self.create();self.assertEqual(rev(),1)
        sa=self.adopt(a);self.assertEqual(rev(),2)
        b=self.create(key='b',table='table-m');sb=self.adopt(b,key='sb');self.assertEqual(rev(),4)
        moves={'moves':[{'reference':o['reference'],'party_size':1} for o in sa['occurrences'][:2]+sb['occurrences'][:2]]}
        self.expect(201,'POST','/reservation-moves',moves,self.a,'m');self.assertEqual(rev(),5)
        self.assertEqual(self.current(sa)['revision'],2);self.assertEqual(self.current(sb)['revision'],2)
        self.expect(200,'POST','/reservation-moves',moves,self.a,'m');self.assertEqual(rev(),5)
        self.expect(201,'POST','/reservation-moves',moves,self.a,'noop');self.assertEqual(rev(),5)
        self.publish();self.assertEqual(rev(),6)
        self.expect(200,'POST','/reservations/'+a['reference']+'/cancel',{},self.a);self.assertEqual(rev(),7)

    def test_first_occurrence_failure_precedes_later_policy_failure(self):
        anchor=self.create()
        self.create(key='block',local='2032-06-24T18:00')
        self.publish(date='2032-07-01',capacities={'table-z':1,'table-a':4,'table-m':8})
        before=self.snapshot()
        self.expect(409,'POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),self.a,'s','table_unavailable')
        self.assertTrue(before==self.snapshot())

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IndependentDeep(name) for name in IndependentDeep.__dict__ if name.startswith('test_'))
