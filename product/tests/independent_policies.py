"""Stage-3 policy/history checks derived from the contract before source review."""
import copy
import unittest
from independent_combinations import IndependentCombinations, combination_fixture


def policy_fixture():
    data = combination_fixture()
    data['restaurants'][0]['manager_user_ids'] = ['user-b']
    return data


class IndependentPolicies(IndependentCombinations):
    def setUp(self):
        self.reset(policy_fixture())
        self.a, self.b = self.login(), self.login('bea@example.test')

    def policy(self, date='2032-06-01', **changes):
        value = dict(effective_from=date, slot_minutes=30, reservation_duration_minutes=90,
                     cancellation_cutoff_minutes=0,
                     opening_hours=policy_fixture()['restaurants'][0]['opening_hours'],
                     capacities={'table-z': 2, 'table-a': 4, 'table-m': 8})
        value.update(changes)
        return value

    def publish(self, key='policy', **changes):
        return self.expect(201, 'POST', '/restaurants/r-independent/policies',
                           self.policy(**changes), self.b, key)

    def history(self, reservation):
        return self.expect(200, 'GET', '/reservations/' + reservation['reference'] + '/history', token=self.a)['entries']

    def test_policy_permissions_and_invalid_values_leave_no_version(self):
        path = '/restaurants/r-independent/policies'
        self.expect(401, 'POST', path, self.policy(), key='p', code='unauthenticated')
        self.expect(403, 'POST', path, self.policy(), self.a, 'p', 'forbidden')
        self.expect(404, 'POST', '/restaurants/absent/policies', self.policy(), self.b, 'p', 'not_found')
        invalid = [dict(self.policy(), **{field: value}) for field, values in {
            'slot_minutes': [True, 0, 1441, '30'],
            'reservation_duration_minutes': [False, 0, 1441, None],
            'cancellation_cutoff_minutes': [True, -1, 10081, 1.5],
            'effective_from': ['2032-02-30', '2032-6-01', '2032-06-01T00:00'],
            'capacities': [{}, {'table-z': 2, 'table-a': 4, 'table-m': True}, {'table-z': 2, 'table-a': 4, 'table-m': 101}],
        }.items() for value in values]
        for field in self.policy():
            value = self.policy(); del value[field]; invalid.append(value)
        invalid.append(dict(self.policy(), opening_hours=[{'weekday':'mon','opens':'18:00','closes':'23:00'}] * 2))
        before = self.snapshot()
        for value in invalid:
            self.expect(422, 'POST', path, value, self.b, 'p', 'validation_failed')
            self.assertTrue(before == self.snapshot())
        result = self.publish('p', slot_minutes=1440, reservation_duration_minutes=1440,
                              cancellation_cutoff_minutes=10080,
                              capacities={'table-z':1,'table-a':100,'table-m':8})
        self.assertEqual(result['policy_version'], 1)

    def test_effective_date_ties_publication_order_and_original_detail(self):
        detail = self.expect(200, 'GET', '/restaurants/r-independent')
        p1 = self.publish('p1', date='2032-06-20', reservation_duration_minutes=120)
        p2 = self.publish('p2', date='2032-06-01', reservation_duration_minutes=30)
        p3 = self.publish('p3', date='2032-06-20', reservation_duration_minutes=60)
        self.assertEqual(self.expect(200,'GET','/restaurants/r-independent/policies')['policies'], [p1,p2,p3])
        self.assertEqual(detail, self.expect(200,'GET','/restaurants/r-independent'))
        for index,(day,version) in enumerate([('2032-05-31',0),('2032-06-19',2),('2032-06-20',3)]):
            r=self.create(key=str(index), local=day+'T18:00')
            self.assertEqual(r['accepted_terms']['policy_version'],version)
        self.assertEqual(p3,self.expect(200,'POST','/restaurants/r-independent/policies',
                         self.policy(date='2032-06-20',reservation_duration_minutes=60),self.b,'p3'))

    def test_terms_history_noop_amend_cancel_and_original_receipt(self):
        original=self.create(); initial=self.history(original)
        self.assertEqual(original['revision'],1)
        self.assertEqual([c['field'] for c in initial[0]['changes']],['table_id','starts_at_local','party_size'])
        self.assertTrue(all(c['from'] is None for c in initial[0]['changes']))
        self.publish(reservation_duration_minutes=120)
        path='/reservations/'+original['reference']
        self.assertEqual(original,self.expect(200,'PATCH',path,{'party_size':2},self.a))
        self.assertEqual(initial,self.history(original))
        changed=self.expect(200,'PATCH',path,{'table_id':'table-a','party_size':3},self.a)
        self.assertEqual(changed['revision'],2)
        self.assertEqual(changed['accepted_terms']['policy_version'],1)
        events=self.history(original)
        self.assertEqual([c['field'] for c in events[1]['changes']],['table_id','party_size'])
        self.assertEqual(events[0],initial[0])
        cancelled=self.expect(200,'POST',path+'/cancel',{},self.a)
        self.assertEqual(cancelled['revision'],3)
        self.assertEqual(cancelled,self.expect(200,'POST',path+'/cancel',{},self.a))
        events=self.history(original)
        self.assertEqual([e['seq'] for e in events],[1,2,3])
        self.assertEqual([e['revision'] for e in events],[1,2,3])
        self.assertEqual(events[-1]['changes'],[])
        self.assertEqual([e['at'] for e in events],sorted(e['at'] for e in events))
        self.assertEqual(original,self.expect(200,'POST','/reservations',self.booking(),self.a,'create'))
        self.assertEqual(events,self.history(original))

    def test_private_history_decision_and_expected_revision_precedence(self):
        r=self.create(local='2001-01-01T18:00'); path='/reservations/'+r['reference']
        for suffix in ('/history','/decision'):
            for token in (None,self.b,'invalid'):
                self.expect(404,'GET',path+suffix,token=token,code='not_found')
        decision=self.expect(200,'GET',path+'/decision',token=self.a)
        self.assertEqual(decision,dict(reference=r['reference'],revision=1,accepted_terms=r['accepted_terms']))
        self.expect(409,'PATCH',path,{'expected_revision':2,'party_size':False},self.a,code='stale_revision')
        for revision in (True,0,-1,'1',1.5):
            self.expect(422,'PATCH',path,{'expected_revision':revision},self.a,code='validation_failed')
        self.expect(409,'PATCH',path,{'expected_revision':1,'party_size':False},self.a,code='cutoff_passed')

    def test_revision_compare_and_swap_fifty_real_changes(self):
        r=self.create(table='table-m',party=1); path='/reservations/'+r['reference']
        results=self.concurrent(50,lambda i:self.request('PATCH',path,{'expected_revision':1,'party_size':2+i%6},self.a))
        self.assertEqual(sum(s==200 for s,b in results),1)
        self.assertTrue(all(s==200 or (s==409 and b['error']['code']=='stale_revision') for s,b in results))
        self.assertEqual(len(self.history(r)),2)

    def test_explanations_independent_rules_shape_and_policy(self):
        self.create(table='table-z')
        plain=self.availability(party=5)
        self.assertTrue(all('explain' not in s for s in plain['slots']))
        for invalid in ('false','1','','TRUE'):
            self.expect(422,'GET','/availability?restaurant_id=r-independent&date=2032-06-17&party_size=5&explain='+invalid,code='validation_failed')
        self.publish(capacities={'table-z':2,'table-a':6,'table-m':8})
        slot=next(s for s in self.availability(party=5,explain='true')['slots'] if s['starts_at_local'].endswith('18:00'))
        rows=slot['explain']
        self.assertEqual([r['table_id'] for r in rows],['table-z','table-a','table-m'])
        self.assertEqual(rows[0]['rules'],[{'rule':'capacity','holds':False},{'rule':'no_overlap','holds':False}])
        for row in rows:
            self.assertEqual(row['policy_version'],1)
            self.assertEqual([v['rule'] for v in row['rules']],['capacity','no_overlap'])
            self.assertEqual(row['available'],all(v['holds'] for v in row['rules']))
        self.assertEqual([r['table_id'] for r in rows if r['available']],slot['available_table_ids'])

    def test_combination_history_canonical_noop_and_policy_capacity(self):
        r=self.pair(party=2); path='/reservations/'+r['reference']
        initial=self.history(r)
        self.assertEqual(initial[0]['changes'][0],{'field':'table_ids','from':None,'to':['table-a','table-z']})
        self.publish(capacities={'table-z':1,'table-a':1,'table-m':8})
        self.assertEqual(r,self.expect(200,'PATCH',path,{'table_ids':['table-z','table-a']},self.a))
        self.assertEqual(initial,self.history(r))
        self.expect(422,'PATCH',path,{'party_size':3},self.a,code='party_exceeds_capacity')
        self.expect(200,'PATCH',path,{'table_id':'table-m'},self.a)
        event=self.history(r)[-1]
        self.assertEqual(event['changes'][0],{'field':'table_ids','from':['table-a','table-z'],'to':['table-m']})
        self.assertEqual(event['accepted_terms']['policy_version'],1)


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IndependentPolicies(name) for name in IndependentPolicies.__dict__ if name.startswith('test_'))
