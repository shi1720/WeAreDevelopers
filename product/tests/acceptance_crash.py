"""Crash at durable boundaries, then recover the original HTTP operation."""
import os
import time
import uuid

import httpx
import pytest

from acceptance_http import Service, BrowserClient
from tablekeeper.storage import SQLiteStore, FirestoreStore


@pytest.mark.parametrize('adapter', ['sqlite', 'firestore'])
@pytest.mark.parametrize('fault,exit_code,expected', [('before_commit',86,201),('after_commit',87,200),('commit_failure',None,201)])
def test_http_crash_exact_receipt_recovery(tmp_path, adapter, fault, exit_code, expected):
    config = {}
    collection = 'verifier_' + uuid.uuid4().hex
    if adapter == 'firestore':
        if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
            pytest.skip('Firestore emulator required')
        config = {'TABLEKEEPER_STORAGE':'firestore','GOOGLE_CLOUD_PROJECT':'demo-proofline-pilot','TABLEKEEPER_COLLECTION':collection}
    service = Service(tmp_path, overrides=config)
    try:
        owner = BrowserClient(service)
        rid = owner.setup()
        body = {'restaurant_id':rid,'table_id':'table_1','starts_at_local':'2032-06-17T18:00','party_size':2}
        marker = tmp_path / 'arm'
        service.environment.update(TABLEKEEPER_FAULT=fault, TABLEKEEPER_FAULT_ARM_FILE=str(marker))
        service.restart()
        marker.touch()
        if exit_code is None:
            assert owner.request('POST','/reservations',body,'crash-key').status_code == 503
            service.stop()
        else:
            with pytest.raises(httpx.TransportError):
                owner.request('POST','/reservations',body,'crash-key')
            service.process.wait(timeout=10)
            assert service.process.returncode == exit_code
        store = SQLiteStore(tmp_path / 'state.sqlite3') if adapter == 'sqlite' else FirestoreStore('demo-proofline-pilot',collection=collection)
        try:
            _, value = store.snapshot('main')
            committed = value['domain']['receipts']
            assert len(value['domain']['reservations']) == (1 if fault == 'after_commit' else 0)
            assert len(committed) == (1 if fault == 'after_commit' else 0)
            original = committed[0]['response'] if committed else None
        finally:
            store.close()
        service.environment.pop('TABLEKEEPER_FAULT')
        service.start()
        # A killed Firestore transaction can hold locks until server expiry.
        # Transport timeout remains unknown outcome, so repeat only exact key/body.
        result = None
        # Emulator observation: a killed transaction releases its lock after
        # about60s. Eight10s HTTP attempts bound recovery beyond that window.
        for attempt in range(8):
            try:
                response = owner.request('POST','/reservations',body,'crash-key')
            except httpx.TransportError:
                if attempt == 7:
                    raise
                time.sleep(1)
                continue
            if response.status_code == 503 and attempt < 7:
                time.sleep(1)
                continue
            assert response.status_code in ((200,) if expected == 200 else (200,201))
            result = response.json()
            break
        assert result is not None
        if original is not None:
            assert result == original
        assert owner.expect(200,'POST','/reservations',body,'crash-key') == result
        assert len(owner.expect(200,'GET','/reservations')['reservations']) == 1
        history = owner.expect(200,'GET','/reservations/'+result['reference']+'/history')['entries']
        assert len(history) == 1 and history[0]['event'] == 'created'
    finally:
        service.close()
