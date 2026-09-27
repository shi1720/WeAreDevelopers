#!/usr/bin/env python3
"""Operator-only hosted checks. NEVER run before deployment authorization.
Booking mutations affect only two synthetic demo namespaces. One deliberately invalid
setup request verifies the secret gate; no import or judge-reset calls are made.
All cookies, CSRF values and response bodies stay in memory and out of evidence.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, date, timedelta
from http.cookies import SimpleCookie
import json
from pathlib import Path
import re
import secrets
import sys
import time
from urllib.parse import urlsplit

import httpx


class GateFailure(Exception):
    pass


class Audit:
    def __init__(self, args):
        self.args = args
        self.rows = []
        self.clients = []
        self.start = time.monotonic()
        self.started = datetime.now(timezone.utc).isoformat()

    def check(self, name, condition):
        self.rows.append({'assertion': name, 'passed': bool(condition)})
        if not condition:
            raise GateFailure(name)

    def client(self, cookies=None):
        client = httpx.Client(base_url=self.args.base_url, timeout=30, follow_redirects=False,
                              trust_env=False, headers={'Accept': 'application/json'}, cookies=cookies)
        self.clients.append(client)
        return client

    def request(self, client, name, method, path, *, body=None, csrf=None, key=None, origin=None):
        headers = {}
        if method != 'GET':
            headers['Origin'] = self.args.origin if origin is None else origin
            if csrf is not None:
                headers['X-CSRF-Token'] = csrf
        if key is not None:
            headers['idempotency-key'] = key  # Intentionally lowercase: HTTP header names are case-insensitive.
        start = time.monotonic()
        response = client.request(method, path, headers=headers, json=body if method != 'GET' else None)
        self.rows.append({'request': name, 'status': response.status_code,
                          'duration_seconds': round(time.monotonic() - start, 3)})
        self.check(name + ': private no-store',
                   {'private', 'no-store'} <= {v.strip().lower() for v in response.headers.get('cache-control', '').split(',')})
        return response

    def body(self, response, name):
        try:
            value = response.json()
        except (ValueError, UnicodeError):
            raise GateFailure(name + ': expected JSON') from None
        self.check(name + ': JSON object', isinstance(value, dict))
        return value

    def cookie(self, response, name):
        values = response.headers.get_list('set-cookie')
        matched = []
        for value in values:
            parsed = SimpleCookie()
            parsed.load(value)
            if '__session' in parsed:
                matched.append(parsed['__session'])
        self.check(name + ': one session cookie', len(matched) == 1)
        cookie = matched[0]
        self.check(name + ': Secure HttpOnly SameSite=Lax Path=/',
                   bool(cookie['secure']) and bool(cookie['httponly'])
                   and cookie['samesite'].lower() == 'lax' and cookie['path'] == '/')

    def session(self, client, name):
        response = self.request(client, name, 'GET', '/api/session')
        self.check(name + ': HTTP 200', response.status_code == 200)
        body = self.body(response, name)
        self.check(name + ': CSRF supplied', isinstance(body.get('csrf_token'), str) and bool(body['csrf_token']))
        return body, response

    def demo(self, client, name):
        anon, response = self.session(client, name + ' anonymous preparation')
        self.cookie(response, name + ' anonymous')
        self.check(name + ': demo enabled', anon.get('demo_enabled') is True)
        response = self.request(client, name + ' start own isolated demo', 'POST', '/api/demo/start',
                                body={}, csrf=anon['csrf_token'])
        self.check(name + ': started', response.status_code == 201)
        self.cookie(response, name + ' demo')
        state = self.body(response, name)
        self.check(name + ': synthetic authenticated guest',
                   state.get('demo') is True and state.get('authenticated') is True and state.get('role') == 'guest')
        return state

    def run(self):
        a, b, boundary = self.client(), self.client(), self.client()
        for path in ('/health', '/health/live', '/health/ready'):
            r = self.request(a, path, 'GET', path)
            self.check(path + ': ready route HTTP 200 JSON', r.status_code == 200 and isinstance(self.body(r, path), dict))
        for path in ('/', '/static/app.js', '/static/styles.css'):
            r = self.request(a, path, 'GET', path)
            self.check(path + ': static HTTP 200', r.status_code == 200)
            self.check(path + ': CSP and nosniff', bool(r.headers.get('content-security-policy')) and r.headers.get_list('x-content-type-options') and all(v.strip().lower() == 'nosniff' for v in r.headers.get('x-content-type-options', '').split(',')))
        # GET-only: never invoke a destructive judge reset/import even if accidentally exposed.
        for path in ('/_test/reset', '/_test/import', '/_test/export'):
            r = self.request(a, 'test-control GET probe', 'GET', path)
            self.check('test-control GET unavailable', r.status_code == 404)
        pre, _ = self.session(boundary, 'unconfigured production boundary')
        self.check('production owner setup remains unconfigured', pre.get('setup_required') is True and pre.get('authenticated') is False)
        r = self.request(boundary, 'setup without operator secret blocked', 'POST', '/api/setup', body={'setup_secret':'synthetic-invalid-secret','owner':None}, csrf=pre['csrf_token'])
        self.check('no public setup secret accepted', r.status_code == 403 and self.body(r, 'setup denial').get('error', {}).get('code') == 'setup_denied')
        pre, _ = self.session(boundary, 'setup failure leaves production unchanged')
        self.check('setup failure did not create owner or venue', pre.get('setup_required') is True and pre.get('authenticated') is False)
        sa, sb = self.demo(a, 'visitor A'), self.demo(b, 'visitor B')
        self.check('independent demo account scopes', sa.get('account_scope') != sb.get('account_scope'))
        r = self.request(a, 'unknown API JSON error', 'GET', '/api/definitely-not-a-route')
        self.check('unknown API HTTP 404 with error object', r.status_code == 404 and isinstance(self.body(r, 'API error').get('error'), dict))
        r = self.request(a, 'discover own demo venue', 'GET', '/restaurants')
        self.check('venue discovery HTTP 200', r.status_code == 200)
        venues = self.body(r, 'venues').get('restaurants', [])
        self.check('single synthetic venue', len(venues) == 1)
        rid = venues[0]['id']
        # Deliberately avoid seeded dates/references; choose a future per-run day.
        day = (date.today() + timedelta(days=370 + secrets.randbelow(5000))).isoformat()
        r = self.request(a, 'find synthetic availability', 'GET', f'/availability?restaurant_id={rid}&date={day}&party_size=2')
        self.check('availability HTTP 200', r.status_code == 200)
        slots = self.body(r, 'availability').get('slots', [])
        usable = [s for s in slots if s.get('available_table_ids')]
        self.check('at least two separated available slots', len(usable) >= 4)
        first, last = usable[0], usable[-1]
        self.check('nonoverlapping demo test times',
                   datetime.fromisoformat(last['starts_at_local']) - datetime.fromisoformat(first['starts_at_local']) >= timedelta(hours=2))
        payload = {'restaurant_id': rid, 'table_id': first['available_table_ids'][0],
                   'starts_at_local': first['starts_at_local'], 'party_size': 2}
        # Invalid boundary probes target a mutation only inside our own synthetic namespace.
        for name, csrf, origin in [('invalid CSRF', 'synthetic-invalid-csrf', self.args.origin),
                                   ('invalid Origin', sa['csrf_token'], 'https://invalid.example')]:
            r = self.request(a, name, 'POST', '/reservations', body=payload, csrf=csrf,
                             key='probe-' + secrets.token_hex(16), origin=origin)
            self.check(name + ': blocked', r.status_code == 403)
        key = 'hosted-' + secrets.token_hex(16)
        r = self.request(a, 'create own booking lowercase key', 'POST', '/reservations', body=payload,
                         csrf=sa['csrf_token'], key=key)
        self.check('booking created', r.status_code == 201)
        booking = self.body(r, 'created booking')
        ref = booking['reference']
        r = self.request(a, 'replay exact lowercase key', 'POST', '/reservations', body=payload,
                         csrf=sa['csrf_token'], key=key)
        self.check('original receipt exact replay', r.status_code == 200 and self.body(r, 'replayed booking') == booking)
        for path in (f'/reservations/{ref}', f'/reservations/{ref}/history', f'/reservations/{ref}/decision'):
            r = self.request(b, 'copied reference isolation', 'GET', path)
            self.check('other visitor cannot read created record', r.status_code == 404)
        # Switch only B; A remains guest and its own reservation must survive.
        r = self.request(b, 'B own manager role', 'POST', '/api/demo/role', body={'role':'manager'}, csrf=sb['csrf_token'])
        self.check('B role switch succeeds', r.status_code == 200)
        sb = self.body(r, 'B manager')
        self.check('B role is manager', sb.get('role') == 'manager')
        r = self.request(b, 'B own manager roster', 'GET', f'/api/roster?restaurant_id={rid}&date={day}')
        self.check('B roster excludes A new booking', r.status_code == 200 and not any(x.get('reference') == ref for x in self.body(r, 'B roster').get('reservations', [])))
        current, _ = self.session(a, 'A role unaffected')
        self.check('A remains guest', current.get('role') == 'guest')
        r = self.request(b, 'B reset only own synthetic demo', 'POST', '/api/demo/reset', body={}, csrf=sb['csrf_token'])
        self.check('B own reset succeeds', r.status_code == 200)
        r = self.request(a, 'A survives B reset', 'GET', f'/reservations/{ref}')
        self.check('A booking unchanged by B reset', r.status_code == 200 and self.body(r, 'A after B reset') == booking)
        parallel_body = dict(payload, starts_at_local=last['starts_at_local'], table_id=last['available_table_ids'][0])
        parallel_key = 'parallel-' + secrets.token_hex(16)
        cookies = httpx.Cookies(a.cookies)
        workers = [self.client(cookies=httpx.Cookies(cookies)) for _ in range(4)]
        def send(client):
            return self.request(client, 'four-way same-key request', 'POST', '/reservations', body=parallel_body,
                                csrf=sa['csrf_token'], key=parallel_key)
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(send, workers))
        initial_statuses = [r.status_code for r in responses]
        self.check('four-way only success or bounded contention', all(s in (200,201,503) for s in initial_statuses))
        for i, response in enumerate(responses):
            if response.status_code == 503:
                for attempt in range(5):
                    time.sleep(0.5 * (attempt + 1))
                    response = send(workers[i])  # Identical body, key, identity and session.
                    if response.status_code != 503:
                        break
                responses[i] = response
        statuses = sorted(r.status_code for r in responses)
        self.check('four-way recovered success with at most one create',
                   all(s in (200,201) for s in statuses) and statuses.count(201) <= 1)
        self.check('four-way one create unless initial response was uncertain',
                   statuses.count(201) == 1 or 503 in initial_statuses)
        values = [self.body(r, 'parallel receipt') for r in responses]
        self.check('four-way identical response bodies', all(v == values[0] for v in values))
        r = self.request(a, 'inspect own resulting bookings', 'GET', '/reservations?scope=all&limit=50')
        self.check('result list HTTP 200', r.status_code == 200)
        records = self.body(r, 'booking list').get('reservations', [])
        self.check('exactly two new records on unique test day', sum(x.get('starts_at_local','').startswith(day) for x in records) == 2)
        retained = self.client(cookies=httpx.Cookies(a.cookies))
        r = self.request(retained, 'new HTTP client retained session', 'GET', f'/reservations/{ref}')
        self.check('original booking survives client replacement', r.status_code == 200 and self.body(r, 'retained booking') == booking)
        old = self.client(cookies=httpx.Cookies(a.cookies))
        r = self.request(a, 'logout own demo session', 'POST', '/auth/logout', body={}, csrf=sa['csrf_token'])
        self.check('logout succeeds', r.status_code == 200)
        r = self.request(old, 'revoked cookie booking read', 'GET', f'/reservations/{ref}')
        self.check('revoked session cannot read namespace', r.status_code in (401,404))
        r = self.request(old, 'revoked cookie manager attempt', 'POST', '/api/demo/role', body={'role':'manager'}, csrf=sa['csrf_token'])
        self.check('revoked session cannot switch role', r.status_code in (401,404))

    def execute(self):
        failure = None
        try:
            self.run()
        except GateFailure as exc:
            failure = {'type':'assertion_failure', 'assertion':str(exc)}
        except Exception as exc:
            # Never stringify HTTP exceptions: they may include request/session context.
            failure = {'type':'execution_error', 'exception_class':type(exc).__name__}
        finally:
            for client in self.clients:
                client.close()
        result = {'started_at_utc':self.started, 'finished_at_utc':datetime.now(timezone.utc).isoformat(),
                  'duration_seconds':round(time.monotonic()-self.start,3), 'base_url':self.args.base_url,
                  'request_origin':self.args.origin, 'base_matches_origin':self.args.base_url == self.args.origin,
                  'freeze_sha':self.args.freeze_sha, 'operator_supplied_image_digest':self.args.image_digest,
                  'passed':failure is None, 'failure':failure, 'checks':self.rows,
                  'limitations':['Booking mutations affect only synthetic namespaces owned by this run; authentication preparation and rejection counters can update main metadata. Expiration/cleanup remain operator-managed.',
                    'GET-only judge-control probes: destructive reset/import verbs intentionally not invoked.',
                    'New HTTP client with retained cookie is not a Cloud Run revision restart test.',
                    'No browser/CSP execution, IAM privilege audit, backup/restore or cloud billing/abuse load test.',
                    'When base_matches_origin is false this is direct-backend verification, not proof of Firebase Hosting cookie forwarding.',
                    'Image digest is operator-supplied metadata, not remotely attested by this script.']}
        with Path(self.args.output).open('x') as out:
            json.dump(result,out,indent=2);out.write('\n')
        print('PASS' if failure is None else 'FAIL', 'hosted synthetic checks; evidence saved')
        return 0 if failure is None else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--origin',help='Expected application HTTPS origin; defaults to base-url. Separate for direct Cloud Run pre-Hosting checks.')
    parser.add_argument('--freeze-sha',required=True)
    parser.add_argument('--image-digest')
    parser.add_argument('--output',required=True,help='New evidence JSON path; existing files never overwritten')
    args=parser.parse_args()
    u=urlsplit(args.base_url)
    if u.scheme!='https' or not u.netloc or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:
        parser.error('base-url must be a bare HTTPS origin')
    args.base_url=args.base_url.rstrip('/')
    args.origin=(args.origin or args.base_url).rstrip('/')
    expected=urlsplit(args.origin)
    if expected.scheme!='https' or not expected.netloc or expected.username or expected.password or expected.path or expected.query or expected.fragment:
        parser.error('origin must be a bare HTTPS origin')
    if not re.fullmatch('[0-9a-f]{40}',args.freeze_sha):parser.error('freeze-sha must be a full lowercase commit SHA')
    if args.image_digest and not re.fullmatch(r'(?:[A-Za-z0-9._:/-]+@)?sha256:[0-9a-f]{64}',args.image_digest):
        parser.error('image-digest must be a sha256 digest, optionally prefixed with the image reference')
    if Path(args.output).exists() or not Path(args.output).parent.is_dir():parser.error('output must be a new file in an existing directory')
    return Audit(args).execute()

if __name__=='__main__':sys.exit(main())
