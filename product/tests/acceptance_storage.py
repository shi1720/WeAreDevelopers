"""Independent adapter acceptance. Run only against an immutable candidate.

From product/: python -m pytest tests/acceptance_storage.py -q
Set FIRESTORE_EMULATOR_HOST and ACCEPTANCE_FIRESTORE_PROJECT to enable both adapters.
All Firestore writes use unique verifier_* collections, never a deployed project.
This suite verifies storage mechanisms, not full booking or browser contracts.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import uuid

import pytest

from tablekeeper import operations
from tablekeeper.storage import SQLiteStore, FirestoreStore, StoreError, fresh, encode, decode
from tablekeeper.validation import APIError


@pytest.fixture(params=['sqlite', 'firestore'])
def store(request, tmp_path):
    if request.param == 'sqlite':
        value = SQLiteStore(tmp_path / 'state.sqlite3')
    else:
        if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
            pytest.skip('Firestore emulator required; skipped is not acceptance')
        value = FirestoreStore(os.environ.get('ACCEPTANCE_FIRESTORE_PROJECT', 'demo-proofline-pilot'),
                               collection='verifier_' + uuid.uuid4().hex)
    value.transact('main', lambda candidate: None, create=True)
    yield value
    value.close()


def replace(candidate, value):
    candidate.clear()
    candidate.update(deepcopy(value))


def test_callback_failure_and_invalid_candidate_are_atomic(store):
    before = store.snapshot('main')
    def fail(candidate):
        candidate['setup_consumed'] = True
        raise RuntimeError('synthetic callback failure')
    with pytest.raises((RuntimeError, StoreError)):
        store.transact('main', fail)
    assert store.snapshot('main') == before
    with pytest.raises(StoreError):
        store.transact('main', lambda c: c.update(schema=999))
    assert store.snapshot('main') == before


def test_noop_snapshot_isolation_and_revision_cas(store):
    revision, original = store.snapshot('main')
    original['setup_consumed'] = True
    assert store.snapshot('main')[1]['setup_consumed'] is False
    store.transact('main', lambda c: None)
    assert store.snapshot('main')[0] == revision
    store.transact('main', lambda c: c.update(setup_consumed=True), expected_revision=revision)
    after = store.snapshot('main')
    with pytest.raises(APIError):
        store.transact('main', lambda c: c.update(setup_consumed=False), expected_revision=revision)
    assert store.snapshot('main') == after


def test_persistence_failure_rolls_back(store, monkeypatch, tmp_path):
    before = store.snapshot('main')
    marker = tmp_path / 'arm'
    marker.touch()
    monkeypatch.setenv('TABLEKEEPER_MODE', 'development')
    monkeypatch.setenv('TABLEKEEPER_FAULT', 'commit_failure')
    monkeypatch.setenv('TABLEKEEPER_FAULT_ARM_FILE', str(marker))
    with pytest.raises(StoreError):
        store.transact('main', lambda c: c.update(setup_consumed=True))
    assert not marker.exists()
    assert store.snapshot('main') == before


def test_production_ignores_host_fault_marker(store, monkeypatch, tmp_path):
    marker = tmp_path / 'arm'
    marker.touch()
    monkeypatch.setenv('TABLEKEEPER_MODE', 'production')
    monkeypatch.setenv('TABLEKEEPER_FAULT', 'commit_failure')
    monkeypatch.setenv('TABLEKEEPER_FAULT_ARM_FILE', str(marker))
    store.transact('main', lambda c: c.update(setup_consumed=True))
    assert marker.exists()
    assert store.snapshot('main')[1]['setup_consumed']


def test_state_capacity_boundary_is_atomic(store):
    # An ignored extension field exercises the envelope codec without weakening
    # domain validation or allocating millions of real bookings.
    value = fresh()
    value['acceptance_padding'] = ''
    value['acceptance_padding'] = 'x' * (4 * 1024 * 1024 - len(encode(value)))
    assert len(encode(value)) == 4 * 1024 * 1024
    store.transact('main', lambda c: replace(c, value))
    before = store.snapshot('main')
    with pytest.raises(APIError) as error:
        store.transact('main', lambda c: c.update(acceptance_padding=c['acceptance_padding'] + 'x'))
    assert error.value.code == 'state_capacity'
    assert store.snapshot('main') == before


def test_backup_restore_maintenance_cas_and_private_permissions(store, tmp_path):
    destination = tmp_path / 'snapshot.json'
    operations.backup(store, 'main', destination)
    assert destination.stat().st_mode & 0o777 == 0o600
    original = store.snapshot('main')[1]
    store.transact('main', lambda c: c.update(setup_consumed=True))
    before = store.snapshot('main')
    with pytest.raises(StoreError):
        operations.restore(store, 'main', destination, before[0])
    assert store.snapshot('main') == before
    locked_revision = operations.maintenance(store, 'main', True)
    locked = store.snapshot('main')
    with pytest.raises(APIError):
        store.transact('main', lambda c: c.update(setup_consumed=False))
    assert store.snapshot('main') == locked
    with pytest.raises(APIError):
        operations.restore(store, 'main', destination, locked_revision - 1)
    assert store.snapshot('main') == locked
    operations.restore(store, 'main', destination, locked_revision)
    operations.maintenance(store, 'main', False)
    assert store.snapshot('main')[1] == original


def test_invalid_restore_never_replaces_previous_state(store, tmp_path):
    good = tmp_path / 'good.json'
    operations.backup(store, 'main', good)
    source = json.loads(good.read_text())
    cases = [dict(source, format='unsupported'), dict(source, sha256='0' * 64),
             dict(source, state=dict(source['state'], schema=999))]
    operations.maintenance(store, 'main', True)
    before = store.snapshot('main')
    for index, case in enumerate(cases):
        path = tmp_path / f'bad{index}.json'
        path.write_text(json.dumps(case))
        with pytest.raises((StoreError, APIError)):
            operations.restore(store, 'main', path, before[0])
        assert store.snapshot('main') == before


def test_backup_during_writes_has_consistent_snapshot(store, tmp_path):
    def increment():
        for index in range(12):
            store.transact('main', lambda c: c.update(acceptance_counter=c.get('acceptance_counter', 0) + 1))
    with ThreadPoolExecutor(max_workers=1) as pool:
        writer = pool.submit(increment)
        for index in range(8):
            path = tmp_path / f'backup{index}.json'
            revision = operations.backup(store, 'main', path)
            value = operations.read_backup(path)
            assert value.get('acceptance_counter', 0) == revision - 1
        writer.result()
    assert store.snapshot('main')[1]['acceptance_counter'] == 12


def test_incident_restore_revokes_sessions_and_keeps_absolute_expiry(store, tmp_path):
    sessions = {'a' * 64: {'user_id': None, 'csrf': 'b' * 64, 'expires_at': 1, 'last_seen': 0}}
    store.transact('main', lambda c: c.update(sessions=sessions))
    backup = tmp_path / 'old.json'
    operations.backup(store, 'main', backup)
    store.transact('main', lambda c: c.update(sessions={}))
    revision = operations.maintenance(store, 'main', True)
    operations.restore(store, 'main', backup, revision)
    assert store.snapshot('main')[1]['sessions'] == sessions
    revision = store.snapshot('main')[0]
    operations.restore(store, 'main', backup, revision, revoke_sessions=True)
    assert store.snapshot('main')[1]['sessions'] == {}


@pytest.mark.parametrize('field,value', [
    ('schema', 999), ('sessions', []), ('setup_consumed', 1), ('demo', 0),
    ('expires_at', 'tomorrow'), ('maintenance', 'locked'),
    ('registry', {'demo_' + 'a' * 32: 'later'}),
    ('attempts', {'a' * 64: {'count': -1, 'until': 'later'}}),
])
def test_operational_schema_corruption_rejected(field, value):
    candidate = fresh()
    candidate[field] = value
    raw = json.dumps(candidate).encode()
    with pytest.raises(StoreError):
        decode(raw, hashlib.sha256(raw).hexdigest())


def test_domain_corruption_is_not_hidden_by_valid_envelope():
    value = fresh()
    value['domain']['schema'] = 999
    raw = json.dumps(value).encode()
    with pytest.raises(StoreError):
        decode(raw, hashlib.sha256(raw).hexdigest())


def test_sqlite_second_process_refuses_owner(tmp_path):
    path = tmp_path / 'owner.sqlite3'
    store = SQLiteStore(path)
    try:
        code = 'from tablekeeper.storage import SQLiteStore,StoreError; import sys\ntry: SQLiteStore(sys.argv[1])\nexcept StoreError: sys.exit(23)\nsys.exit(0)'
        result = subprocess.run([sys.executable, '-c', code, str(path)], capture_output=True, timeout=10)
        assert result.returncode == 23
    finally:
        store.close()
    reopened = SQLiteStore(path)
    reopened.close()


@pytest.mark.parametrize('corruption', ['checksum', 'schema'])
def test_sqlite_corrupt_startup_refuses(tmp_path, corruption):
    import sqlite3
    path = tmp_path / 'corrupt.sqlite3'
    store = SQLiteStore(path)
    store.transact('main', lambda c: None, create=True)
    store.close()
    with sqlite3.connect(path) as db:
        if corruption == 'checksum':
            db.execute('UPDATE namespaces SET checksum=?', ('0' * 64,))
        else:
            value = fresh()
            value['schema'] = 999
            raw = json.dumps(value).encode()
            db.execute('UPDATE namespaces SET payload=?,checksum=?', (raw, hashlib.sha256(raw).hexdigest()))
    with pytest.raises(StoreError):
        SQLiteStore(path)
    # Rejection must not replace the corrupt input with a fresh successful store.
    with sqlite3.connect(path) as db:
        raw, checksum = db.execute('SELECT payload,checksum FROM namespaces').fetchone()
        if corruption == 'checksum':
            assert checksum == '0' * 64
        else:
            assert json.loads(raw)['schema'] == 999


def test_restore_into_separate_sqlite_store_preserves_snapshot(store, tmp_path):
    store.transact('main', lambda c: c.update(setup_consumed=True))
    path = tmp_path / 'portable.json'
    operations.backup(store, 'main', path)
    destination = SQLiteStore(tmp_path / 'separate.sqlite3')
    try:
        revision = operations.maintenance(destination, 'main', True)
        operations.restore(destination, 'main', path, revision)
        operations.maintenance(destination, 'main', False)
        assert destination.snapshot('main')[1] == store.snapshot('main')[1]
    finally:
        destination.close()


def test_sqlite_online_backup_cli_and_restore_ownership(tmp_path):
    path = tmp_path / 'online.sqlite3'
    owner = SQLiteStore(path)
    owner.transact('main', lambda c: None, create=True)
    stop = threading.Event()
    started = threading.Event()
    env = dict(os.environ, TABLEKEEPER_STORAGE='sqlite', TABLEKEEPER_DB=str(path))
    env.pop('K_SERVICE', None)
    env.pop('TABLEKEEPER_FAULT', None)
    def write_continuously():
        while not stop.is_set():
            owner.transact('main', lambda c: c.update(acceptance_counter=c.get('acceptance_counter', 0) + 1))
            started.set()
            stop.wait(0.002)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker = pool.submit(write_continuously)
            assert started.wait(5)
            try:
                previous = owner.snapshot('main')[0]
                backup = tmp_path / 'online-backup.json'
                result = subprocess.run([sys.executable, '-m', 'tablekeeper.operations', '--namespace', 'main',
                                         'backup', str(backup)], env=env, capture_output=True, timeout=15)
                assert result.returncode == 0, result.stderr.decode()[-1000:]
                assert owner.snapshot('main')[0] > previous, 'writer did not progress during backup'
                envelope = json.loads(backup.read_text())
                restored = operations.read_backup(backup)
                assert restored['acceptance_counter'] == envelope['revision'] - 1
                assert backup.stat().st_mode & 0o777 == 0o600
                # Restore must remain exclusive even when backup gains read-only access.
                result = subprocess.run([sys.executable, '-m', 'tablekeeper.operations', '--namespace', 'main',
                                         'restore', str(backup), '--expected-revision', str(envelope['revision'])],
                                        env=env, capture_output=True, timeout=15)
                assert result.returncode != 0
            finally:
                stop.set()
                worker.result(timeout=10)
        destination = SQLiteStore(tmp_path / 'restored.sqlite3')
        try:
            revision = operations.maintenance(destination, 'main', True)
            operations.restore(destination, 'main', backup, revision)
            operations.maintenance(destination, 'main', False)
            assert destination.snapshot('main')[1] == restored
        finally:
            destination.close()
    finally:
        stop.set()
        owner.close()


@pytest.mark.parametrize('fault,exit_code,committed', [('before_commit', 86, False), ('after_commit', 87, True)])
def test_sqlite_crash_boundary(tmp_path, fault, exit_code, committed):
    path = tmp_path / 'crash.sqlite3'
    store = SQLiteStore(path)
    store.transact('main', lambda c: None, create=True)
    store.close()
    marker = tmp_path / 'arm'
    marker.touch()
    env = dict(os.environ, TABLEKEEPER_MODE='development', TABLEKEEPER_FAULT=fault,
               TABLEKEEPER_FAULT_ARM_FILE=str(marker))
    code = 'from tablekeeper.storage import SQLiteStore; import sys; s=SQLiteStore(sys.argv[1]); s.transact("main",lambda c:c.update(setup_consumed=True))'
    result = subprocess.run([sys.executable, '-c', code, str(path)], env=env, capture_output=True, timeout=10)
    assert result.returncode == exit_code
    reopened = SQLiteStore(path)
    try:
        revision, value = reopened.snapshot('main')
        assert value['setup_consumed'] is committed
        assert revision == (2 if committed else 1)
    finally:
        reopened.close()


def test_firestore_multiprocess_counter_and_revision():
    if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
        pytest.skip('Firestore emulator required')
    project = os.environ.get('ACCEPTANCE_FIRESTORE_PROJECT', 'demo-proofline-pilot')
    collection = 'verifier_' + uuid.uuid4().hex
    store = FirestoreStore(project, collection=collection)
    store.transact('main', lambda c: None, create=True)
    # The storage contract permits bounded contention errors. Retry a stable
    # operation identity, never a blind increment after an unknown outcome.
    code = '''from tablekeeper.storage import FirestoreStore,StoreError
import sys,time
s=FirestoreStore(sys.argv[1],collection=sys.argv[2])
for index in range(10):
    key=sys.argv[3]+':'+str(index)
    def operation(c):
        receipts=c.setdefault('acceptance_receipts',[])
        if key not in receipts:
            receipts.append(key)
            c['acceptance_counter']=c.get('acceptance_counter',0)+1
    for attempt in range(4):
        try:
            s.transact('main',operation)
            break
        except StoreError:
            if attempt==3: raise
            time.sleep(.1*(attempt+1))
s.close()
'''
    processes = [subprocess.Popen([sys.executable, '-c', code, project, collection, str(index)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for index in range(2)]
    try:
        for process in processes:
            _, stderr = process.communicate(timeout=90)
            assert process.returncode == 0, stderr.decode()[-1500:]
        revision, value = store.snapshot('main')
        assert revision == 21
        assert value['acceptance_counter'] == 20
        assert len(set(value['acceptance_receipts'])) == 20
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
        store.close()


@pytest.mark.parametrize('corruption', ['schema', 'checksum', 'chunk_revision', 'missing_chunk', 'chunk_size'])
def test_firestore_corrupt_root_or_chunk_refuses(corruption):
    if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
        pytest.skip('Firestore emulator required')
    project = os.environ.get('ACCEPTANCE_FIRESTORE_PROJECT', 'demo-proofline-pilot')
    store = FirestoreStore(project, collection='verifier_' + uuid.uuid4().hex)
    try:
        store.transact('main', lambda c: None, create=True)
        root = store.collection.document('main')
        chunk = root.collection('chunks').document('0')
        if corruption == 'schema':
            root.update({'schema': 999})
        elif corruption == 'checksum':
            root.update({'sha256': '0' * 64})
        elif corruption == 'chunk_revision':
            chunk.update({'revision': 999})
        elif corruption == 'missing_chunk':
            chunk.delete()
        else:
            chunk.update({'data': b'x' * (512 * 1024 + 1)})
        metadata = root.get().to_dict()
        with pytest.raises(StoreError):
            store.snapshot('main')
        with pytest.raises(StoreError):
            store.transact('main', lambda c: c.update(setup_consumed=True), create=True)
        assert root.get().to_dict() == metadata
    finally:
        store.close()
