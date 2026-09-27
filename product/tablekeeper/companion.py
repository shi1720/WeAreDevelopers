"""Cookie-bound operational boundary around the inherited domain service."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import hmac
from http.cookies import SimpleCookie
import os
from pathlib import Path
import re
import secrets
import time
from urllib.parse import urlsplit, unquote

from . import auth, reservations, policies, replans
from .state import from_fixture
from .storage import fresh, open_store, StoreError
from .validation import APIError, invalid, calendar_date, canonical

SESSION_SECONDS = 12 * 3600
IDLE_SECONDS = 2 * 3600
ANON_SECONDS = 30 * 60
DEMO_SECONDS = 2 * 3600


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Companion:
    def __init__(self, domain_route, store=None):
        self.mode = os.environ.get('TABLEKEEPER_MODE', 'production')
        if self.mode not in ('production', 'development'):
            raise StoreError('Explicit supported mode required')
        self.origin = os.environ.get('TABLEKEEPER_PUBLIC_ORIGIN', '')
        parsed = urlsplit(self.origin)
        if (not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username
                or parsed.scheme not in ('https', 'http') or (self.mode == 'production' and parsed.scheme != 'https')):
            raise StoreError('Exact public HTTPS origin required; development permits HTTP')
        self.demo_enabled = os.environ.get('TABLEKEEPER_PUBLIC_DEMO') == '1'
        self.setup_secret = os.environ.get('TABLEKEEPER_SETUP_SECRET', '')
        secret_file = os.environ.get('TABLEKEEPER_SETUP_SECRET_FILE')
        if secret_file:
            if Path(secret_file).stat().st_mode & 0o077:
                raise StoreError('Setup secret file must be private (0600)')
            self.setup_secret = Path(secret_file).read_text().strip()
        if self.setup_secret and len(self.setup_secret) < 32:
            raise StoreError('Setup secret must contain at least 32 random characters')
        self.store = store or open_store()
        self.domain_route = domain_route
        try:
            self.store.snapshot('main')
        except APIError as exc:
            if exc.code != 'not_found':
                raise
            self.store.transact('main', lambda value: None, create=True)

    def cookie(self, namespace, token, max_age=SESSION_SECONDS):
        return f'__session={namespace}.{token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}' + ('; Secure' if self.mode == 'production' else '')

    def locator(self, headers):
        try:
            cookies = SimpleCookie()
            cookies.load(headers.get('Cookie', ''))
            raw = cookies['__session'].value
            namespace, token = raw.split('.', 1)
            if not re.fullmatch(r'(main|demo_[0-9a-f]{32})', namespace) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
                return 'main', None
            return namespace, token
        except (KeyError, ValueError):
            return 'main', None

    def prune(self, value, now):
        value['sessions'] = {k: s for k, s in value['sessions'].items()
                             if s['expires_at'] > now and s['last_seen'] + IDLE_SECONDS > now}
        value['attempts'] = {k: v for k, v in value['attempts'].items() if v['until'] > now}

    def new_session(self, value, user, now):
        self.prune(value, now)
        anonymous = sorted(((key, session) for key, session in value['sessions'].items() if session['user_id'] is None),
                           key=lambda item: item[1]['last_seen'])
        if user is None and len(anonymous) >= 128:
            # Anonymous browser preparation cannot consume authenticated capacity.
            value['sessions'].pop(anonymous[0][0])
        elif len(value['sessions']) >= 1024 and anonymous:
            value['sessions'].pop(anonymous[0][0])
        if len(value['sessions']) >= 1024:
            raise APIError(429, 'session_capacity')
        if user is not None:
            owned = sorted(((k, s) for k, s in value['sessions'].items() if s['user_id'] == user), key=lambda item: item[1]['last_seen'])
            for key, _ in owned[:-7]:
                del value['sessions'][key]
        token = secrets.token_urlsafe(32)
        csrf = digest('csrf:' + token)
        expires = now + (SESSION_SECONDS if user else ANON_SECONDS)
        if value['expires_at'] is not None:
            expires = min(expires, value['expires_at'])
        session = {'user_id': user, 'csrf': digest(csrf), 'expires_at': expires, 'last_seen': now}
        value['sessions'][digest(token)] = session
        return token, session

    def get_session(self, value, token, now):
        if value['demo'] and (value['expires_at'] is None or value['expires_at'] <= now):
            raise APIError(401, 'demo_expired', 'This synthetic demo expired. Start a new isolated visit.')
        session = value['sessions'].get(digest(token)) if token else None
        if session is None or session['expires_at'] <= now or session['last_seen'] + IDLE_SECONDS <= now:
            raise APIError(401, 'unauthenticated')
        session['last_seen'] = now
        return session

    def session_body(self, value, namespace, token, session):
        uid = session['user_id']
        user = value['domain']['users'].get(uid)
        if user:
            role = 'manager' if any(uid in r['manager_user_ids'] for r in value['domain']['restaurants']) else 'guest'
            user = {k: user[k] for k in ('display_name', 'email')} | {'user_id': uid, 'role': role}
        scope = digest(namespace + ':' + value.get('scope_generation', 'initial') + ':' + str(uid))
        return {'user': user, 'authenticated': user is not None, 'user_id': uid,
                'display_name': user['display_name'] if user else None, 'role': user['role'] if user else None,
                'email': user['email'] if user else None, 'account_scope': scope,
                'csrf_token': digest('csrf:' + token), 'scope_id': scope,
                'setup_required': not value['setup_consumed'], 'demo_enabled': self.demo_enabled,
                'demo': value['demo'], 'expires_at': session['expires_at']}

    def csrf(self, headers, session):
        token = headers.get('X-CSRF-Token', '')
        if not token or not hmac.compare_digest(digest(token), session['csrf']):
            raise APIError(403, 'csrf_failed')

    def throttle(self, value, label, now, limit):
        key = digest(label)
        self.prune(value, now)
        if key not in value['attempts']:
            if len(value['attempts']) >= 1024:
                raise APIError(429, 'try_later')
            value['attempts'][key] = {'count': 0, 'until': now + 60}
        entry = value['attempts'][key]
        entry['count'] += 1
        if entry['count'] > limit:
            raise APIError(429, 'try_later', 'Please wait a minute before trying again.')

    def credentials(self, body, signup=False):
        for key in ('email', 'password') + (('display_name',) if signup else ()):
            if type(body.get(key)) is not str or not 1 <= len(body[key]) <= (256 if key == 'password' else 200):
                invalid('Invalid ' + key)
        if signup and len(body['password']) < 12:
            invalid('Use a password of at least 12 characters')

    def dispatch(self, method, path, query, headers, body):
        aliases = {'/api/session': '/auth/session', '/api/setup': '/setup',
                   '/api/demo/start': '/demo/start', '/api/demo/role': '/demo/role', '/api/demo/reset': '/demo/reset'}
        path = aliases.get(path, path)
        if path == '/api/roster':
            rid = query.get('restaurant_id', [''])[0]
            if not re.fullmatch('[A-Za-z0-9_-]{1,64}', rid):
                invalid('Invalid restaurant_id')
            path = '/restaurants/' + rid + '/roster'
        if path.startswith('/_test/'):
            raise APIError(404, 'not_found')
        if method == 'GET' and path in ('/health', '/health/live'):
            return 200, {'status': 'alive'}, None
        if method == 'GET' and path == '/health/ready':
            _, value = self.store.snapshot('main')
            if value['maintenance']:
                raise APIError(503, 'maintenance')
            return 200, {'status': 'ready'}, None
        if method not in ('GET', 'POST', 'PATCH'):
            raise APIError(405, 'method_not_allowed')
        if method != 'GET' and headers.get('Origin') != self.origin:
            raise APIError(403, 'origin_rejected')
        namespace, token = self.locator(headers)
        now = time.time()
        if path == '/demo/start' and method == 'POST':
            return self.start_demo(namespace, token, headers, now)

        def execute(value, token=token):
            cookie = None
            try:
                session = self.get_session(value, token, now)
            except APIError:
                if method != 'GET' or path != '/auth/session' or namespace != 'main':
                    raise
                try:
                    self.throttle(value, 'anonymous-sessions', now, 60)
                except APIError as exc:
                    return exc.status, {'error': {'code': exc.code, 'message': exc.message}}, None
                token, session = self.new_session(value, None, now)
                cookie = self.cookie(namespace, token, ANON_SECONDS)
            if method != 'GET':
                self.csrf(headers, session)
            if path == '/auth/session' and method == 'GET':
                return 200, self.session_body(value, namespace, token, session), cookie
            if path in ('/auth/login', '/auth/signup', '/setup') and method == 'POST':
                # Failures commit ONLY bounded abuse counters, never partial domain changes.
                try:
                    self.throttle(value, 'auth-global', now, 60)
                    owner = body.get('owner')
                    label = body.get('email', owner.get('email', 'setup') if type(owner) is dict else 'setup')
                    self.throttle(value, 'auth:' + str(label), now, 8)
                except APIError as exc:
                    return exc.status, {'error': {'code': exc.code, 'message': exc.message}}, None
                candidate = deepcopy(value)
                try:
                    if path == '/setup':
                        self.setup(candidate, body)
                        uid = next(iter(candidate['domain']['users']))
                    else:
                        if not candidate['setup_consumed'] or candidate['demo']:
                            raise APIError(403, 'unavailable')
                        self.credentials(body, path.endswith('signup'))
                        result = (auth.signup if path.endswith('signup') else auth.login)(candidate['domain'], body)
                        uid = result['user_id']
                        candidate['domain']['tokens'].clear()
                    candidate['sessions'].pop(digest(token), None)
                    next_token, next_session = self.new_session(candidate, uid, now)
                    value.clear()
                    value.update(candidate)
                    return (201 if path != '/auth/login' else 200), self.session_body(value, namespace, next_token, next_session), self.cookie(namespace, next_token)
                except APIError as exc:
                    if exc.code == 'email_taken':
                        exc = APIError(400, 'account_unavailable', 'Unable to create this account. Try signing in or contact the venue owner.')
                    return exc.status, {'error': {'code': exc.code, 'message': exc.message}}, None
            uid = session['user_id']
            if path == '/auth/logout' and method == 'POST':
                value['sessions'].pop(digest(token), None)
                return 200, {'logged_out': True}, self.cookie('main', '', 0)
            public_read = method == 'GET' and (path == '/restaurants' or re.fullmatch(r'/restaurants/[^/]+(?:/policies)?', path) or (path == '/availability' and 'exclude_reference' not in query))
            if public_read:
                status, response = self.domain_route(value['domain'], method, path, query, {}, body)
                policy_route = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
                if policy_route:
                    restaurant = reservations.restaurant_for(value['domain'], unquote(policy_route[1]))
                    response['policies'].insert(0, dict(policies.base_terms(restaurant), effective_from='0001-01-01'))
                return status, response, None
            if uid is None:
                raise APIError(401, 'unauthenticated')
            domain = value['domain']
            if method == 'GET' and path == '/availability' and 'exclude_reference' in query:
                from .availability import get_availability
                from .validation import party_size
                reference = query['exclude_reference'][0]
                record = reservations.owned(domain, uid, reference)
                rid = query.get('restaurant_id', [''])[0]
                if record['restaurant_id'] != rid:
                    raise APIError(404, 'not_found')
                day = query.get('date', [''])[0]
                calendar_date(day)
                size = query.get('party_size', [''])[0]
                if not re.fullmatch('[0-9]+', size):
                    invalid('Invalid party_size')
                size = party_size(int(size))
                restaurant = reservations.restaurant_for(domain, rid)
                if 'explain' in query and query['explain'] != ['true']:
                    invalid('explain accepts only true')
                result = get_availability(restaurant, [r for ref, r in domain['reservations'].items() if ref != reference], day, size,
                    policy=policies.select_terms(domain, restaurant, day), explain='explain' in query, closures=domain['closures'])
                return 200, result, None
            if path == '/auth/password' and method == 'POST':
                if value['demo']:
                    raise APIError(403, 'demo_only')
                try:
                    self.throttle(value, 'password:' + uid, now, 8)
                except APIError as exc:
                    return exc.status, {'error': {'code': exc.code, 'message': exc.message}}, None
                self.credentials({'email': domain['users'][uid]['email'], 'password': body.get('new_password'), 'display_name': 'unused'}, True)
                current = body.get('current_password')
                if type(current) is not str or len(current) > 256 or not auth.check_password(current, domain['users'][uid]['password_hash']):
                    return 401, {'error': {'code': 'unauthenticated', 'message': 'Unable to change password with these credentials.'}}, None
                domain['users'][uid]['password_hash'] = auth.hash_password(body['new_password'])
                value['sessions'] = {k: s for k, s in value['sessions'].items() if s['user_id'] != uid}
                next_token, next_session = self.new_session(value, uid, now)
                return 200, self.session_body(value, namespace, next_token, next_session), self.cookie(namespace, next_token)
            if path in ('/demo/role', '/demo/reset') and method == 'POST':
                if not value['demo']:
                    raise APIError(403, 'forbidden')
                if path.endswith('reset'):
                    from .demo import fixture
                    value['domain'] = from_fixture(fixture())
                    value['scope_generation'] = secrets.token_hex(16)
                    value['extra_receipts'] = []
                    value['sessions'] = {}
                    uid = 'demo_guest'
                else:
                    if body.get('role') not in ('guest', 'manager'):
                        invalid('Choose guest or manager')
                    uid = 'demo_' + body['role']
                    value['sessions'].pop(digest(token), None)
                next_token, next_session = self.new_session(value, uid, now)
                return 200, self.session_body(value, namespace, next_token, next_session), self.cookie(namespace, next_token, DEMO_SECONDS)
            if method == 'GET' and path == '/reservations':
                scope = query.get('scope', query.get('view', ['upcoming']))[0]
                if scope not in ('upcoming', 'past', 'all'):
                    invalid('Invalid booking scope')
                records = [r for r in domain['reservations'].values() if r['user_id'] == uid]
                if scope != 'all':
                    records = [r for r in records if (datetime.fromisoformat(r['ends_at']).timestamp() >= now and r['status'] == 'confirmed') == (scope == 'upcoming')]
                records.sort(key=lambda r: (r['starts_at'], r['reference']), reverse=scope == 'past')
                return 200, self.page([reservations.public(r) for r in records], query), None
            roster = re.fullmatch(r'/restaurants/([^/]+)/roster', path)
            if roster and method == 'GET':
                rid = unquote(roster[1])
                replans.manager(domain, uid, rid)
                day = query.get('date', [''])[0]
                calendar_date(day)
                records = [r for r in domain['reservations'].values() if r['restaurant_id'] == rid and r['starts_at_local'][:10] == day and r['status'] == 'confirmed']
                records.sort(key=lambda r: (r['starts_at'], r['reference']))
                rows = [{k: deepcopy(r[k]) for k in ('reference', 'starts_at_local', 'starts_at', 'ends_at', 'party_size', 'table_ids', 'status')} | {'display_name': domain['users'][r['user_id']]['display_name']} for r in records]
                return 200, self.page(rows, query, 50), None
            individual = re.fullmatch(r'/reservations/([^/]+)(/cancel)?', path)
            if individual and ((method == 'PATCH' and not individual[2]) or (method == 'POST' and individual[2])):
                key = headers.get('Idempotency-Key')
                if not key:
                    raise APIError(400, 'missing_idempotency_key')
                if len(key) > 255:
                    invalid('Idempotency key exceeds 255 characters')
                receipt = next((r for r in value['extra_receipts'] if (r['user_id'], r['method'], r['path'], r['key']) == (uid, method, path, key)), None)
                if receipt:
                    if canonical(receipt['body']) != canonical(body):
                        raise APIError(409, 'idempotency_key_reuse')
                    return 200, deepcopy(receipt['response']), None
                reference = unquote(individual[1])
                if method == 'PATCH' and 'expected_revision' not in body:
                    invalid('expected_revision is required')
                result = reservations.amend(domain, uid, reference, body) if method == 'PATCH' else reservations.cancel(domain, uid, reference)
                value['extra_receipts'].append({'user_id': uid, 'method': method, 'path': path, 'key': key, 'body': deepcopy(body), 'response': deepcopy(result)})
                return 200, result, None
            # Internal compatibility token exists only in the private callback.
            domain['tokens']['internal'] = uid
            try:
                status, response = self.domain_route(domain, method, path, query,
                    {'Authorization': 'Bearer internal', 'Idempotency-Key': headers.get('Idempotency-Key')}, body)
            finally:
                domain['tokens'].clear()
            return status, response, None

        try:
            return self.store.transact(namespace, execute)
        except APIError as exc:
            if namespace != 'main' and method == 'GET' and path == '/auth/session' and exc.code in ('unauthenticated', 'demo_expired', 'not_found'):
                # Expired demo credentials cannot access their namespace. Issue
                # a fresh anonymous main session so the visitor can start again.
                return self.dispatch(method, path, query, dict(headers) | {'Cookie': ''}, body)
            raise

    def page(self, records, query, default=20):
        try:
            cursor = int(query.get('cursor', query.get('offset', ['0']))[0])
            limit = int(query.get('limit', [str(default)])[0])
        except ValueError:
            invalid('Invalid pagination')
        if cursor < 0 or not 1 <= limit <= 50:
            invalid('Invalid pagination')
        end = cursor + limit
        return {'reservations': records[cursor:end], 'next_cursor': str(end) if end < len(records) else None,
                'next_offset': end if end < len(records) else None, 'total': len(records)}

    def setup(self, value, body):
        if value['setup_consumed'] or value['demo']:
            raise APIError(409, 'already_configured')
        supplied = body.get('setup_secret', '')
        if not self.setup_secret or type(supplied) is not str or not hmac.compare_digest(supplied, self.setup_secret):
            raise APIError(403, 'setup_denied')
        owner = body.get('owner')
        restaurant = deepcopy(body.get('restaurant'))
        if type(owner) is not dict or type(restaurant) is not dict:
            invalid('Owner and restaurant are required')
        self.credentials(owner, True)
        restaurant['id'] = 'venue'
        restaurant['manager_user_ids'] = ['owner']
        if not 1 <= len(restaurant.get('tables', [])) <= 6 or len(restaurant.get('combinable', [])) > 4:
            invalid('The pilot supports 1-6 tables and at most 4 declared pairs; closure plans consider at most 6 overlapping bookings.')
        if not isinstance(restaurant.get('name'), str) or not 1 <= len(restaurant['name']) <= 100:
            invalid('Invalid venue name')
        # Reuse the bounded policy contract for initial operational settings.
        policies.validate_policy(restaurant, dict(restaurant, effective_from='2000-01-01', capacities={t['id']: t['capacity'] for t in restaurant['tables']}))
        value['domain'] = from_fixture({'users': [dict(owner, id='owner')], 'restaurants': [restaurant], 'reservations': []})
        value['setup_consumed'] = True

    def start_demo(self, namespace, token, headers, now):
        if not self.demo_enabled:
            raise APIError(404, 'not_found')
        def authorize(value):
            session = self.get_session(value, token, now)
            self.csrf(headers, session)
        self.store.transact(namespace, authorize)
        demo_id = 'demo_' + secrets.token_hex(16)
        def reserve(value):
            self.throttle(value, 'demo-create', now, 10)
            if len(value['registry']) >= 100:
                raise APIError(429, 'demo_capacity', 'Demo capacity is temporarily full. Please try later.')
            value['registry'][demo_id] = now + DEMO_SECONDS
        self.store.transact('main', reserve)
        def seed(value):
            from .demo import fixture
            value.update(domain=from_fixture(fixture()), setup_consumed=True, demo=True, expires_at=now + DEMO_SECONDS)
            next_token, session = self.new_session(value, 'demo_guest', now)
            return 201, self.session_body(value, demo_id, next_token, session), self.cookie(demo_id, next_token, DEMO_SECONDS)
        return self.store.transact(demo_id, seed, create=True)
