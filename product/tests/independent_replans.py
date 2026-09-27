"""Closure contract checks against an independently enumerated optimum."""
import unittest
import random
from independent_policies import IndependentPolicies, policy_fixture
from independent_planner_oracle import solve


class IndependentReplans(IndependentPolicies):
    path = '/restaurants/r-independent/replans'

    def closure(self, table='table-z', start='18:00', end='19:00'):
        return {'table_id': table, 'from': '2032-06-17T'+start+':00+00:00', 'to': '2032-06-17T'+end+':00+00:00'}

    def preview(self, body=None, key='preview'):
        return self.expect(201, 'POST', self.path, body or self.closure(), self.b, key)

    def apply(self, plan, key='apply'):
        return self.expect(201, 'POST', self.path+'/'+plan['plan_id']+'/apply', {}, self.b, key)

    def test_optimum_preview_purity_apply_history_receipts_and_roundtrip(self):
        a = self.create(); b = self.create(key='b', table='table-a', party=3)
        records = [a,b]; histories = [self.history(r) for r in records]
        expected = solve(policy_fixture()['restaurants'][0], records, self.closure())
        plan = self.preview()
        for field in expected: self.assertEqual(plan[field], expected[field])
        self.assertEqual(plan['restaurant_revision'], 2)
        for r,h in zip(records,histories):
            self.assertEqual(self.history(r), h)
            self.assertEqual(self.expect(200,'GET','/reservations/'+r['reference'],token=self.a), r)
        self.assertEqual(plan,self.expect(200,'POST',self.path,self.closure(),self.b,'preview'))
        result = self.apply(plan)
        self.assertEqual(result['restaurant_revision'],3)
        old = {r['reference']:r for r in records}
        for r in result['reservations']:
            previous = old[r['reference']]
            changed = r['table_ids'] != previous['table_ids']
            for field in ('starts_at','ends_at','accepted_terms','party_size','reservation_id','created_at'):
                self.assertEqual(r[field],previous[field])
            self.assertEqual(r['revision'],previous['revision']+int(changed))
            if changed:
                event=self.history(r)[-1]
                self.assertEqual(event['event'],'reassigned')
                self.assertEqual(event['plan_id'],plan['plan_id'])
                self.assertEqual(event['changes'],[{'field':'table_ids','from':previous['table_ids'],'to':r['table_ids']}])
        self.expect(409,'POST',self.path+'/'+plan['plan_id']+'/apply',{},self.b,'other','plan_already_applied')
        self.assertEqual(result,self.expect(200,'POST',self.path+'/'+plan['plan_id']+'/apply',{},self.b,'apply'))
        self.expect(409,'POST','/reservations',self.booking(),self.a,'blocked','table_unavailable')
        exported=self.snapshot(); self.expect(204,'POST','/_test/import',exported)
        self.assertEqual(result,self.expect(200,'POST',self.path+'/'+plan['plan_id']+'/apply',{},self.b,'apply'))
        self.assertEqual(a,self.expect(200,'POST','/reservations',self.booking(),self.a,'create'))

    def test_impossible_plan_failure_is_atomic_and_key_reusable(self):
        for i,t in enumerate(['table-z','table-a','table-m']): self.create(key=str(i),table=t)
        before=self.snapshot()
        self.expect(409,'POST',self.path,self.closure(),self.b,'p','no_feasible_plan')
        self.assertTrue(before==self.snapshot())
        self.preview(self.closure(start='20:00',end='21:00'),key='p')

    def test_fifty_concurrent_apply_exactly_once(self):
        self.create(); plan=self.preview(); path=self.path+'/'+plan['plan_id']+'/apply'
        results=self.concurrent(50,lambda i:self.request('POST',path,{},self.b,'same'))
        self.assertEqual(sum(s==201 for s,b in results),1)
        self.assertTrue(all(s in (200,201) for s,b in results))
        self.assertTrue(all(b==results[0][1] for s,b in results))

    def test_stale_plan_after_real_change_but_not_noop(self):
        r=self.create(); plan=self.preview()
        self.expect(200,'PATCH','/reservations/'+r['reference'],{'party_size':2},self.a)
        self.assertEqual(self.preview(key='second')['restaurant_revision'],plan['restaurant_revision'])
        self.expect(200,'PATCH','/reservations/'+r['reference'],{'party_size':1},self.a)
        before=self.snapshot()
        self.expect(409,'POST',self.path+'/'+plan['plan_id']+'/apply',{},self.b,'apply','stale_plan')
        self.assertTrue(before==self.snapshot())

    def test_generated_six_table_four_pair_six_booking_oracle(self):
        rng=random.Random(49017)
        for case in range(24):
            data=policy_fixture(); restaurant=data['restaurants'][0]
            restaurant['tables']=[{'id':'seat-'+str(i),'label':'Seat '+str(i),'capacity':rng.randint(2,6)} for i in range(6)]
            restaurant['combinable']=[['seat-1','seat-0'],['seat-2','seat-1'],['seat-4','seat-3'],['seat-5','seat-4']]
            self.reset(data); self.a=self.login(); self.b=self.login('bea@example.test')
            records=[]
            for i,t in enumerate(restaurant['tables']):
                records.append(self.create(key='r'+str(i),table=t['id'],party=rng.randint(1,t['capacity']),local='2032-06-17T'+rng.choice(['17:30','18:00','18:30','19:00'])))
            closure=self.closure(table='seat-'+str(case%6),start='18:00',end='19:00')
            expected=solve(restaurant,records,closure)
            before=self.snapshot()
            if expected is None:
                self.expect(409,'POST',self.path,closure,self.b,'oracle','no_feasible_plan')
                self.assertTrue(before==self.snapshot())
            else:
                plan=self.preview(closure,'oracle')
                for field in expected: self.assertEqual(plan[field],expected[field],f'case {case}: {field}')

    def test_closure_half_open_edges_and_explanations(self):
        plan=self.preview(); self.apply(plan)
        self.create(key='before',local='2032-06-17T17:00')
        self.create(key='after',local='2032-06-17T19:00')
        self.expect(409,'POST','/reservations',self.booking(local='2032-06-17T17:30'),self.a,'inside','table_unavailable')
        slot=next(s for s in self.availability(explain='true')['slots'] if s['starts_at_local'].endswith('18:00'))
        row=next(r for r in slot['explain'] if r['table_id']=='table-z')
        self.assertEqual(row['rules'],[{'rule':'capacity','holds':True},{'rule':'no_overlap','holds':False}])
        self.assertTrue(all('table-z' not in o['table_ids'] for o in slot['available_options']))

    def test_prior_closure_and_historical_capacity_constrain_repair(self):
        prior=self.closure(table='table-a'); self.apply(self.preview(prior))
        original=self.create(party=2)
        self.publish(capacities={'table-z':1,'table-a':1,'table-m':1})
        expected=solve(policy_fixture()['restaurants'][0],[original],self.closure(),[prior])
        plan=self.preview(key='next')
        for field in expected: self.assertEqual(plan[field],expected[field])
        result=self.apply(plan,key='next-apply')['reservations'][0]
        self.assertEqual(result['table_ids'],['table-m'])
        self.assertEqual(result['accepted_terms'],original['accepted_terms'])

    def test_repairs_ignore_guest_cutoff(self):
        original=self.create(local='2001-01-01T18:00')
        body={'table_id':'table-z','from':'2001-01-01T18:00:00+00:00','to':'2001-01-01T19:00:00+00:00'}
        plan=self.preview(body); result=self.apply(plan)
        self.assertEqual(result['reservations'][0]['starts_at'],original['starts_at'])
        self.assertEqual(result['reservations'][0]['status'],'confirmed')

    def test_preview_permissions_intervals_and_failed_key_reuse(self):
        self.expect(401,'POST',self.path,self.closure(),key='p',code='unauthenticated')
        self.expect(403,'POST',self.path,self.closure(),self.a,'p','forbidden')
        self.expect(404,'POST',self.path,self.closure(table='missing'),self.b,'p','not_found')
        before=self.snapshot()
        for value in [dict(self.closure(),to=self.closure()['from']),dict(self.closure(),to='2032-06-17T17:00:00Z'),dict(self.closure(),**{'from':'2032-06-17T18:00:00'}),dict(self.closure(),to='not-a-date')]:
            self.expect(422,'POST',self.path,value,self.b,'p','validation_failed')
            self.assertTrue(before==self.snapshot())
        self.preview(key='p')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IndependentReplans(name) for name in IndependentReplans.__dict__ if name.startswith('test_'))
