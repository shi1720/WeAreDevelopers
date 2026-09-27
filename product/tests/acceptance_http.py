"""Independent operational HTTP gates against the canonical companion wire contract.

Run from an immutable product checkout: python -m pytest tests/acceptance_http.py -q
Each case owns a temporary synthetic SQLite service. No judge reset endpoints.
Do not enable pytest --showlocals: test memory contains synthetic credentials.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import httpx
import pytest

PASSWORD = 'synthetic-acceptance-password'
PRODUCT = Path(os.environ.get('ACCEPTANCE_PRODUCT_ROOT', Path(__file__).resolve().parents[1])).resolve()


def setup_body(secret):
    return {'setup_secret': secret,
            'owner': {'email': 'owner@acceptance.test', 'password': PASSWORD, 'display_name': 'Synthetic Owner'},
            'restaurant': {'name': 'Acceptance Hearth', 'timezone': 'Etc/UTC', 'slot_minutes': 30,
                           'reservation_duration_minutes': 60, 'cancellation_cutoff_minutes': 0,
                           'opening_hours': [{'weekday': day, 'opens': '00:00', 'closes': '23:59'}
                                             for day in 'mon tue wed thu fri sat sun'.split()],
                           'tables': [{'id': 'table_1', 'label': 'Window', 'capacity': 2},
                                      {'id': 'table_2', 'label': 'Garden', 'capacity': 4},
                                      {'id': 'table_3', 'label': 'Hearth', 'capacity': 6}],
                           'combinable': [['table_1', 'table_2']]}}


class Service:
    def __init__(self, directory, demo=False):
        self.directory = directory
        self.secret = secrets.token_urlsafe(32)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{self.port}'
        self.environment = dict(os.environ, PORT=str(self.port), TABLEKEEPER_MODE='development',
                                TABLEKEEPER_PUBLIC_ORIGIN=self.url, TABLEKEEPER_STORAGE='sqlite',
                                TABLEKEEPER_DB=str(directory / 'state.sqlite3'),
                                TABLEKEEPER_SETUP_SECRET=self.secret, TABLEKEEPER_PUBLIC_DEMO='1' if demo else '0')
        for name in ('K_SERVICE', 'TABLEKEEPER_FAULT', 'TABLEKEEPER_FAULT_ARM_FILE'):
            self.environment.pop(name, None)
        self.process = None
        self.log = (directory / 'private-service.log').open('ab')
        self.start()

    def start(self):
        self.process = subprocess.Popen([sys.executable, '-m', 'tablekeeper.server'], cwd=PRODUCT,
                                        env=self.environment, stdout=self.log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(f'service exited before readiness, status={self.process.returncode}')
            try:
                if httpx.get(self.url + '/health', timeout=0.3).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.05)
        raise AssertionError('service readiness timeout')

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

    def restart(self):
        self.stop()
        self.start()

    def close(self):
        self.stop()
        self.log.close()


class BrowserClient:
    def __init__(self, service):
        self.service = service
        self.client = httpx.Client(base_url=service.url, timeout=10)
        self.csrf = None
        self.session()

    def request(self, method, path, body=None, key=None, headers=None):
        sent = {'Origin': self.service.url}
        if self.csrf and method != 'GET':
            sent['X-CSRF-Token'] = self.csrf
        if key is not None:
            sent['Idempotency-Key'] = key
        sent.update(headers or {})
        response = self.client.request(method, path, json=body, headers=sent)
        cache = response.headers.get('cache-control', '').lower()
        assert 'private' in cache and 'no-store' in cache, f'{method} {path}: missing private,no-store'
        return response

    def expect(self, status, method, path, body=None, key=None, code=None, headers=None):
        response = self.request(method, path, body, key, headers)
        assert response.status_code == status, f'{method} {path}: expected {status}, got {response.status_code}'
        result = response.json()
        if code:
            assert result.get('error', {}).get('code') == code
        return result

    def session(self):
        result = self.expect(200, 'GET', '/api/session')
        for field in ('authenticated', 'user_id', 'display_name', 'role', 'account_scope',
                      'csrf_token', 'setup_required', 'demo_enabled', 'demo'):
            assert field in result, f'missing canonical session field {field}'
        assert 'token' not in result and 'session' not in result
        self.csrf = result['csrf_token']
        return result

    def setup(self):
        self.expect(201, 'POST', '/api/setup', setup_body(self.service.secret))
        assert self.session()['authenticated']
        return self.expect(200, 'GET', '/restaurants')['restaurants'][0]['id']

    def signup(self, email='guest@acceptance.test'):
        self.expect(201, 'POST', '/auth/signup', {'email': email, 'password': PASSWORD, 'display_name': 'Synthetic Guest'})
        self.session()

    def booking(self, rid, key='booking', local='2032-06-17T18:00', table='table_1'):
        body = {'restaurant_id': rid, 'table_id': table, 'starts_at_local': local, 'party_size': 2}
        return body, self.expect(201, 'POST', '/reservations', body, key)


@pytest.fixture
def service(tmp_path):
    value = Service(tmp_path)
    yield value
    value.close()


def test_canonical_shell_session_cookie_and_empty_production_data(service):
    client = BrowserClient(service)
    assert client.session()['setup_required'] is True
    assert client.session()['authenticated'] is False
    assert {cookie.name for cookie in client.client.cookies.jar} == {'__session'}
    response = httpx.get(service.url + '/api/session')
    cookie = response.headers.get('set-cookie', '').lower()
    assert 'httponly' in cookie and 'samesite=' in cookie
    for path in ('/setup', '/bookings', '/account', '/demo'):
        response = client.client.get(path)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
    for method, path in [('POST', '/_test/reset'), ('GET', '/_test/export'), ('POST', '/_test/import')]:
        assert client.request(method, path, {}).status_code == 404
    assert client.expect(200, 'GET', '/restaurants')['restaurants'] == []


def test_setup_secret_consumption_and_restart(service):
    client = BrowserClient(service)
    wrong = setup_body('wrong-secret')
    assert client.request('POST', '/api/setup', wrong).status_code in (401, 403)
    assert client.session()['setup_required']
    rid = client.setup()
    assert not client.session()['setup_required']
    assert client.request('POST', '/api/setup', setup_body(service.secret)).status_code in (403, 409)
    service.restart()
    assert not client.session()['setup_required']
    assert client.expect(200, 'GET', '/restaurants')['restaurants'][0]['id'] == rid
    service.log.flush()
    log = (service.directory / 'private-service.log').read_text()
    assert service.secret not in log and PASSWORD not in log


def test_concurrent_setup_consumes_once(service):
    clients = [BrowserClient(service), BrowserClient(service)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda c: c.request('POST', '/api/setup', setup_body(service.secret)).status_code, clients))
    assert results.count(201) == 1
    assert all(status in (201, 403, 409) for status in results)
    assert len(clients[0].expect(200, 'GET', '/restaurants')['restaurants']) == 1


def test_origin_csrf_password_minimum_and_logout_revocation(service):
    owner = BrowserClient(service)
    owner.setup()
    guest = BrowserClient(service)
    body = {'email': 'new@acceptance.test', 'password': 'a' * 11, 'display_name': 'Synthetic'}
    guest.expect(422, 'POST', '/auth/signup', body)
    body['password'] = PASSWORD
    assert guest.request('POST', '/auth/signup', body, headers={'Origin': 'https://foreign.test'}).status_code == 403
    assert guest.request('POST', '/auth/signup', body, headers={'X-CSRF-Token': 'bad'}).status_code == 403
    guest.signup()
    old_cookie = guest.client.cookies.get('__session')
    guest.expect(200, 'POST', '/auth/logout', {})
    attacker = httpx.Client(base_url=service.url, cookies={'__session': old_cookie})
    assert attacker.get('/reservations').status_code == 401
    assert guest.session()['authenticated'] is False


def test_booking_replay_after_edit_cancel_restart_and_failed_key_reuse(service):
    owner = BrowserClient(service)
    rid = owner.setup()
    guest = BrowserClient(service)
    guest.signup()
    invalid = {'restaurant_id': rid, 'table_id': 'table_1', 'starts_at_local': '2032-06-17T18:00', 'party_size': 0}
    guest.expect(422, 'POST', '/reservations', invalid, 'booking')
    body, original = guest.booking(rid)
    changed_body = {'party_size': 1, 'expected_revision': original['revision']}
    changed = guest.expect(200, 'PATCH', '/reservations/' + original['reference'], changed_body, 'edit')
    assert changed['revision'] == original['revision'] + 1
    guest.expect(200, 'POST', '/reservations/' + original['reference'] + '/cancel', {}, 'cancel')
    service.restart()
    assert guest.expect(200, 'POST', '/reservations', body, 'booking') == original
    assert guest.expect(200, 'PATCH', '/reservations/' + original['reference'], changed_body, 'edit') == changed
    guest.expect(409, 'POST', '/reservations', dict(body, party_size=1), 'booking', 'idempotency_key_reuse')


def test_owner_list_pagination_roster_and_private_history(service):
    owner = BrowserClient(service)
    rid = owner.setup()
    guest = BrowserClient(service)
    guest.signup()
    references = []
    for index in range(3):
        _, booking = guest.booking(rid, key=f'list{index}', local=f'2032-06-{17 + index}T18:00')
        references.append(booking['reference'])
    first = guest.expect(200, 'GET', '/reservations?view=upcoming&limit=2&offset=0')
    second = guest.expect(200, 'GET', f'/reservations?view=upcoming&limit=2&offset={first["next_offset"]}')
    assert len(first['reservations']) == 2 and len(second['reservations']) == 1
    assert second['next_offset'] is None
    assert {r['reference'] for r in first['reservations'] + second['reservations']} == set(references)
    assert owner.expect(200, 'GET', '/reservations?view=upcoming&limit=25&offset=0')['reservations'] == []
    for suffix in ('', '/history', '/decision'):
        owner.expect(404, 'GET', '/reservations/' + references[0] + suffix)
    query = f'/api/roster?restaurant_id={rid}&date=2032-06-17&limit=50&offset=0'
    guest.expect(403, 'GET', query)
    roster = owner.expect(200, 'GET', query)
    assert len(roster['reservations']) == 1
    assert roster['next_offset'] is None
    assert roster['reservations'][0]['reference'] == references[0]
    assert roster['reservations'][0]['display_name'] == 'Synthetic Guest'
    for forbidden in ('password', 'password_hash', 'sessions', 'history', 'accepted_terms'):
        assert forbidden not in roster['reservations'][0]


def test_password_change_revokes_other_session(service):
    owner = BrowserClient(service)
    owner.setup()
    guest = BrowserClient(service)
    guest.signup()
    second = BrowserClient(service)
    second.expect(200, 'POST', '/auth/login', {'email': 'guest@acceptance.test', 'password': PASSWORD})
    second.session()
    guest.expect(200, 'POST', '/auth/password', {'current_password': PASSWORD, 'new_password': PASSWORD + '-changed'})
    assert second.request('GET', '/reservations').status_code == 401
    service.restart()
    assert second.request('GET', '/reservations').status_code == 401


def test_demo_two_visitors_copied_reference_role_reset_isolation(tmp_path):
    service = Service(tmp_path, demo=True)
    try:
        clients = [BrowserClient(service), BrowserClient(service)]
        for client in clients:
            client.expect(201, 'POST', '/api/demo/start', {})
            assert client.session()['demo']
        scopes = [client.session()['account_scope'] for client in clients]
        assert scopes[0] != scopes[1]
        a, b = clients
        rid = a.expect(200, 'GET', '/restaurants')['restaurants'][0]['id']
        detail = a.expect(200, 'GET', '/restaurants/' + rid)
        # Synthetic demo inventory can differ from setup inventory.
        table = detail['tables'][0]['id']
        slots = a.expect(200, 'GET', f'/availability?restaurant_id={rid}&date=2032-06-17&party_size=1')['slots']
        assert slots
        body = {'restaurant_id': rid, 'table_id': table, 'starts_at_local': slots[0]['starts_at_local'], 'party_size': 1}
        booking = a.expect(201, 'POST', '/reservations', body, 'demo-booking')
        for suffix in ('', '/history', '/decision'):
            b.expect(404, 'GET', '/reservations/' + booking['reference'] + suffix)
        b.expect(200, 'POST', '/api/demo/role', {'role': 'manager'})
        b.session()
        b.expect(200, 'POST', '/api/demo/reset', {})
        assert a.expect(200, 'GET', '/reservations/' + booking['reference'])['reference'] == booking['reference']
        assert a.session()['account_scope'] == scopes[0]
    finally:
        service.close()
