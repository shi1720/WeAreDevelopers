"""Combined seating invariants and backward-compatible snapshot migration."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tablekeeper.server import Application
from tablekeeper.validation import APIError
from test_core import fixture


class CombinationTests(unittest.TestCase):
    def setUp(self):
        self.app = Application()
        f = fixture()
        f['restaurants'][0]['tables'].append({'id': 'c', 'label': 'Courtyard', 'capacity': 3})
        f['restaurants'][0]['combinable'] = [['b', 'a'], ['b', 'c']]
        self.call('POST', '/_test/reset', f)
        self.token = self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})[1]['token']

    def call(self, method, path, body=None, key=None):
        return self.app.dispatch(method, path, {}, {'Authorization': 'Bearer ' + getattr(self, 'token', ''), 'Idempotency-Key': key}, body)

    def body(self, ids=None, size=7, local='2099-09-24T19:00'):
        return {'restaurant_id': 'r', 'table_ids': ['a', 'b'] if ids is None else ids, 'party_size': size, 'starts_at_local': local}

    def book(self, key='pair', **kw):
        return self.call('POST', '/reservations', self.body(**kw), key)

    def assert_error(self, status, code, call):
        with self.assertRaises(APIError) as caught:
            call()
        self.assertEqual((caught.exception.status, caught.exception.code), (status, code))

    def test_pair_canonical_order_and_singleton_alias(self):
        pair = self.book()[1]
        self.assertEqual(pair['table_ids'], ['b', 'a'])
        self.assertNotIn('table_id', pair)
        unchanged = self.call('PATCH', '/reservations/' + pair['reference'], {'table_ids': ['a', 'b']})[1]
        self.assertEqual(pair, unchanged)
        single = self.call('PATCH', '/reservations/' + pair['reference'], {'table_ids': ['b'], 'party_size': 5})[1]
        self.assertEqual(single['table_id'], 'b')
        self.assertEqual(single['table_ids'], ['b'])

    def test_selection_rules_and_failed_key_reuse(self):
        for ids, code in [([], 'validation_failed'), (['a', 'a'], 'validation_failed'),
                          (['a', 'b', 'c'], 'combination_not_allowed'), (['a', 'c'], 'combination_not_allowed')]:
            self.assert_error(422, code, lambda: self.book(ids=ids))
        self.assert_error(404, 'not_found', lambda: self.book(ids=['b', 'unknown']))
        self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/reservations', dict(self.body(), table_id='a'), 'pair'))
        for ids in ('a', None, True, 2):
            self.assert_error(400, 'malformed_request', lambda: self.book(ids=ids) if ids is not None else self.call('POST', '/reservations', dict(self.body(), table_ids=None), 'pair'))
        self.assertEqual(self.book()[0], 201)

    def test_overlap_members_and_half_open_release(self):
        pair = self.book()[1]
        for ids in (['a'], ['b'], ['b', 'c']):
            self.assert_error(409, 'table_unavailable', lambda: self.book(key='contender', ids=ids, size=2))
        self.book(key='adjacent', local='2099-09-24T20:30')
        self.call('POST', '/reservations/' + pair['reference'] + '/cancel', {})
        self.book(key='freed')

    def test_atomic_pair_single_swap_and_no_partial_occupancy(self):
        pair = self.book(size=2)[1]
        single = self.book(key='single', ids=['c'], size=2)[1]
        body = {'moves': [{'reference': pair['reference'], 'table_ids': ['c']},
                          {'reference': single['reference'], 'table_ids': ['a', 'b']}]}
        status, moved = self.call('POST', '/reservation-moves', body, 'swap')
        self.assertEqual(status, 201)
        self.assertEqual([r['table_ids'] for r in moved['reservations']], [['c'], ['b', 'a']])
        snapshot = self.call('GET', '/_test/export')[1]
        bad = {'moves': [{'reference': pair['reference'], 'table_id': 'a'},
                         {'reference': single['reference'], 'table_ids': ['b', 'a']}]}
        self.assert_error(409, 'table_unavailable', lambda: self.call('POST', '/reservation-moves', bad, 'failed'))
        self.assertEqual(snapshot, self.call('GET', '/_test/export')[1])
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(self.call('POST', '/reservation-moves', body, 'swap'), (200, moved))

    def test_50_mixed_contenders_have_one_winner(self):
        def attempt(index):
            try:
                return self.book(key=str(index), ids=['b'] if index % 2 else ['b', 'a'], size=2)[0]
            except APIError as error:
                self.assertEqual(error.code, 'table_unavailable')
                return error.status
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(attempt, range(50)))
        self.assertEqual(results.count(201), 1)
        self.assertEqual(results.count(409), 49)

    def test_cancelled_seed_pair_does_not_occupy_and_import_roundtrip(self):
        f = fixture()
        f['restaurants'][0]['combinable'] = [['a', 'b']]
        f['reservations'] = [dict(self.body(), id='seed', reference='SEED01', user_id='ada', status='cancelled')]
        self.call('POST', '/_test/reset', f)
        self.token = self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})[1]['token']
        self.book()
        snapshot = self.call('GET', '/_test/export')[1]
        self.call('POST', '/_test/import', snapshot)
        self.assertEqual(snapshot, self.call('GET', '/_test/export')[1])
        self.assertEqual(self.call('GET', '/reservations/SEED01')[1]['status'], 'cancelled')

    def test_legacy_schema1_preserves_receipt_value_and_credentials(self):
        # Construct the exact schema-1 wire shape: table_id only, schema=1,
        # no combinable field. The stage-1 program is intentionally not a runtime dependency.
        original = self.call('POST', '/reservations', {'restaurant_id': 'r', 'table_id': 'a',
            'starts_at_local': '2099-09-24T19:00', 'party_size': 2}, 'legacy')[1]
        snapshot = self.call('GET', '/_test/export')[1]
        snapshot['state']['schema'] = 1
        for restaurant in snapshot['state']['restaurants']:
            restaurant.pop('combinable')
        for record in snapshot['state']['reservations'].values():
            record.pop('table_ids')
        snapshot['state']['receipts'][0]['response'].pop('table_ids')
        original.pop('table_ids')
        self.call('POST', '/_test/import', snapshot)
        retry_body = snapshot['state']['receipts'][0]['body']
        self.assertEqual(self.call('POST', '/reservations', retry_body, 'legacy'), (200, original))
        self.assertEqual(self.call('GET', '/reservations/' + original['reference'])[1]['table_ids'], ['a'])
        self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})
        upgraded = self.call('GET', '/_test/export')[1]
        self.call('POST', '/_test/import', upgraded)
        self.assertEqual(self.call('POST', '/reservations', retry_body, 'legacy'), (200, original))

    def test_invalid_legacy_structure_never_changes_destination(self):
        self.book()
        before = self.call('GET', '/_test/export')[1]
        for field, value in [('restaurants', [None]), ('restaurants', {}),
                             ('reservations', []), ('reservations', {'x': []})]:
            bad = deepcopy(before)
            bad['state']['schema'] = 1
            bad['state'][field] = value
            self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
            self.assertEqual(self.call('GET', '/_test/export')[1], before)


if __name__ == '__main__':
    unittest.main()
