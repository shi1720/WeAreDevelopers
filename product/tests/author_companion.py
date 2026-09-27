"""Author checks for durable state and operational boundaries; independent gates are separate."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time

import pytest

from tablekeeper.companion import Companion
from tablekeeper.server import Application
from tablekeeper.storage import SQLiteStore, StoreError, fresh, MAX_BYTES
from tablekeeper import operations
from tablekeeper.validation import APIError


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('TABLEKEEPER_MODE', 'development')
    monkeypatch.setenv('TABLEKEEPER_PUBLIC_ORIGIN', 'http://localhost:8080')
    monkeypatch.setenv('TABLEKEEPER_SETUP_SECRET', 'synthetic-setup-secret-at-least-32-characters')
    monkeypatch.setenv('TABLEKEEPER_PUBLIC_DEMO', '1')
    store = SQLiteStore(tmp_path / 'store.sqlite3')
    instance = Companion(Application.route, store)
    instance.domain_route = lambda *args: Application.route(None, *args)
    yield instance
    store.close()


class Browser:
    def __init__(self, app):
        self.app = app
        self.cookie = ''
        self.csrf = ''
        self.call('GET', '/auth/session')

    def call(self, method, path, body=None, query=None, key=None):
        headers = {'Cookie': self.cookie, 'Origin': 'http://localhost:8080', 'X-CSRF-Token': self.csrf}
        if key:
            headers['Idempotency-Key'] = key
        status, response, cookie = self.app.dispatch(method, path, query or {}, headers, body or {})
        if cookie:
            self.cookie = cookie.split(';')[0]
        if isinstance(response, dict) and 'csrf_token' in response:
            self.csrf = response['csrf_token']
        return status, response


def setup_body():
    return {'setup_secret': 'synthetic-setup-secret-at-least-32-characters',
            'owner': {'email': 'owner@venue.test', 'password': 'synthetic password 12', 'display_name': 'Owner'},
            'restaurant': {'name': 'Synthetic Venue', 'timezone': 'Europe/London',
                'slot_minutes': 30, 'reservation_duration_minutes': 60, 'cancellation_cutoff_minutes': 60,
                'opening_hours': [{'weekday': day, 'opens': '10:00', 'closes': '23:00'} for day in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')],
                'tables': [{'id': 'one', 'label': 'One', 'capacity': 4}, {'id': 'two', 'label': 'Two', 'capacity': 4}], 'combinable': [['one', 'two']]}}


def booking():
    return {'restaurant_id': 'venue', 'starts_at_local': '2035-06-14T19:00', 'table_id': 'one', 'party_size': 2}


def test_setup_restart_retry_and_extra_receipts(app, tmp_path):
    browser = Browser(app)
    assert browser.call('POST', '/setup', setup_body())[0] == 201
    status, original = browser.call('POST', '/reservations', booking(), key='book')
    assert status == 201
    reference = original['reference']
    changed = browser.call('PATCH', '/reservations/' + reference, {'expected_revision': 1, 'party_size': 3}, key='edit')[1]
    assert changed['revision'] == 2
    path = app.store.path
    app.store.close()
    app.store = SQLiteStore(path)
    assert browser.call('POST', '/reservations', booking(), key='book') == (200, original)
    assert browser.call('PATCH', '/reservations/' + reference, {'expected_revision': 1, 'party_size': 3}, key='edit') == (200, changed)
    assert browser.call('POST', '/setup', setup_body())[0] == 409
    app.store.close()
    app.store = SQLiteStore(path)


def test_atomicity_concurrency_failed_key_and_ownership(app, monkeypatch, tmp_path):
    browser = Browser(app)
    browser.call('POST', '/setup', setup_body())
    with pytest.raises(StoreError):
        SQLiteStore(app.store.path)
    def reserve(index):
        try:
            return browser.call('POST', '/reservations', booking(), key=str(index))[0]
        except APIError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sorted(pool.map(reserve, range(8))) == [201] + [409] * 7
    snapshot = app.store.snapshot('main')[1]
    marker = tmp_path / 'armed'
    marker.touch()
    monkeypatch.setenv('TABLEKEEPER_FAULT', 'commit_failure')
    monkeypatch.setenv('TABLEKEEPER_FAULT_ARM_FILE', str(marker))
    other = dict(booking(), table_id='two')
    with pytest.raises(StoreError):
        browser.call('POST', '/reservations', other, key='failure')
    assert app.store.snapshot('main')[1] == snapshot
    assert browser.call('POST', '/reservations', other, key='failure')[0] == 201


def test_backup_restore_validation_and_session_incident(app, tmp_path):
    browser = Browser(app)
    browser.call('POST', '/setup', setup_body())
    original = browser.call('POST', '/reservations', booking(), key='original')[1]
    destination = tmp_path / 'backup.json'
    operations.backup(app.store, 'main', destination)
    other = SQLiteStore(tmp_path / 'other.sqlite3')
    revision = operations.maintenance(other, 'main', True)
    operations.restore(other, 'main', destination, revision, True)
    assert other.snapshot('main')[1]['sessions'] == {}
    assert other.snapshot('main')[1]['domain']['receipts'][0]['response'] == original
    operations.maintenance(other, 'main', False)
    before = other.snapshot('main')
    destination.write_text('{}')
    with pytest.raises(StoreError):
        operations.restore(other, 'main', destination, before[0])
    assert other.snapshot('main') == before
    other.close()


def test_demo_cookie_isolation_roles_expiry_and_reset(app):
    first, second = Browser(app), Browser(app)
    first.call('POST', '/demo/start')
    second.call('POST', '/demo/start')
    one = first.call('GET', '/auth/session')[1]
    two = second.call('GET', '/auth/session')[1]
    assert one['scope_id'] != two['scope_id']
    first.call('POST', '/demo/role', {'role': 'manager'})
    assert second.call('GET', '/auth/session')[1]['user']['role'] == 'guest'
    namespace, token = app.locator({'Cookie': first.cookie})
    second_namespace, _ = app.locator({'Cookie': second.cookie})
    first.cookie = '__session=' + second_namespace + '.' + token
    with pytest.raises(APIError):
        first.call('GET', '/reservations')
    second.call('POST', '/demo/reset')
    app.store.transact(second_namespace, lambda value: value.update(expires_at=time.time() - 1))
    with pytest.raises(APIError, match='expired'):
        second.call('GET', '/reservations')
    assert namespace != second_namespace


def test_auth_csrf_logout_password_and_limits(app):
    browser = Browser(app)
    assert browser.call('POST', '/setup', setup_body())[0] == 201
    old_cookie = browser.cookie
    browser.call('POST', '/auth/password', {'current_password': 'synthetic password 12', 'new_password': 'different synthetic password'})
    with pytest.raises(APIError):
        app.dispatch('GET', '/reservations', {}, {'Cookie': old_cookie}, {})
    with pytest.raises(APIError):
        app.dispatch('POST', '/auth/logout', {}, {'Cookie': browser.cookie, 'Origin': 'https://evil.test', 'X-CSRF-Token': browser.csrf}, {})
    browser.call('POST', '/auth/logout')
    with pytest.raises(APIError):
        browser.call('GET', '/reservations')
    browser.call('GET', '/auth/session')
    for _ in range(8):
        browser.call('POST', '/auth/login', {'email': 'nobody@venue.test', 'password': 'wrong'})
    assert browser.call('POST', '/auth/login', {'email': 'nobody@venue.test', 'password': 'wrong'})[0] == 429


def test_capacity_and_corruption_fail_closed(app):
    before = app.store.snapshot('main')
    with pytest.raises(APIError, match='storage is full'):
        app.store.transact('main', lambda value: value.update(padding='x' * MAX_BYTES))
    assert app.store.snapshot('main') == before
    app.store.db.execute("UPDATE namespaces SET checksum='bad' WHERE id='main'")
    with pytest.raises(StoreError):
        app.store.snapshot('main')


def test_policy_series_closure_history_survive_restart(app):
    guest = Browser(app)
    guest.call('POST', '/demo/start')
    adoption = guest.call('POST', '/series', {'anchor_reference': 'EVENING1', 'count': 3, 'interval_weeks': 1}, key='adopt')[1]
    sid = adoption['series_id']
    amended = guest.call('POST', '/series/' + sid + '/amend', {'expected_revision': 1, 'from_index': 1, 'local_time': '18:00'}, key='amend')[1]
    guest.call('POST', '/demo/role', {'role': 'manager'})
    rid = 'the_orangery'
    restaurant = guest.call('GET', '/restaurants/' + rid)[1]
    policy = {k: restaurant[k] for k in ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours')}
    policy.update(effective_from='2036-01-01', capacities={t['id']: t['capacity'] for t in restaurant['tables']})
    assert guest.call('POST', '/restaurants/' + rid + '/policies', policy, key='policy')[0] == 201
    plan = guest.call('POST', '/restaurants/' + rid + '/replans', {'table_id': 'window', 'from': '2035-06-14T18:00:00+01:00', 'to': '2035-06-14T20:30:00+01:00'}, key='preview')[1]
    applied = guest.call('POST', '/restaurants/' + rid + '/replans/' + plan['plan_id'] + '/apply', {}, key='apply')[1]
    path = app.store.path
    app.store.close()
    app.store = SQLiteStore(path)
    assert guest.call('POST', '/restaurants/' + rid + '/replans/' + plan['plan_id'] + '/apply', {}, key='apply')[1] == applied
    guest.call('POST', '/demo/role', {'role': 'guest'})
    assert guest.call('POST', '/series', {'anchor_reference': 'EVENING1', 'count': 3, 'interval_weeks': 1}, key='adopt')[1] == adoption
    assert guest.call('POST', '/series/' + sid + '/amend', {'expected_revision': 1, 'from_index': 1, 'local_time': '18:00'}, key='amend')[1] == amended
    history = guest.call('GET', '/reservations/EVENING1/history')[1]['entries']
    assert history[-1]['event'] == 'reassigned'


def test_concurrent_setup_and_backup_during_writes(app, tmp_path):
    first, second = Browser(app), Browser(app)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda browser: browser.call('POST', '/setup', setup_body())[0], (first, second))) == [201, 409]
    browser = first if first.call('GET', '/auth/session')[1]['user'] else second
    def writes():
        for hour in range(10, 20):
            browser.call('POST', '/reservations', dict(booking(), starts_at_local=f'2035-06-14T{hour}:00'), key=f'h{hour}')
    from tablekeeper.storage import SQLiteReader
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(writes)
        for index in range(5):
            reader = SQLiteReader(app.store.path)
            file = tmp_path / f'backup-{index}.json'
            operations.backup(reader, 'main', file)
            snapshot = operations.read_backup(file)
            assert len(snapshot['domain']['reservations']) == len(snapshot['domain']['receipts'])
            reader.close()
        future.result()
