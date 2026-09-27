"""Private operator commands. Run with the backend service identity, never in a browser."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from .storage import decode, encode, open_store, StoreError, SQLiteReader
from .validation import APIError


def backup(store, namespace, destination):
    revision, value = store.snapshot(namespace)
    raw = encode(value)
    envelope = {'format': 'tablekeeper-companion-backup-1', 'namespace': namespace,
                'revision': revision, 'created_at': time.time(), 'sha256': hashlib.sha256(raw).hexdigest(),
                'state': value}
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(envelope, output, sort_keys=True, separators=(',', ':'), allow_nan=False)
        output.flush()
        os.fsync(output.fileno())
    return revision


def read_backup(source):
    if Path(source).stat().st_size > 5 * 1024 * 1024:
        raise StoreError('Backup exceeds capacity')
    try:
        envelope = json.loads(Path(source).read_text())
        if envelope['format'] != 'tablekeeper-companion-backup-1':
            raise StoreError('Unsupported backup format')
        raw = encode(envelope['state'])
        return decode(raw, envelope['sha256'])
    except (ValueError, KeyError, TypeError) as exc:
        raise StoreError('Invalid backup') from exc


def maintenance(store, namespace, enabled):
    def update(value):
        value['maintenance'] = {'since': time.time()} if enabled else None
    store.transact(namespace, update, create=True, maintenance=True)
    return store.snapshot(namespace)[0]


def restore(store, namespace, source, revision, revoke_sessions=False):
    restored = read_backup(source)  # Validate before touching existing state.
    if namespace == 'main' and restored['demo']:
        raise StoreError('Cannot restore a demo into the production namespace')
    if namespace.startswith('demo_') and not restored['demo']:
        raise StoreError('Cannot restore production state into a demo namespace')
    def replace(value):
        if not value['maintenance']:
            raise StoreError('Restore requires an explicit maintenance lock')
        replacement = deepcopy(restored)
        replacement['maintenance'] = value['maintenance']
        if revoke_sessions:
            replacement['sessions'] = {}
        # Expiration is absolute: restore never extends session/demo lifetimes.
        value.clear()
        value.update(replacement)
    store.transact(namespace, replace, maintenance=True, expected_revision=revision)
    return store.snapshot(namespace)[0]


def cleanup(store, limit=20):
    now = time.time()
    _, main = store.snapshot('main')
    expired = [key for key, expiry in main['registry'].items() if expiry <= now][:limit]
    for namespace in expired:
        # Expired namespaces cannot accept writes, so deleting their chunks is safe.
        store.delete(namespace)
        def remove(value):
            if value['registry'].get(namespace, now + 1) <= now:
                value['registry'].pop(namespace, None)
        store.transact('main', remove, maintenance=True)
    return len(expired)


def reset_password(store, namespace, user_id, password_file):
    from .auth import hash_password
    source = Path(password_file)
    if source.stat().st_mode & 0o077:
        raise StoreError('Password file must have private permissions')
    password = source.read_text().rstrip('\n')
    if not 12 <= len(password) <= 256:
        raise StoreError('Invalid password length')
    hashed = hash_password(password)
    def update(value):
        if value['demo'] or user_id not in value['domain']['users']:
            raise StoreError('Invalid recovery target')
        value['domain']['users'][user_id]['password_hash'] = hashed
        value['sessions'] = {key: session for key, session in value['sessions'].items() if session['user_id'] != user_id}
    store.transact(namespace, update)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', default='main')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    b = commands.add_parser('backup')
    b.add_argument('file')
    m = commands.add_parser('maintenance')
    m.add_argument('action', choices=('on', 'off'))
    r = commands.add_parser('restore')
    r.add_argument('file')
    r.add_argument('--expected-revision', type=int, required=True)
    r.add_argument('--revoke-sessions', action='store_true')
    c = commands.add_parser('cleanup')
    c.add_argument('--limit', type=int, default=20, choices=range(1, 101))
    p = commands.add_parser('reset-password')
    p.add_argument('--user-id', required=True)
    p.add_argument('--password-file', required=True)
    args = parser.parse_args()
    store = None
    try:
        store = (SQLiteReader(os.environ.get('TABLEKEEPER_DB', './data/tablekeeper.sqlite3'))
                 if args.command in ('backup', 'status') and os.environ.get('TABLEKEEPER_STORAGE', 'sqlite') == 'sqlite'
                 else open_store())
        if args.command == 'backup':
            result = {'revision': backup(store, args.namespace, args.file)}
        elif args.command == 'maintenance':
            result = {'revision': maintenance(store, args.namespace, args.action == 'on')}
        elif args.command == 'restore':
            result = {'revision': restore(store, args.namespace, args.file, args.expected_revision, args.revoke_sessions)}
        elif args.command == 'cleanup':
            result = {'removed': cleanup(store, args.limit)}
        elif args.command == 'reset-password':
            reset_password(store, args.namespace, args.user_id, args.password_file)
            result = {'changed': True, 'sessions_revoked': True}
        else:
            revision, value = store.snapshot(args.namespace)
            result = {'revision': revision, 'maintenance': bool(value['maintenance']), 'configured': value['setup_consumed']}
        print(json.dumps(result))
    except (StoreError, APIError, OSError):
        print('Operation failed safely. Check private file permissions, state integrity, store ownership and revision.', file=sys.stderr)
        return 1
    finally:
        if store:
            store.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
