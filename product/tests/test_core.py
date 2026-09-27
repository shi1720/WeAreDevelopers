"""Spec-derived transactional checks, independent of the official harness."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
import sys
import json
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tablekeeper.server import Application, Handler, Server
from tablekeeper.validation import APIError, object_body


def fixture():
    return {'users': [{'id': 'ada', 'email': 'ada@example.test', 'password': 'synthetic password', 'display_name': 'Ada'},
                      {'id': 'ben', 'email': 'ben@example.test', 'password': 'synthetic password', 'display_name': 'Ben'}],
            'restaurants': [{'id': 'r', 'name': 'The Orchard', 'timezone': 'Europe/Berlin',
                'slot_minutes': 30, 'reservation_duration_minutes': 90, 'cancellation_cutoff_minutes': 120,
                'opening_hours': [{'weekday': day, 'opens': '17:00', 'closes': '23:00'}
                                  for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')],
                'tables': [{'id': 'a', 'label': 'Window', 'capacity': 4}, {'id': 'b', 'label': 'Garden', 'capacity': 6}]}],
            'reservations': []}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.app = Application()
        self.call('POST', '/_test/reset', fixture())
        self.token = self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})[1]['token']
        self.other = self.call('POST', '/auth/login', {'email': 'ben@example.test', 'password': 'synthetic password'})[1]['token']

    def call(self, method, path, body=None, key=None, token=None, query=None):
        headers = {}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if key is not None:
            headers['Idempotency-Key'] = key
        return self.app.dispatch(method, path, query or {}, headers, body)

    def body(self, table='a', local='2099-09-24T19:00'):
        return {'restaurant_id': 'r', 'table_id': table, 'starts_at_local': local, 'party_size': 2}

    def book(self, key='one', **kwargs):
        return self.call('POST', '/reservations', self.body(**kwargs), key=key, token=self.token)

    def assert_error(self, status, code, operation):
        with self.assertRaises(APIError) as raised:
            operation()
        self.assertEqual((raised.exception.status, raised.exception.code), (status, code))

    def test_50_identical_requests_have_one_commit(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda _: self.book(), range(50)))
        self.assertEqual(sum(status == 201 for status, _ in results), 1)
        self.assertEqual(sum(status == 200 for status, _ in results), 49)
        self.assertTrue(all(body == results[0][1] for _, body in results))
        self.assertEqual(len(self.app.store.data['reservations']), 1)

    def test_50_competitors_never_double_book(self):
        def attempt(i):
            try:
                return self.book(key=str(i))[0]
            except APIError as error:
                self.assertEqual(error.code, 'table_unavailable')
                return error.status
        with ThreadPoolExecutor(max_workers=50) as pool:
            outcomes = list(pool.map(attempt, range(50)))
        self.assertEqual(outcomes.count(201), 1)
        self.assertEqual(outcomes.count(409), 49)
        self.assertEqual(len(self.app.store.data['receipts']), 1)

    def test_original_receipt_survives_cancel_and_import(self):
        _, original = self.book()
        self.call('POST', '/reservations/' + original['reference'] + '/cancel', {}, token=self.token)
        exported = self.call('GET', '/_test/export')[1]
        self.assertNotIn('password', exported['state']['users']['ada'])
        self.call('POST', '/_test/reset', fixture())
        self.call('POST', '/_test/import', exported)
        self.assertEqual(self.book(), (200, original))
        self.assertEqual(self.call('GET', '/reservations/' + original['reference'], token=self.token)[1]['status'], 'cancelled')
        self.call('POST', '/auth/login', {'email': 'ada@example.test', 'password': 'synthetic password'})

    def test_reuse_precedes_validation_and_unknown_fields_matter(self):
        self.book()
        bad = dict(self.body(), party_size=False)
        self.assert_error(409, 'idempotency_key_reuse', lambda: self.call('POST', '/reservations', bad, key='one', token=self.token))
        self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/reservations', bad, key='bad', token=self.token))
        self.book(key='bad', table='b')
        self.assert_error(409, 'idempotency_key_reuse', lambda: self.call('POST', '/reservations', dict(self.body(), ignored=1), key='one', token=self.token))

    def test_atomic_swap_and_failure_leave_whole_snapshot_unchanged(self):
        a = self.book()[1]
        b = self.book(key='two', table='b')[1]
        body = {'moves': [{'reference': a['reference'], 'table_id': 'b'}, {'reference': b['reference'], 'table_id': 'a'}]}
        status, swapped = self.call('POST', '/reservation-moves', body, key='one', token=self.token)
        self.assertEqual(status, 201)  # same key, distinct write path
        self.assertEqual([r['table_id'] for r in swapped['reservations']], ['b', 'a'])
        before = self.call('GET', '/_test/export')[1]
        body['moves'][1]['party_size'] = 100
        self.assert_error(422, 'party_exceeds_capacity', lambda: self.call('POST', '/reservation-moves', body, key='failed', token=self.token))
        self.assertEqual(before, self.call('GET', '/_test/export')[1])

    def test_half_open_and_owner_isolation(self):
        first = self.book()[1]
        self.book(key='adjacent', local='2099-09-24T20:30')
        self.assert_error(404, 'not_found', lambda: self.call('GET', '/reservations/' + first['reference'], token=self.other))
        self.assert_error(404, 'not_found', lambda: self.call('PATCH', '/reservations/' + first['reference'], {}, token=self.other))
        self.call('POST', '/reservations', self.body(table='b'), key='one', token=self.other)

    def test_invalid_import_does_not_replace_any_state(self):
        self.book()
        good = self.call('GET', '/_test/export')[1]
        variants = []
        for key, value in [('users', []), ('reservations', {'bad': {}}), ('tokens', {'token': 'unknown'}), ('receipts', [{}])]:
            bad = deepcopy(good)
            bad['state'][key] = value
            variants.append(bad)
        bad = deepcopy(good)
        bad['format_version'] = True
        variants.append(bad)
        for bad in variants:
            self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
            self.assertEqual(good, self.call('GET', '/_test/export')[1])

    def test_json_type_and_key_boundaries(self):
        self.assert_error(400, 'malformed_request', lambda: object_body('[]'))
        self.assert_error(400, 'malformed_request', lambda: object_body('{'))
        for key in (None, ''):
            self.assert_error(400, 'missing_idempotency_key', lambda: self.call('POST', '/reservations', self.body(), key=key, token=self.token))
        self.assert_error(422, 'validation_failed', lambda: self.book(key='x' * 256))
        self.book(key='x' * 255)
        for value in (False, '2', 2.5, 0, -1):
            self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/reservations', dict(self.body(table='b'), party_size=value), key='invalid', token=self.token))

    def test_past_create_and_cutoff_failure_atomicity(self):
        old = self.book(local='2001-01-01T19:00')[1]
        before = self.call('GET', '/_test/export')[1]
        self.assert_error(409, 'cutoff_passed', lambda: self.call('PATCH', '/reservations/' + old['reference'], {'table_id': 'missing'}, token=self.token))
        self.assertEqual(before, self.call('GET', '/_test/export')[1])

    def test_receipt_corruption_rejected_atomically(self):
        self.book()
        good = self.call('GET', '/_test/export')[1]
        for mutate in (lambda r: r['body'].update(party_size=False),
                       lambda r: r['response'].update(status='cancelled'),
                       lambda r: r['response'].update(party_size=3)):
            bad = deepcopy(good)
            mutate(bad['state']['receipts'][0])
            self.assert_error(422, 'validation_failed', lambda: self.call('POST', '/_test/import', bad))
            self.assertEqual(good, self.call('GET', '/_test/export')[1])

    def test_export_is_detached_and_import_replaces_credentials(self):
        exported = self.call('GET', '/_test/export')[1]
        extra = self.call('POST', '/auth/signup', {'email': 'new@example.test', 'password': 'synthetic new', 'display_name': 'New'})[1]
        self.book()
        self.call('POST', '/_test/import', exported)
        self.assertEqual(self.call('GET', '/reservations', token=self.token)[1], {'reservations': []})
        self.assert_error(401, 'unauthenticated', lambda: self.call('GET', '/reservations', token=extra['token']))
        self.call('POST', '/_test/import', exported)
        self.assertEqual(exported, self.call('GET', '/_test/export')[1])


class HttpTests(unittest.TestCase):
    def test_real_http_types_auth_and_concurrency(self):
        class TestHandler(Handler):
            application = Application()
        server = Server(('127.0.0.1', 0), TestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)

        def request(path, data=None, token=None, key=None):
            headers = {'Content-Type': 'application/json'}
            if token:
                headers['Authorization'] = 'Bearer ' + token
            if key:
                headers['Idempotency-Key'] = key
            req = Request(base + path, data=data, headers=headers)
            try:
                response = urlopen(req, timeout=5)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read()
                self.assertEqual(response.headers['Content-Type'], 'application/json; charset=utf-8')
                return response.status, json.loads(raw) if raw else None

        try:
            self.assertEqual(request('/health'), (200, {'status': 'ok'}))
            self.assertEqual(request('/_test/reset', json.dumps(fixture()).encode()), (204, None))
            token = request('/auth/login', b'{"email":"ada@example.test","password":"synthetic password"}')[1]['token']
            for data in (b'[]', b'{', b'{"x":NaN}'):
                self.assertEqual(request('/reservations', data, token, 'bad')[0], 400)
            payload = b'{"restaurant_id":"r","table_id":"a","party_size":2,"starts_at_local":"2099-09-24T19:00"}'
            with ThreadPoolExecutor(max_workers=50) as pool:
                results = list(pool.map(lambda _: request('/reservations', payload, token, 'race'), range(50)))
            self.assertEqual(sum(status == 201 for status, _ in results), 1)
            self.assertEqual(sum(status == 200 for status, _ in results), 49)
            self.assertTrue(all(body == results[0][1] for _, body in results))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
