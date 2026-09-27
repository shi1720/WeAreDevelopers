"""Durable candidate transactions. No callback may publish outside its candidate."""
from copy import deepcopy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from threading import RLock, local
import time

from .state import empty, validate_state
from .validation import APIError

MAX_BYTES = 4 * 1024 * 1024
CHUNK_BYTES = 512 * 1024
MAX_REQUEST_BYTES = 8 * 1024 * 1024
STORE_NETWORK_SECONDS = 8.0
RPC_SECONDS = 4.0


class StoreError(RuntimeError):
    """Private operational failure; never include payloads in public errors."""


def fresh():
    return {'schema': 1, 'domain': empty(), 'sessions': {}, 'attempts': {},
            'extra_receipts': [], 'setup_consumed': False, 'demo': False,
            'expires_at': None, 'registry': {}, 'maintenance': None}


def validate(value):
    try:
        if type(value) is not dict or type(value.get('schema')) is not int or value.get('schema') != 1:
            raise ValueError('unsupported schema')
        validate_state(value['domain'])
        if value['domain']['tokens']:
            raise ValueError('legacy tokens are not allowed')
        for key in ('sessions', 'attempts', 'registry'):
            if type(value[key]) is not dict:
                raise ValueError('invalid metadata')
        if len(value['sessions']) > 1024 or len(value['attempts']) > 1024 or len(value['registry']) > 100:
            raise ValueError('metadata capacity')
        for digest, session in value['sessions'].items():
            if not re.fullmatch('[0-9a-f]{64}', digest) or type(session) is not dict:
                raise ValueError('invalid session')
            if session['user_id'] is not None and session['user_id'] not in value['domain']['users']:
                raise ValueError('invalid session owner')
            if not all(type(session[k]) in (int, float) and math.isfinite(session[k]) and session[k] >= 0 for k in ('expires_at', 'last_seen')):
                raise ValueError('invalid session lifetime')
            if not re.fullmatch('[0-9a-f]{64}', session['csrf']):
                raise ValueError('invalid csrf digest')
        if type(value['setup_consumed']) is not bool or type(value['demo']) is not bool:
            raise ValueError('invalid flags')
        if not value['setup_consumed'] and value['domain'] != empty():
            raise ValueError('unconsumed setup cannot contain configured domain state')
        if value['setup_consumed']:
            venues = value['domain']['restaurants']
            if len(venues) != 1 or not venues[0].get('manager_user_ids'):
                raise ValueError('configured namespace requires one venue and a valid manager')
        if 'scope_generation' in value and (type(value['scope_generation']) is not str or not re.fullmatch('[0-9a-f]{32}', value['scope_generation'])):
            raise ValueError('invalid recovery generation')
        if value['expires_at'] is not None and (type(value['expires_at']) not in (int, float) or not math.isfinite(value['expires_at'])):
            raise ValueError('invalid namespace lifetime')
        if value['demo']:
            if not value['setup_consumed'] or not value['domain']['restaurants'] or value['expires_at'] is None or value['expires_at'] <= 0:
                raise ValueError('demo requires configured state and finite positive expiry')
        elif value['expires_at'] is not None:
            raise ValueError('non-demo namespace cannot have demo expiry')
        lock = value['maintenance']
        if lock is not None and (type(lock) is not dict or set(lock) != {'since'}
                or type(lock['since']) not in (int, float) or not math.isfinite(lock['since']) or lock['since'] < 0):
            raise ValueError('invalid maintenance lock')
        for entry in value['attempts'].values():
            if type(entry['count']) is not int or entry['count'] < 0 or type(entry['until']) not in (int, float) or not math.isfinite(entry['until']):
                raise ValueError('invalid throttle')
        for name, expiry in value['registry'].items():
            namespace_id(name)
            if name == 'main' or type(expiry) not in (int, float) or not math.isfinite(expiry):
                raise ValueError('invalid demo registry')
        if len(value['domain']['restaurants']) > 1:
            raise ValueError('one venue per namespace required')
        for venue in value['domain']['restaurants']:
            if not 1 <= len(venue['tables']) <= 6 or len(venue['combinable']) > 4:
                raise ValueError('unsupported inventory')
        if type(value['extra_receipts']) is not list:
            raise ValueError('invalid receipts')
        seen = set()
        for receipt in value['extra_receipts']:
            scope = tuple(receipt[k] for k in ('user_id', 'method', 'path', 'key'))
            if scope in seen or receipt['user_id'] not in value['domain']['users']:
                raise ValueError('invalid receipt scope')
            seen.add(scope)
            if receipt['method'] not in ('PATCH', 'POST') or type(receipt['body']) is not dict or type(receipt['response']) is not dict:
                raise ValueError('invalid receipt')
            from .state import validate_record, validate_historical_response
            response = dict(receipt['response'], user_id=receipt['user_id'])
            validate_record(response, value['domain'])
            validate_historical_response(value['domain'], response)
            expected_path = '/reservations/' + response['reference'] + ('/cancel' if receipt['method'] == 'POST' else '')
            if receipt['path'] != expected_path or not isinstance(receipt['key'], str) or not 1 <= len(receipt['key']) <= 255:
                raise ValueError('invalid receipt route')
        return value
    except (KeyError, TypeError, ValueError, APIError) as exc:
        raise StoreError('Invalid or unsupported durable state') from exc


def encode(value):
    validate(value)
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    if len(raw) > MAX_BYTES:
        raise APIError(507, 'state_capacity', 'Venue storage is full. Export a private backup and contact the operator; no history or receipt was discarded.')
    return raw


def decode(raw, checksum):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != checksum:
        raise StoreError('Durable state checksum or size mismatch')
    try:
        return validate(json.loads(raw))
    except (ValueError, UnicodeError) as exc:
        raise StoreError('Invalid durable JSON') from exc


def namespace_id(namespace):
    if not re.fullmatch(r'(?:main|demo_[0-9a-f]{32})', namespace):
        raise StoreError('Invalid namespace')
    return namespace


def fault(point):
    """Host-controlled local test hook, never enabled in production or over HTTP."""
    if os.environ.get('TABLEKEEPER_MODE') != 'development':
        return
    if os.environ.get('TABLEKEEPER_FAULT') != point:
        return
    marker = os.environ.get('TABLEKEEPER_FAULT_ARM_FILE')
    if not marker or not Path(marker).exists():
        return
    Path(marker).unlink()
    if point == 'commit_failure':
        raise StoreError('Injected persistence failure')
    os._exit(86 if point == 'before_commit' else 87)


class SQLiteStore:
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = RLock()
        self.owner = open(self.path + '.owner', 'a+b')
        os.chmod(self.path + '.owner', 0o600)
        try:
            fcntl.flock(self.owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.owner.close()
            raise StoreError('SQLite store already has an owner') from exc
        self.db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        os.chmod(self.path, 0o600)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS namespaces (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload BLOB NOT NULL, checksum TEXT NOT NULL)')
        for raw, checksum in self.db.execute('SELECT payload,checksum FROM namespaces'):
            decode(raw, checksum)

    def transact(self, namespace, callback, *, create=False, maintenance=False, expected_revision=None):
        namespace_id(namespace)
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                row = self.db.execute('SELECT revision,payload,checksum FROM namespaces WHERE id=?', (namespace,)).fetchone()
                if expected_revision is not None and (0 if row is None else row[0]) != expected_revision:
                    raise APIError(409, 'stale_store_revision')
                if row is None and not create:
                    raise APIError(404, 'not_found')
                value = fresh() if row is None else decode(row[1], row[2])
                if value['maintenance'] and not maintenance:
                    raise APIError(503, 'maintenance')
                result = callback(value)
                raw = encode(value)
                if row is None or raw != row[1]:
                    fault('before_commit')
                    fault('commit_failure')
                    self.db.execute('INSERT OR REPLACE INTO namespaces VALUES (?,?,?,?)',
                        (namespace, 1 if row is None else row[0] + 1, raw, hashlib.sha256(raw).hexdigest()))
                self.db.execute('COMMIT')
            except BaseException:
                if self.db.in_transaction:
                    self.db.execute('ROLLBACK')
                raise
            fault('after_commit')
            return result

    def snapshot(self, namespace):
        with self.lock:
            row = self.db.execute('SELECT revision,payload,checksum FROM namespaces WHERE id=?', (namespace_id(namespace),)).fetchone()
            if row is None:
                raise APIError(404, 'not_found')
            return row[0], decode(row[1], row[2])

    def delete(self, namespace):
        if namespace == 'main':
            raise StoreError('Cannot delete main namespace')
        with self.lock:
            self.db.execute('DELETE FROM namespaces WHERE id=?', (namespace_id(namespace),))

    def close(self):
        self.db.close()
        self.owner.close()


class SQLiteReader:
    """Read-only snapshots may coexist with the exclusive writer."""
    def __init__(self, path):
        from urllib.parse import quote
        self.db = sqlite3.connect('file:' + quote(str(Path(path).resolve())) + '?mode=ro', uri=True)

    def snapshot(self, namespace):
        row = self.db.execute('SELECT revision,payload,checksum FROM namespaces WHERE id=?', (namespace_id(namespace),)).fetchone()
        if row is None:
            raise APIError(404, 'not_found')
        return row[0], decode(row[1], row[2])

    def close(self):
        self.db.close()


class FirestoreStore:
    def __init__(self, project, collection='tablekeeper', database='(default)'):
        from google.cloud import firestore
        if not project or not re.fullmatch('[a-zA-Z0-9_-]{1,64}', collection):
            raise StoreError('Explicit project and valid collection required')
        self.firestore = firestore
        self.clock = local()
        clock = self.clock

        class DeadlineAPI:
            """Bound the pinned SDK's internal transaction RPCs as well as reads."""
            def __init__(self, api):
                self.api = api

            def __getattr__(self, name):
                target = getattr(self.api, name)
                if name not in ('begin_transaction', 'batch_get_documents', 'commit', 'rollback'):
                    return target

                def call(*args, **kwargs):
                    remaining = getattr(clock, 'deadline', time.monotonic() + RPC_SECONDS) - time.monotonic()
                    if name == 'rollback':
                        # Release server locks even when the main budget expired.
                        timeout = 1.0
                    else:
                        if remaining <= 0:
                            raise StoreError('Firestore operation deadline exceeded; retry unchanged request')
                        timeout = min(RPC_SECONDS, remaining)
                    kwargs.update(retry=None, timeout=timeout)
                    return target(*args, **kwargs)
                return call

        class DeadlineClient(firestore.Client):
            @property
            def _firestore_api(self):
                # SDK2.21 Transaction methods lack public timeout parameters.
                # Keep SDK transaction/retry logic, bounding its GAPIC boundary.
                return DeadlineAPI(super()._firestore_api)

        self.client = DeadlineClient(project=project, database=database)
        self.collection = self.client.collection(collection)

    @contextmanager
    def network_budget(self):
        previous = getattr(self.clock, 'deadline', None)
        self.clock.deadline = time.monotonic() + STORE_NETWORK_SECONDS
        try:
            yield
        finally:
            if previous is None:
                del self.clock.deadline
            else:
                self.clock.deadline = previous

    def _read(self, namespace, transaction):
        root = self.collection.document(namespace_id(namespace))
        snap = root.get(transaction=transaction)
        if not snap.exists:
            return root, None, None
        meta = snap.to_dict()
        if meta.get('schema') != 1 or type(meta.get('chunks')) is not int or not 1 <= meta['chunks'] <= 8:
            raise StoreError('Unsupported Firestore root')
        if type(meta.get('revision')) is not int or meta['revision'] < 1:
            raise StoreError('Invalid Firestore revision')
        blobs = []
        for index in range(meta['chunks']):
            chunk = root.collection('chunks').document(str(index)).get(transaction=transaction)
            item = chunk.to_dict() if chunk.exists else {}
            data = item.get('data')
            if not isinstance(data, bytes) or len(data) > CHUNK_BYTES or item.get('revision') != meta['revision']:
                raise StoreError('Missing or invalid Firestore chunk')
            blobs.append(data)
        raw = b''.join(blobs)
        if len(raw) != meta.get('bytes'):
            raise StoreError('Invalid Firestore size')
        return root, meta, decode(raw, meta.get('sha256'))

    def transact(self, namespace, callback, *, create=False, maintenance=False, expected_revision=None):
        from google.cloud.firestore_v1.types import CommitRequest
        transaction = self.client.transaction(max_attempts=5)

        @self.firestore.transactional
        def execute(tx):
            root, meta, value = self._read(namespace, tx)
            if expected_revision is not None and (0 if meta is None else meta['revision']) != expected_revision:
                raise APIError(409, 'stale_store_revision')
            if value is None:
                if not create:
                    raise APIError(404, 'not_found')
                value = fresh()
            before = encode(value)
            if value['maintenance'] and not maintenance:
                raise APIError(503, 'maintenance')
            result = callback(value)
            raw = encode(value)
            if meta is None or raw != before:
                revision = 1 if meta is None else meta['revision'] + 1
                chunks = [raw[i:i + CHUNK_BYTES] for i in range(0, len(raw), CHUNK_BYTES)]
                for index, data in enumerate(chunks):
                    tx.set(root.collection('chunks').document(str(index)), {'data': data, 'revision': revision})
                for index in range(len(chunks), 0 if meta is None else meta['chunks']):
                    tx.delete(root.collection('chunks').document(str(index)))
                tx.set(root, {'schema': 1, 'revision': revision, 'chunks': len(chunks),
                              'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
                # Measure actual protobuf writes, not a JSON-size approximation.
                request = CommitRequest(database=self.client._database_string, writes=tx._write_pbs,
                                        transaction=tx.id or b'')
                if len(CommitRequest.serialize(request)) > MAX_REQUEST_BYTES:
                    raise APIError(507, 'state_capacity')
                for write in tx._write_pbs:
                    if write.update and len(type(write.update).serialize(write.update)) > 768 * 1024:
                        raise APIError(507, 'state_capacity')
                fault('before_commit')
                fault('commit_failure')
            return result

        try:
            with self.network_budget():
                result = execute(transaction)
        except (APIError, StoreError):
            raise
        except Exception as exc:
            raise StoreError('Firestore transaction unavailable; retry the unchanged request') from exc
        fault('after_commit')
        return result

    def snapshot(self, namespace):
        transaction = self.client.transaction(max_attempts=5, read_only=True)

        @self.firestore.transactional
        def read(tx):
            _, meta, value = self._read(namespace, tx)
            if value is None:
                raise APIError(404, 'not_found')
            return meta['revision'], value
        try:
            with self.network_budget():
                return read(transaction)
        except (APIError, StoreError):
            raise
        except Exception as exc:
            raise StoreError('Firestore snapshot unavailable') from exc

    def delete(self, namespace):
        if namespace == 'main':
            raise StoreError('Cannot delete main namespace')
        root = self.collection.document(namespace_id(namespace))
        batch = self.client.batch()
        for index in range(8):
            batch.delete(root.collection('chunks').document(str(index)))
        batch.delete(root)
        batch.commit()

    def close(self):
        self.client.close()


def open_store():
    adapter = os.environ.get('TABLEKEEPER_STORAGE', 'sqlite')
    if adapter == 'sqlite':
        if os.environ.get('K_SERVICE'):
            raise StoreError('Cloud Run requires Firestore authoritative storage')
        return SQLiteStore(os.environ.get('TABLEKEEPER_DB', './data/tablekeeper.sqlite3'))
    if adapter == 'firestore':
        return FirestoreStore(os.environ.get('GOOGLE_CLOUD_PROJECT'),
                              os.environ.get('TABLEKEEPER_COLLECTION', 'tablekeeper'),
                              os.environ.get('TABLEKEEPER_DATABASE', '(default)'))
    raise StoreError('Unsupported storage adapter')
