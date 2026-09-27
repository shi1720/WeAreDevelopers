"""Author emulator checks. No real project credentials or deployed data."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
import subprocess
import sys
import uuid

import pytest

from tablekeeper import operations
from tablekeeper.storage import FirestoreStore, MAX_BYTES, encode, fresh, StoreError
from tablekeeper.validation import APIError


@pytest.fixture
def store():
    if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
        pytest.skip('Explicit Firestore emulator required')
    value = FirestoreStore('demo-proofline-pilot', 'author_' + uuid.uuid4().hex)
    value.transact('main', lambda v: None, create=True)
    yield value
    value.close()


def worker(store, source, **extra):
    environment = dict(os.environ, AUTHOR_COLLECTION=store.collection.id, **extra)
    return subprocess.Popen([sys.executable, '-c', source], env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


PRELUDE = "from tablekeeper.storage import FirestoreStore; import os; s=FirestoreStore('demo-proofline-pilot',os.environ['AUTHOR_COLLECTION']); "


def test_two_live_processes_serialize_booking(store):
    from tablekeeper.demo import fixture
    from tablekeeper.state import from_fixture
    store.transact('main', lambda value: value.update(domain=from_fixture(fixture()), setup_consumed=True))
    source = PRELUDE + """
from tablekeeper import reservations
from tablekeeper.validation import APIError
import time
time.sleep(0.2)
body={'restaurant_id':'the_orangery','table_id':'window','starts_at_local':'2035-06-15T19:00','party_size':2}
try:
    result=s.transact('main',lambda value: reservations.idempotent(value['domain'],'demo_guest','POST','/reservations',os.environ['AUTHOR_KEY'],body,lambda: reservations.create(value['domain'],'demo_guest',body)))
    print(result[0])
except APIError as error:
    print(error.status)
s.close()
"""
    first = worker(store, source, AUTHOR_KEY='first')
    second = worker(store, source, AUTHOR_KEY='second')
    values = []
    for process in (first, second):
        output, error = process.communicate(timeout=30)
        assert process.returncode == 0, error
        values.append(int(output.strip()))
    assert sorted(values) == [201, 409]
    assert len(store.snapshot('main')[1]['domain']['reservations']) == 4


def test_sdk_callback_retry_uses_private_candidate(store, monkeypatch):
    from google.api_core.exceptions import Aborted
    from google.cloud.firestore_v1.transaction import Transaction
    original = Transaction._commit
    calls = []
    def commit(transaction):
        calls.append(True)
        if len(calls) == 1:
            # A server-side ABORTED releases its lock. Reproduce that boundary
            # rather than leaving an artificial live transaction in the emulator.
            transaction._client._firestore_api.rollback(request={
                'database': transaction._client._database_string, 'transaction': transaction.id})
            raise Aborted('synthetic retry')
        return original(transaction)
    monkeypatch.setattr(Transaction, '_commit', commit)
    count = []
    def change(value):
        count.append(True)
        value['author_counter'] = value.get('author_counter', 0) + 1
        return value['author_counter']
    assert store.transact('main', change) == 1
    assert len(count) == 2
    assert store.snapshot('main')[1]['author_counter'] == 1


def test_chunk_capacity_and_hash_fail_closed(store):
    value = fresh()
    value['author_padding'] = ''
    value['author_padding'] = 'x' * (MAX_BYTES - len(encode(value)))
    def replace(candidate):
        candidate.clear()
        candidate.update(value)
    store.transact('main', replace)
    before = store.snapshot('main')
    assert store.collection.document('main').get().to_dict()['chunks'] == 8
    with pytest.raises(APIError):
        store.transact('main', lambda candidate: candidate.update(author_padding=candidate['author_padding'] + 'x'))
    assert store.snapshot('main') == before
    store.collection.document('main').collection('chunks').document('0').update({'data': b'bad'})
    with pytest.raises(StoreError):
        store.snapshot('main')


@pytest.mark.parametrize('fault,expected,code', [('before_commit', False, 86), ('after_commit', True, 87)])
def test_crash_boundaries(store, tmp_path, fault, expected, code):
    marker = tmp_path / 'arm'
    marker.touch()
    process = worker(store, PRELUDE + "s.transact('main',lambda value:value.update(setup_consumed=True))", TABLEKEEPER_MODE='development', TABLEKEEPER_FAULT=fault, TABLEKEEPER_FAULT_ARM_FILE=str(marker))
    output, error = process.communicate(timeout=30)
    assert process.returncode == code, error
    assert store.snapshot('main')[1]['setup_consumed'] is expected


def test_backup_during_writes_and_restore_cas(store, tmp_path):
    def updates():
        for index in range(10):
            store.transact('main', lambda value: value.update(author_sequence=index, author_double=index * 2))
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(updates)
        for index in range(4):
            file = tmp_path / f'backup-{index}.json'
            operations.backup(store, 'main', file)
            restored = operations.read_backup(file)
            assert restored.get('author_double', 0) == restored.get('author_sequence', 0) * 2
        running.result()
    revision = operations.maintenance(store, 'main', True)
    with pytest.raises(APIError):
        operations.restore(store, 'main', file, revision - 1)
    operations.restore(store, 'main', file, revision, True)
    operations.maintenance(store, 'main', False)
