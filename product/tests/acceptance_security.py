"""Durable session expiry, namespace binding and restored receipt checks."""
import hashlib
import os
import time
import uuid

import httpx
import pytest

from acceptance_http import Service, BrowserClient, service
from tablekeeper.storage import SQLiteStore, FirestoreStore
from tablekeeper import operations


@pytest.mark.parametrize('expiry', ['absolute','inactivity'])
def test_expired_sessions_rejected_after_restart(service, expiry):
    owner = BrowserClient(service)
    owner.setup()
    raw_cookie = owner.client.cookies.get('__session')
    token = raw_cookie.split('.',1)[1]
    digest = hashlib.sha256(token.encode()).hexdigest()
    service.stop()
    store = SQLiteStore(service.directory / 'state.sqlite3')
    try:
        def expire(value):
            session = value['sessions'][digest]
            if expiry == 'absolute':
                session['expires_at'] = time.time() - 1
            else:
                session['last_seen'] = time.time() - 7201
        store.transact('main', expire)
    finally:
        store.close()
    service.start()
    assert owner.request('GET','/reservations').status_code == 401


def test_session_read_touch_persists_and_expiry_does_not_extend(service):
    owner = BrowserClient(service)
    owner.setup()
    token = owner.client.cookies.get('__session').split('.',1)[1]
    digest = hashlib.sha256(token.encode()).hexdigest()
    def snapshot():
        service.stop()
        store = SQLiteStore(service.directory / 'state.sqlite3')
        try:
            return store.snapshot('main')[1]['sessions'][digest]
        finally:
            store.close()
            service.start()
    before = snapshot()
    time.sleep(.03)
    owner.expect(200,'GET','/reservations')
    after = snapshot()
    assert after['last_seen'] > before['last_seen']
    assert after['expires_at'] == before['expires_at']


def test_production_secure_cookie_and_test_routes_absent(tmp_path):
    server = Service(tmp_path, overrides={'TABLEKEEPER_MODE':'production','TABLEKEEPER_PUBLIC_ORIGIN':'https://synthetic.acceptance.test'})
    try:
        response = httpx.get(server.url + '/api/session')
        cookie = response.headers.get('set-cookie','').lower()
        assert '__session=' in cookie and 'secure' in cookie and 'httponly' in cookie and 'samesite=lax' in cookie
        assert response.json()['authenticated'] is False
        assert response.headers['strict-transport-security']
        for route in ('/_test/reset','/_test/import','/_test/export'):
            assert httpx.post(server.url + route,json={}).status_code == 404
    finally:
        server.close()


def test_demo_cookie_locator_is_not_authority_and_expiry_synchronous(tmp_path):
    server = Service(tmp_path, demo=True)
    try:
        a,b = BrowserClient(server),BrowserClient(server)
        for client in (a,b):
            client.expect(201,'POST','/api/demo/start',{})
            client.session()
        namespace_a,token_a = a.client.cookies.get('__session').split('.',1)
        namespace_b,_ = b.client.cookies.get('__session').split('.',1)
        forged = httpx.get(server.url+'/reservations',cookies={'__session':namespace_b+'.'+token_a})
        assert forged.status_code == 401
        assert a.expect(200,'GET','/reservations?namespace='+namespace_b) == a.expect(200,'GET','/reservations')
        server.stop()
        store = SQLiteStore(tmp_path/'state.sqlite3')
        try:
            store.transact(namespace_a,lambda c:c.update(expires_at=time.time()-1))
        finally:
            store.close()
        server.start()
        assert a.request('GET','/reservations').status_code == 401
        assert b.request('GET','/reservations').status_code == 200
        server.stop()
        store = SQLiteStore(tmp_path/'state.sqlite3')
        try:
            assert operations.cleanup(store,limit=1) == 1
            assert namespace_a not in store.snapshot('main')[1]['registry']
            assert namespace_b in store.snapshot('main')[1]['registry']
        finally:
            store.close()
        server.start()
        assert b.request('GET','/reservations').status_code == 200
    finally:
        server.close()


def test_firestore_backup_restore_separate_instance_original_receipt(tmp_path):
    if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
        pytest.skip('Firestore emulator required')
    project = 'demo-proofline-pilot'
    source_collection, target_collection = ['verifier_'+uuid.uuid4().hex for _ in range(2)]
    (tmp_path/'source').mkdir()
    (tmp_path/'target').mkdir()
    env = {'TABLEKEEPER_STORAGE':'firestore','GOOGLE_CLOUD_PROJECT':project,'TABLEKEEPER_COLLECTION':source_collection}
    source = Service(tmp_path/'source',overrides=env)
    target = None
    try:
        owner = BrowserClient(source)
        rid = owner.setup()
        body,original = owner.booking(rid,key='restore-receipt')
        owner.expect(200,'POST','/reservations/'+original['reference']+'/cancel',{},'restore-cancel')
        history = owner.expect(200,'GET','/reservations/'+original['reference']+'/history')
        backup = tmp_path/'private-backup.json'
        src = FirestoreStore(project,collection=source_collection)
        dst = FirestoreStore(project,collection=target_collection)
        try:
            operations.backup(src,'main',backup)
            revision = operations.maintenance(dst,'main',True)
            operations.restore(dst,'main',backup,revision)
            operations.maintenance(dst,'main',False)
        finally:
            src.close()
            dst.close()
        target = Service(tmp_path/'target',overrides=dict(env,TABLEKEEPER_COLLECTION=target_collection))
        headers = {'Origin':target.url,'X-CSRF-Token':owner.csrf,'Idempotency-Key':'restore-receipt'}
        response = httpx.post(target.url+'/reservations',json=body,headers=headers,cookies=owner.client.cookies,timeout=20)
        assert response.status_code == 200 and response.json() == original
        response = httpx.get(target.url+'/reservations/'+original['reference']+'/history',cookies=owner.client.cookies,timeout=20)
        assert response.status_code == 200 and response.json() == history
    finally:
        if target:
            target.close()
        source.close()
