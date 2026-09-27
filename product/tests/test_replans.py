"""Stage4 planner, transactional apply, series amendment and portable provenance."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import unittest
import test_policies_series as helpers
from tablekeeper.validation import APIError


class Stage4Tests(unittest.TestCase):
    setUp = helpers.PolicySeriesTests.setUp
    call = helpers.PolicySeriesTests.call
    book = helpers.PolicySeriesTests.book
    body = helpers.PolicySeriesTests.body
    error = helpers.PolicySeriesTests.error
    snapshot = helpers.PolicySeriesTests.snapshot
    history = helpers.PolicySeriesTests.history

    def preview(self, key='preview', **overrides):
        body = {'table_id': 'a', 'from': '2099-09-24T18:00:00+02:00', 'to': '2099-09-24T22:00:00+02:00'}
        body.update(overrides)
        return self.call('POST', '/restaurants/r/replans', body, key)

    def apply(self, plan, key='apply'):
        return self.call('POST', '/restaurants/r/replans/' + plan['plan_id'] + '/apply', {}, key)

    def adopt(self, count=3):
        anchor = self.book()
        return self.call('POST', '/series', {'anchor_reference': anchor['reference'], 'count': count, 'interval_weeks': 1}, 'adopt')[1]

    def amend_series(self, agreement, revision=1, first=0, clock='20:00', key='amend'):
        return self.call('POST', '/series/' + agreement['series_id'] + '/amend',
            {'expected_revision': revision, 'from_index': first, 'local_time': clock}, key)

    def test_preview_purity_apply_history_closure_and_receipts(self):
        old = self.book()
        before = self.snapshot()['state']
        _, plan = self.preview()
        after = self.snapshot()['state']
        for name in ('reservations', 'histories', 'restaurant_revisions', 'closures'):
            self.assertEqual(before[name], after[name])
        self.assertEqual(plan['moved_count'], 1)
        self.assertEqual(plan['assignments'][0]['table_ids'], ['b'])
        detail = self.call('GET', '/api/restaurants/r/replans/' + plan['plan_id'])[1]
        self.assertEqual(detail['before_reservations'], [old])
        self.assertEqual(self.preview(), (200, plan))
        _, applied = self.apply(plan)
        new = applied['reservations'][0]
        for name in ('starts_at', 'ends_at', 'starts_at_local', 'party_size', 'accepted_terms'):
            self.assertEqual(old[name], new[name])
        entry = self.history(old['reference'])[-1]
        self.assertEqual(entry['event'], 'reassigned')
        self.assertEqual(entry['changes'], [{'field': 'table_ids', 'from': ['a'], 'to': ['b']}])
        self.assertEqual(entry['plan_id'], plan['plan_id'])
        self.error(409, 'table_unavailable', lambda: self.book(key='blocked'))
        self.assertEqual(self.apply(plan), (200, applied))
        self.error(409, 'plan_already_applied', lambda: self.apply(plan, 'different'))
        exported = self.snapshot()
        self.assertEqual(self.call('POST', '/_test/import', exported)[0], 204)
        self.assertEqual(self.snapshot(), exported)

    def test_stale_and_no_feasible_are_atomic(self):
        self.book()
        _, plan = self.preview()
        self.book(key='other', local='2099-09-25T19:00')
        before = self.snapshot()
        self.error(409, 'stale_plan', lambda: self.apply(plan))
        self.assertEqual(before, self.snapshot())
        self.book(key='block', table='b')
        before = self.snapshot()
        self.error(409, 'no_feasible_plan', lambda: self.preview('impossible'))
        self.assertEqual(before, self.snapshot())

    def test_repair_ignores_cutoff_and_replay_survives_later_changes(self):
        from unittest.mock import patch
        from datetime import datetime, timezone
        old = self.book()
        with patch('tablekeeper.reservations.now', return_value=datetime(2100, 1, 1, tzinfo=timezone.utc)):
            _, plan = self.preview()
            _, applied = self.apply(plan)
        self.call('PATCH', '/reservations/' + old['reference'], {'party_size': 1})
        self.assertEqual(self.apply(plan), (200, applied))
        self.error(409, 'plan_already_applied', lambda: self.apply(plan, 'new-key'))
        self.call('POST', '/_test/import', self.snapshot())

    def test_planning_limit_and_corrupt_plan_roll_back(self):
        _, plan = self.preview()
        original = self.snapshot()
        for field, value in [('moved_count', 1), ('unused_seats', 1), ('assignments', [{'reference':'MISSING'}])]:
            bad = deepcopy(original)
            bad['state']['plans'][plan['plan_id']]['preview'][field] = value
            self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
            self.assertEqual(original, self.snapshot())
        from tablekeeper.planner import solve
        restaurant = {'id':'r', 'tables':[{'id':str(i)} for i in range(7)]}
        proposed = dict(plan['closure'], restaurant_id='r')
        self.error(422, 'planning_limit', lambda: solve(restaurant, [], [], proposed))

    def test_50_apply_replays_and_once_counters(self):
        self.book()
        _, plan = self.preview()
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda _: self.apply(plan), range(50)))
        self.assertEqual(sum(status == 201 for status, _ in results), 1)
        self.assertTrue(all(value == results[0][1] for _, value in results))
        self.assertEqual(len(self.snapshot()['state']['closures']), 1)
        self.assertEqual(self.snapshot()['state']['restaurant_revisions']['r'], 2)

    def test_series_collective_and_repair_preserve_exceptions_roundtrip(self):
        agreement = self.adopt(4)
        refs = [o['reference'] for o in agreement['occurrences']]
        self.call('PATCH', '/reservations/' + refs[1], {'party_size': 1})
        self.call('POST', '/reservations/' + refs[3] + '/cancel', {})
        _, changed = self.amend_series(agreement, revision=3)
        self.assertEqual(changed['revision'], 4)
        self.assertEqual([o['exception'] for o in changed['occurrences']], [False, True, False, False])
        self.assertEqual([o['reservation']['starts_at_local'][11:] for o in changed['occurrences']], ['20:00','19:00','20:00','19:00'])
        _, plan = self.preview()
        self.apply(plan)
        current = self.call('GET', '/series/' + agreement['series_id'])[1]
        self.assertEqual(current['revision'], 5)
        self.assertFalse(current['occurrences'][0]['exception'])
        exported = self.snapshot()
        self.call('POST', '/_test/import', exported)
        self.assertEqual(self.snapshot(), exported)
        self.assertEqual(self.amend_series(agreement, revision=3), (200, changed))
        bad = deepcopy(exported)
        bad['state']['series'][agreement['series_id']]['occurrences'][1]['exception'] = False
        self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
        self.assertEqual(self.snapshot(), exported)
        bad = deepcopy(exported)
        bad['state']['series_operations'] = []
        self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
        self.assertEqual(self.snapshot(), exported)

    def test_series_noop_empty_and_cas(self):
        agreement = self.adopt()
        _, unchanged = self.amend_series(agreement, clock='19:00')
        self.assertEqual(agreement, unchanged)
        with ThreadPoolExecutor(max_workers=2) as pool:
            def run(clock):
                try:
                    return self.amend_series(agreement, clock=clock, key=clock)[0]
                except APIError as error:
                    return error.code
            results = list(pool.map(run, ['20:00','20:30']))
        self.assertCountEqual(results, [201, 'stale_revision'])
        current = self.call('GET', '/series/' + agreement['series_id'])[1]
        for occurrence in current['occurrences']:
            self.call('POST', '/reservations/' + occurrence['reference'] + '/cancel', {})
        current = self.call('GET', '/series/' + agreement['series_id'])[1]
        self.assertEqual(self.amend_series(agreement, revision=current['revision'], key='empty')[1], current)
        self.call('POST', '/_test/import', self.snapshot())

    def test_series_failure_rolls_back_and_errors_precede_occupancy(self):
        agreement = self.adopt()
        self.book(key='block', local='2099-10-01T21:00')
        before = self.snapshot()
        self.error(409, 'table_unavailable', lambda: self.amend_series(agreement, clock='20:00'))
        self.assertEqual(self.snapshot(), before)
        self.error(422, 'outside_opening_hours', lambda: self.amend_series(agreement, clock='23:00'))
        self.assertEqual(self.snapshot(), before)

    def test_preview_permissions_intervals_and_empty_closure(self):
        self.error(403, 'forbidden', lambda: self.call('POST', '/restaurants/r/replans', {}, 'x', token=self.other))
        for values in [{'from': '2099-09-24T18:00'}, {'to': '2099-09-24T18:00:00+02:00'}, {'from': True}]:
            self.error(422, 'validation_failed', lambda: self.preview(**values))
        _, plan = self.preview()
        self.assertEqual(plan['assignments'], [])
        self.apply(plan)
        self.call('POST', '/_test/import', self.snapshot())

    def test_optimizer_objective_tiers_and_full_interval_fixed_booking(self):
        from tablekeeper.planner import solve
        from test_core import fixture
        restaurant = fixture()['restaurants'][0]
        restaurant['tables'] = [{'id': t, 'label': t, 'capacity': c} for t,c in [('a',4),('b',2),('c',2)]]
        restaurant['combinable'] = [['b','c']]
        def booking(ref, ids, start='19:00', end='20:30', size=2):
            return {'reference':ref,'restaurant_id':'r','status':'confirmed','table_ids':ids,'party_size':size,
                    'starts_at':'2099-09-24T'+start+':00+02:00','ends_at':'2099-09-24T'+end+':00+02:00',
                    'accepted_terms':{'capacities':{'a':4,'b':2,'c':2}}}
        closure = {'restaurant_id':'r','table_id':'a','from':'2099-09-24T19:30:00+02:00','to':'2099-09-24T20:00:00+02:00'}
        _, assignments, moved, unused = solve(restaurant, [booking('A',['a']), booking('B',['c'])], [], closure)
        self.assertEqual([a['table_ids'] for a in assignments], [['b'],['c']])
        self.assertEqual((moved,unused),(1,0))
        _, assignments, _, _ = solve(restaurant, [booking('A',['a'])], [], closure)
        self.assertEqual(assignments[0]['table_ids'], ['b'])  # equal unused seats: fixture rank
        fixed = booking('Z',['b'],'18:00','19:30')  # outside closure, overlaps full booking
        _, assignments, _, _ = solve(restaurant, [booking('A',['a']),fixed], [], closure)
        self.assertEqual(assignments[0]['table_ids'], ['c'])
        # A larger unchanged table outranks a smaller empty one: moves first.
        closure['table_id'] = 'c'
        _, assignments, moved, unused = solve(restaurant,[booking('A',['a'])],[],closure)
        self.assertEqual((assignments[0]['table_ids'],moved,unused),(['a'],0,2))

    def test_six_tables_four_pairs_six_nonoverlapping_bookings(self):
        from tablekeeper.planner import solve
        restaurant = {'id':'r','tables':[{'id':str(i)} for i in range(6)],
                      'combinable':[['0','1'],['1','2'],['2','3'],['3','4']]}
        bookings = [{'reference':str(i),'restaurant_id':'r','status':'confirmed','table_ids':['0'],
                     'party_size':1,'accepted_terms':{'capacities':{str(j):2 for j in range(6)}},
                     'starts_at':f'2099-09-24T{10+i:02d}:00:00+00:00',
                     'ends_at':f'2099-09-24T{11+i:02d}:00:00+00:00'} for i in range(6)]
        closure = {'restaurant_id':'r','table_id':'0','from':'2099-09-24T00:00:00+00:00','to':'2099-09-25T00:00:00+00:00'}
        _, assignments, moved, unused = solve(restaurant,bookings,[],closure)
        self.assertEqual([a['table_ids'] for a in assignments],[['1']]*6)
        self.assertEqual((moved,unused),(6,6))
