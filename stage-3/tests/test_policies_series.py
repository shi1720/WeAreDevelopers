"""Spec-derived policies, histories, agreement transitions and transaction tests."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tablekeeper.server import Application
from tablekeeper.validation import APIError
from test_core import fixture


class PolicySeriesTests(unittest.TestCase):
    def setUp(self):
        self.app = Application()
        f = fixture()
        f['restaurants'][0]['manager_user_ids'] = ['ada']
        f['restaurants'][0]['combinable'] = [['b', 'a']]
        self.call('POST', '/_test/reset', f)
        self.token = self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})[1]['token']
        self.other = self.call('POST', '/auth/login', {'email': 'ben@example.test', 'password': 'synthetic password'})[1]['token']

    def call(self, method, path, body=None, key=None, token=None, query=None):
        chosen = getattr(self, 'token', None) if token is None else token
        headers = {'Idempotency-Key': key}
        if chosen:
            headers['Authorization'] = 'Bearer ' + chosen
        return self.app.dispatch(method, path, query or {}, headers, body)

    def error(self, status, code, operation):
        with self.assertRaises(APIError) as result:
            operation()
        self.assertEqual((result.exception.status, result.exception.code), (status, code))

    def body(self, local='2099-09-24T19:00', table='a', size=2):
        return {'restaurant_id': 'r', 'table_id': table, 'party_size': size, 'starts_at_local': local}

    def book(self, key='book', **kw):
        return self.call('POST', '/reservations', self.body(**kw), key)[1]

    def policy(self, effective='2099-09-01', **overrides):
        value = {'effective_from': effective, 'slot_minutes': 30, 'reservation_duration_minutes': 120,
                 'cancellation_cutoff_minutes': 60, 'opening_hours': fixture()['restaurants'][0]['opening_hours'],
                 'capacities': {'a': 4, 'b': 6}}
        value.update(overrides)
        return value

    def publish(self, key='policy', **kw):
        return self.call('POST', '/restaurants/r/policies', self.policy(**kw), key)

    def snapshot(self):
        return self.call('GET', '/_test/export')[1]

    def history(self, ref):
        return self.call('GET', '/reservations/' + ref + '/history')[1]['entries']

    def test_effective_date_order_ties_and_immutable_original_terms(self):
        old = self.book()
        self.publish(effective='2099-09-20', reservation_duration_minutes=60)
        self.publish(key='earlier', effective='2099-09-01', reservation_duration_minutes=30)
        self.publish(key='tie', effective='2099-09-20', reservation_duration_minutes=120)
        fresh = self.book(key='fresh', table='b')
        self.assertEqual(fresh['accepted_terms']['policy_version'], 3)
        self.assertEqual(fresh['ends_at'][11:16], '21:00')
        self.assertEqual(self.call('GET', '/reservations/' + old['reference'])[1], old)
        self.assertEqual(self.call('POST', '/reservations', self.body(), 'book'), (200, old))
        self.assertEqual(self.call('GET', '/restaurants/r')[1]['reservation_duration_minutes'], 90)
        self.assertEqual([p['policy_version'] for p in self.call('GET', '/restaurants/r/policies')[1]['policies']], [1, 2, 3])

    def test_policy_validation_permissions_and_failed_versions(self):
        self.error(403, 'forbidden', lambda: self.call('POST', '/restaurants/r/policies', self.policy(), 'x', token=self.other))
        self.error(401, 'unauthenticated', lambda: self.call('POST', '/restaurants/r/policies', self.policy(), 'x', token=''))
        for field, value in [('slot_minutes', True), ('slot_minutes', 0), ('reservation_duration_minutes', 1441),
                             ('cancellation_cutoff_minutes', -1), ('capacities', {'a': 4}), ('effective_from', '2099-02-29'),
                             ('opening_hours', [{'weekday': 'mon', 'opens': '19:00', 'closes': '18:00'}])]:
            before = self.snapshot()
            self.error(422, 'validation_failed', lambda: self.call('POST', '/restaurants/r/policies', self.policy(**{field: value}), 'bad'))
            self.assertEqual(before, self.snapshot())
        status, result = self.publish(key='bad')
        self.assertEqual((status, result['policy_version']), (201, 1))
        self.assertEqual(self.publish(key='bad'), (200, result))
        self.error(409, 'idempotency_key_reuse', lambda: self.call('POST', '/restaurants/r/policies', {'bad': True}, 'bad'))

    def test_noop_keeps_terms_even_if_new_policy_would_reject(self):
        old = self.book()
        self.publish(capacities={'a': 1, 'b': 6})
        result = self.call('PATCH', '/reservations/' + old['reference'], {'party_size': 2})[1]
        self.assertEqual(result, old)
        self.assertEqual(len(self.history(old['reference'])), 1)
        before = self.snapshot()
        self.error(422, 'party_exceeds_capacity', lambda: self.call('PATCH', '/reservations/' + old['reference'], {'starts_at_local': '2099-09-24T19:30'}))
        self.assertEqual(before, self.snapshot())

    def test_history_pair_transitions_cancel_and_cas_precedence(self):
        old = self.book()
        path = '/reservations/' + old['reference']
        pair = self.call('PATCH', path, {'table_ids': ['a', 'b'], 'expected_revision': 1})[1]
        self.assertEqual(pair['revision'], 2)
        self.assertEqual(self.history(old['reference'])[1]['changes'], [{'field': 'table_ids', 'from': ['a'], 'to': ['b', 'a']}])
        self.assertEqual(self.call('PATCH', path, {'table_ids': ['a', 'b'], 'expected_revision': 2})[1], pair)
        self.error(409, 'stale_revision', lambda: self.call('PATCH', path, {'expected_revision': 1, 'party_size': False}))
        self.error(422, 'validation_failed', lambda: self.call('PATCH', path, {'expected_revision': True}))
        cancelled = self.call('POST', path + '/cancel', {})[1]
        self.assertEqual(cancelled['revision'], 3)
        self.assertEqual(self.call('POST', path + '/cancel', {})[1], cancelled)
        entries = self.history(old['reference'])
        self.assertEqual([e['seq'] for e in entries], [1, 2, 3])
        self.assertEqual(entries[-1]['changes'], [])
        for suffix in ('/history', '/decision'):
            self.error(404, 'not_found', lambda: self.call('GET', path + suffix, token=''))
            self.error(404, 'not_found', lambda: self.call('GET', path + suffix, token=self.other))
        snapshot = self.snapshot()
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(snapshot, self.snapshot())

    def test_old_cutoff_is_checked_before_new_policy_and_changes(self):
        old = self.book()
        self.publish(cancellation_cutoff_minutes=0)
        instant = datetime.fromisoformat(old['starts_at']).astimezone(timezone.utc) - timedelta(minutes=60)
        before = self.snapshot()
        with patch('tablekeeper.reservations.now', return_value=instant):
            self.error(409, 'cutoff_passed', lambda: self.call('PATCH', '/reservations/' + old['reference'], {'table_id': 'missing'}))
            self.error(409, 'cutoff_passed', lambda: self.call('POST', '/reservations/' + old['reference'] + '/cancel', {}))
        self.assertEqual(before, self.snapshot())

    def test_concurrent_cas_only_one_real_change(self):
        old = self.book()
        def attempt(i):
            try:
                return self.call('PATCH', '/reservations/' + old['reference'], {'expected_revision': 1, 'party_size': 3 if i % 2 else 4})[0]
            except APIError as error:
                self.assertEqual(error.code, 'stale_revision')
                return error.status
        with ThreadPoolExecutor(max_workers=50) as pool:
            result = list(pool.map(attempt, range(50)))
        self.assertEqual(result.count(200), 1)
        self.assertEqual(result.count(409), 49)
        self.assertEqual(len(self.history(old['reference'])), 2)

    def test_series_adopts_anchor_and_preserves_original_receipts(self):
        anchor = self.book()
        history_before = self.history(anchor['reference'])
        self.publish(effective='2099-10-01', reservation_duration_minutes=60)
        body = {'anchor_reference': anchor['reference'], 'count': 3, 'interval_weeks': 1}
        status, agreement = self.call('POST', '/series', body, 'series')
        self.assertEqual(status, 201)
        self.assertEqual(agreement['occurrences'][0]['reservation'], anchor)
        self.assertEqual(self.history(anchor['reference']), history_before)
        self.assertEqual([o['reservation']['accepted_terms']['policy_version'] for o in agreement['occurrences']], [0, 1, 1])
        self.assertEqual(self.call('POST', '/reservations', self.body(), 'book'), (200, anchor))
        second = agreement['occurrences'][1]['reference']
        self.call('PATCH', '/reservations/' + second, {'party_size': 3})
        self.call('POST', '/reservations/' + anchor['reference'] + '/cancel', {})
        current = self.call('GET', '/series/' + agreement['series_id'])[1]
        self.assertEqual(current['revision'], 3)
        self.assertTrue(current['occurrences'][1]['exception'])
        self.assertFalse(current['occurrences'][0]['exception'])
        self.assertEqual(current['occurrences'][2]['reservation']['status'], 'confirmed')
        self.assertEqual(self.call('POST', '/series', body, 'series'), (200, agreement))
        snapshot = self.snapshot()
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(snapshot, self.snapshot())
        self.assertEqual(self.call('POST', '/series', body, 'series'), (200, agreement))

    def test_series_rolls_back_generated_bookings_histories_and_key(self):
        anchor = self.book()
        self.book(key='conflict', local='2099-10-08T19:00')
        body = {'anchor_reference': anchor['reference'], 'count': 3, 'interval_weeks': 1}
        before = self.snapshot()
        self.error(409, 'table_unavailable', lambda: self.call('POST', '/series', body, 'series'))
        self.assertEqual(before, self.snapshot())
        body['count'] = 2
        self.assertEqual(self.call('POST', '/series', body, 'series')[0], 201)

    def test_batch_touches_series_and_restaurant_once(self):
        anchor = self.book()
        agreement = self.call('POST', '/series', {'anchor_reference': anchor['reference'], 'count': 3, 'interval_weeks': 1}, 'series')[1]
        refs = [o['reference'] for o in agreement['occurrences']]
        before_rev = self.app.store.data['restaurant_revisions']['r']
        body = {'moves': [{'reference': ref, 'party_size': 3, 'expected_revision': 1} for ref in refs]}
        self.call('POST', '/reservation-moves', body, 'batch')
        current = self.call('GET', '/series/' + agreement['series_id'])[1]
        self.assertEqual(current['revision'], 2)
        self.assertTrue(all(o['exception'] for o in current['occurrences']))
        self.assertEqual(self.app.store.data['restaurant_revisions']['r'], before_rev + 1)
        snapshot = self.snapshot()
        self.call('POST', '/reservation-moves', body, 'batch')
        self.assertEqual(snapshot, self.snapshot())

    def test_explanations_report_both_rules_and_policy(self):
        self.book(size=4)
        self.publish(capacities={'a': 1, 'b': 6})
        query = {'restaurant_id': ['r'], 'date': ['2099-09-24'], 'party_size': ['2'], 'explain': ['true']}
        response = self.call('GET', '/availability', query=query)[1]
        slot = next(s for s in response['slots'] if s['starts_at_local'].endswith('19:00'))
        self.assertEqual(slot['explain'][0], {'table_id': 'a', 'policy_version': 1, 'available': False,
            'rules': [{'rule': 'capacity', 'holds': False}, {'rule': 'no_overlap', 'holds': False}]})
        query.pop('explain')
        self.assertNotIn('explain', self.call('GET', '/availability', query=query)[1]['slots'][0])
        for value in ('', 'false', '1'):
            query['explain'] = [value]
            self.error(422, 'validation_failed', lambda: self.call('GET', '/availability', query=query))

    def test_invalid_history_and_series_import_are_atomic(self):
        anchor = self.book()
        agreement = self.call('POST', '/series', {'anchor_reference': anchor['reference'], 'count': 2, 'interval_weeks': 1}, 'series')[1]
        before = self.snapshot()
        bad = deepcopy(before)
        bad['state']['histories'][anchor['reference']][0]['changes'][0]['from'] = 'wrong'
        self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
        bad = deepcopy(before)
        bad['state']['series'][agreement['series_id']]['occurrences'][1]['index'] = 9
        self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
        bad = deepcopy(before)
        bad['state']['receipts'][0]['response']['revision'] = 999
        self.error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
        self.assertEqual(before, self.snapshot())

    def test_series_count_interval_limits_and_owner_visibility(self):
        anchor = self.book()
        for count, interval in [(1, 1), (13, 1), (2, 0), (2, 5), (True, 1), (2, False)]:
            self.error(422, 'validation_failed', lambda: self.call('POST', '/series',
                {'anchor_reference': anchor['reference'], 'count': count, 'interval_weeks': interval}, 'limits'))
        body = {'anchor_reference': anchor['reference'], 'count': 12, 'interval_weeks': 4}
        agreement = self.call('POST', '/series', body, 'limits')[1]
        self.assertEqual(len(agreement['occurrences']), 12)
        self.assertEqual(len({o['reference'] for o in agreement['occurrences']}), 12)
        self.error(409, 'already_in_series', lambda: self.call('POST', '/series', body, 'again'))
        for token in ('', self.other):
            self.error(404, 'not_found', lambda: self.call('GET', '/series/' + agreement['series_id'], token=token))
        snapshot = self.snapshot()
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(snapshot, self.snapshot())

    def test_series_dst_gap_rollback_and_first_fold(self):
        f = fixture()
        f['restaurants'][0]['opening_hours'] = [{'weekday': 'sun', 'opens': '00:00', 'closes': '06:00'}]
        self.call('POST', '/_test/reset', f)
        self.token = self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})[1]['token']
        with patch('tablekeeper.reservations.now', return_value=datetime(2026, 1, 1, tzinfo=timezone.utc)):
            anchor = self.book(local='2026-03-22T02:30')
            before = self.snapshot()
            self.error(422, 'invalid_local_time', lambda: self.call('POST', '/series',
                {'anchor_reference': anchor['reference'], 'count': 3, 'interval_weeks': 1}, 'gap'))
            self.assertEqual(before, self.snapshot())
            fold_anchor = self.book(key='fold', local='2026-10-18T02:30')
            series = self.call('POST', '/series', {'anchor_reference': fold_anchor['reference'], 'count': 2, 'interval_weeks': 1}, 'fold')[1]
            repeated = series['occurrences'][1]['reservation']
            self.assertEqual(repeated['starts_at'], '2026-10-25T02:30:00+02:00')
            self.assertEqual(repeated['ends_at'], '2026-10-25T03:00:00+01:00')

    def test_batch_failure_and_noop_keep_all_counters_and_exceptions(self):
        anchor = self.book()
        series = self.call('POST', '/series', {'anchor_reference': anchor['reference'], 'count': 2, 'interval_weeks': 1}, 's')[1]
        refs = [o['reference'] for o in series['occurrences']]
        before = self.snapshot()
        self.error(409, 'stale_revision', lambda: self.call('POST', '/reservation-moves',
            {'moves': [{'reference': refs[0], 'party_size': 3}, {'reference': refs[1], 'expected_revision': 2}]}, 'bad'))
        self.assertEqual(before, self.snapshot())
        self.call('POST', '/reservation-moves', {'moves': [{'reference': ref, 'party_size': 2} for ref in refs]}, 'noop')
        after = self.snapshot()
        for field in ('histories', 'series', 'restaurant_revisions', 'reservations'):
            self.assertEqual(before['state'][field], after['state'][field])

    def test_policy_change_amendment_revalidates_and_adopts_full_terms(self):
        anchor = self.book()
        self.publish(reservation_duration_minutes=60, capacities={'a': 1, 'b': 5})
        updated = self.call('PATCH', '/reservations/' + anchor['reference'], {'table_id': 'b'})[1]
        self.assertEqual(updated['revision'], 2)
        self.assertEqual(updated['accepted_terms']['capacities'], {'a': 1, 'b': 5})
        self.assertEqual(updated['ends_at'][11:16], '20:00')
        entries = self.history(anchor['reference'])
        self.assertEqual([e['accepted_terms']['policy_version'] for e in entries], [0, 1])
        self.assertEqual(entries[1]['changes'], [{'field': 'table_id', 'from': 'a', 'to': 'b'}])
        snapshot = self.snapshot()
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(snapshot, self.snapshot())


if __name__ == '__main__':
    unittest.main()
