#!/usr/bin/env python3
"""Two-phase operator revision-continuity check. Do not execute without authorization.
Only owns a newly created synthetic demo. Never invokes production setup or test controls.
Private state contains session material; public evidence never contains payloads or tokens.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
from urllib.parse import urlsplit

# This sibling is an operator test helper, not a deployed application dependency.
_helper = Path(__file__).with_name('verify-hosted.py')
_spec = importlib.util.spec_from_file_location('proofline_private_hosted_check', _helper)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
Audit, GateFailure = _module.Audit, _module.GateFailure


def secure_read(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid():
            raise GateFailure('private state must be an owned regular file with mode 0600')
        with os.fdopen(fd, 'r') as stream:
            fd = None
            return json.load(stream)
    finally:
        if fd is not None:
            os.close(fd)


def secure_create(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'w') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, separators=(',', ':'))
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def begin(audit):
    args = audit.args
    client = audit.client()
    session = audit.demo(client, 'continuity own visitor')
    response = audit.request(client, 'continuity venue discovery', 'GET', '/restaurants')
    audit.check('venue discovery HTTP 200', response.status_code == 200)
    venues = audit.body(response, 'venues').get('restaurants', [])
    audit.check('one synthetic venue', len(venues) == 1)
    rid = venues[0]['id']
    day = (date.today() + timedelta(days=400 + secrets.randbelow(5000))).isoformat()
    response = audit.request(client, 'continuity future availability', 'GET',
                             f'/availability?restaurant_id={rid}&date={day}&party_size=2')
    audit.check('availability HTTP 200', response.status_code == 200)
    available = [slot for slot in audit.body(response, 'availability').get('slots', []) if slot.get('available_table_ids')]
    audit.check('future synthetic seating available', bool(available))
    body = {'restaurant_id':rid, 'table_id':available[0]['available_table_ids'][0],
            'starts_at_local':available[0]['starts_at_local'], 'party_size':2}
    key = 'continuity-' + secrets.token_hex(16)
    response = audit.request(client, 'create continuity reservation', 'POST', '/reservations',
                             body=body, key=key, csrf=session['csrf_token'])
    audit.check('continuity reservation created', response.status_code == 201)
    receipt = audit.body(response, 'continuity receipt')
    cookie = client.cookies.get('__session')
    audit.check('owned demo cookie available privately', isinstance(cookie, str) and cookie.startswith('demo_'))
    # Only this private file contains the sensitive material, never evidence stdout.
    value = {'format':1, 'base_url':args.base_url, 'origin':args.origin, 'freeze_sha':args.freeze_sha,
             'image_digest':args.image_digest, 'old_revision':args.old_revision,
             'created_at_utc':datetime.now(timezone.utc).isoformat(), 'cookie':cookie,
             'csrf':session['csrf_token'], 'body':body, 'key':key,
             'reference':receipt['reference'], 'original_receipt':receipt, 'test_day':day}
    secure_create(args.state_file, value)
    audit.check('private continuity state saved mode 0600', stat.S_IMODE(Path(args.state_file).stat().st_mode) == 0o600)


def after(audit):
    args = audit.args
    value = secure_read(args.state_file)
    audit.check('supported private state', value.get('format') == 1)
    for field, expected in [('base_url', args.base_url), ('origin', args.origin), ('freeze_sha', args.freeze_sha),
                            ('image_digest', args.image_digest), ('old_revision', args.old_revision)]:
        audit.check('continuity metadata matches: ' + field, value.get(field) == expected)
    audit.check('operator names different old and new revisions', args.new_revision != args.old_revision)
    audit.check('state belongs to a synthetic demo', isinstance(value.get('cookie'), str) and value['cookie'].startswith('demo_'))
    client = audit.client()
    client.cookies.set('__session', value['cookie'], domain=urlsplit(args.base_url).hostname, path='/')
    response = audit.request(client, 'post-revision original booking lookup', 'GET', '/reservations/' + value['reference'])
    audit.check('original booking present after operator revision change', response.status_code == 200)
    audit.check('original booking response unchanged', audit.body(response, 'post-revision lookup') == value['original_receipt'])
    response = audit.request(client, 'post-revision original idempotency retry', 'POST', '/reservations',
                             body=value['body'], key=value['key'], csrf=value['csrf'])
    audit.check('original retry returns receipt HTTP 200', response.status_code == 200)
    audit.check('exact original receipt after operator revision change', audit.body(response, 'post-revision receipt') == value['original_receipt'])
    response = audit.request(client, 'post-revision own booking list', 'GET', '/reservations?scope=all&limit=50')
    audit.check('own booking list HTTP 200', response.status_code == 200)
    rows = audit.body(response, 'post-revision list').get('reservations', [])
    audit.check('exactly one booking on private unique test day',
                sum(row.get('starts_at_local', '').startswith(value['test_day']) for row in rows) == 1)
    audit.check('original reference appears exactly once', sum(row.get('reference') == value['reference'] for row in rows) == 1)
    # Keep old cookie in a separate client to check server revocation, not only deletion.
    revoked = audit.client()
    revoked.cookies.set('__session', value['cookie'], domain=urlsplit(args.base_url).hostname, path='/')
    response = audit.request(client, 'logout continuity own session', 'POST', '/auth/logout', body={}, csrf=value['csrf'])
    audit.check('continuity logout succeeds', response.status_code == 200)
    response = audit.request(revoked, 'post-logout retained cookie probe', 'GET', '/reservations/' + value['reference'])
    audit.check('continuity session revoked server-side', response.status_code in (401,404))


def origin(value):
    u = urlsplit(value)
    if u.scheme != 'https' or not u.netloc or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:
        raise argparse.ArgumentTypeError('expected bare HTTPS origin')
    return value.rstrip('/')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['begin','after'], required=True)
    parser.add_argument('--base-url', type=origin, required=True)
    parser.add_argument('--origin', type=origin)
    parser.add_argument('--state-file', required=True, help='Explicit private state path; begin creates owned mode-0600 file exclusively')
    parser.add_argument('--output', required=True, help='New public-safe evidence JSON; never overwritten')
    parser.add_argument('--freeze-sha', required=True)
    parser.add_argument('--image-digest', required=True)
    parser.add_argument('--old-revision', required=True, help='Operator-supplied original Cloud Run revision')
    parser.add_argument('--new-revision', help='Required after; operator-supplied serving revision after update')
    args = parser.parse_args()
    args.origin = args.origin or args.base_url
    if not re.fullmatch('[0-9a-f]{40}', args.freeze_sha):
        parser.error('freeze-sha must be a full commit SHA')
    if not re.fullmatch(r'(?:[A-Za-z0-9._:/-]+@)?sha256:[0-9a-f]{64}', args.image_digest):
        parser.error('expected image sha256 digest, optionally prefixed by image reference')
    for revision in (args.old_revision, args.new_revision):
        if revision is not None and not re.fullmatch('[a-z][a-z0-9-]{1,62}', revision):
            parser.error('revision must be a Cloud Run revision name')
    if args.phase == 'after' and not args.new_revision:
        parser.error('after requires --new-revision')
    state_path, output_path = Path(args.state_file), Path(args.output)
    if state_path.resolve() == output_path.resolve():
        parser.error('private state and public evidence must be different paths')
    if not state_path.parent.is_dir() or not output_path.parent.is_dir():
        parser.error('state/evidence parent directories must already exist')
    if output_path.exists() or output_path.is_symlink():
        parser.error('output must be a fresh file')
    if args.phase == 'begin' and (state_path.exists() or state_path.is_symlink()):
        parser.error('begin requires a new private state file')
    if args.phase == 'after' and (not state_path.is_file() or state_path.is_symlink()):
        parser.error('after requires an existing private regular state file')
    audit = Audit(args)
    failure = None
    try:
        (begin if args.phase == 'begin' else after)(audit)
    except GateFailure as exc:
        failure = {'type':'assertion_failure', 'assertion':str(exc)}
    except Exception as exc:
        failure = {'type':'execution_error', 'exception_class':type(exc).__name__}
    finally:
        for client in audit.clients:
            client.close()
    result = {'phase':args.phase, 'started_at_utc':audit.started,
              'finished_at_utc':datetime.now(timezone.utc).isoformat(),
              'duration_seconds':round(time.monotonic()-audit.start,3),
              'base_url':args.base_url, 'request_origin':args.origin,
              'freeze_sha':args.freeze_sha, 'operator_supplied_image_digest':args.image_digest,
              'operator_supplied_old_revision':args.old_revision,
              'operator_supplied_new_revision':args.new_revision,
              'passed':failure is None, 'failure':failure, 'checks':audit.rows,
              'limitations':['Revision names, image digest and traffic switch are operator-supplied, not remotely attested by this script.',
                'Operator must independently retain gcloud describe evidence of same image, new revision and 100 percent serving traffic.',
                'Only this run own synthetic demo was mutated; no test reset/import or production setup was invoked.',
                'Begin alone is not restart durability evidence. After must run after verified new revision routing.',
                'Cookies, CSRF, request body, booking reference and original response exist only in the explicit private mode-0600 state file.',
                'Session revocation occurs after successful checks; expired demo/session or failed checks yield honest failure evidence.',
                'Direct Cloud Run testing does not prove Firebase Hosting behavior; final hosted/browser checks remain separate.']}
    with output_path.open('x') as out:
        json.dump(result,out,indent=2);out.write('\n')
    print('PASS' if failure is None else 'FAIL', args.phase, 'continuity evidence saved; private state not printed')
    return 0 if failure is None else 1


if __name__ == '__main__':
    sys.exit(main())
