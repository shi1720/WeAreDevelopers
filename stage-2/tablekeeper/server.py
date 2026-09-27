"""Threaded HTTP adapter with one linearizable state boundary."""
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import mimetypes
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit
from . import auth, reservations
from .availability import get_availability
from .state import Store, from_fixture, import_envelope
from .validation import APIError, calendar_date, invalid, object_body, party_size


class Application:
    def __init__(self):
        self.store = Store()
        if os.environ.get('TABLEKEEPER_DEMO', '1') != '0':
            from .demo import fixture
            self.store.data = from_fixture(fixture())

    def dispatch(self, method, path, query, headers, body):
        with self.store.lock:
            if method == 'GET' and path == '/health':
                return 200, {'status': 'ok'}
            if path.startswith('/_test/'):
                if os.environ.get('TABLEKEEPER_TEST_CONTROLS', '1') == '0':
                    raise APIError(404, 'not_found')
                if method == 'POST' and path == '/_test/reset':
                    self.store.data = from_fixture(body)
                    return 204, None
                if method == 'GET' and path == '/_test/export':
                    return 200, self.store.export()
                if method == 'POST' and path == '/_test/import':
                    self.store.data = import_envelope(body)
                    return 204, None
                raise APIError(404, 'not_found')
            # Mutations use an isolated candidate state. Only a successful response
            # publishes it, so errors cannot leak records, counters or retry claims.
            state = deepcopy(self.store.data) if method != 'GET' else self.store.data
            result = self.route(state, method, path, query, headers, body)
            if method != 'GET':
                self.store.data = state
            return result

    def route(self, state, method, path, query, headers, body):
        if method == 'POST' and path == '/auth/signup':
            return 201, auth.signup(state, body)
        if method == 'POST' and path == '/auth/login':
            return 200, auth.login(state, body)
        if method == 'GET' and path == '/restaurants':
            return 200, {'restaurants': [{k: r[k] for k in ('id', 'name', 'timezone')} for r in state['restaurants']]}
        match = re.fullmatch(r'/restaurants/([^/]+)', path)
        if method == 'GET' and match:
            return 200, deepcopy(reservations.restaurant_for(state, unquote(match[1])))
        if method == 'GET' and path == '/availability':
            for key in ('restaurant_id', 'date', 'party_size'):
                if key not in query:
                    invalid('Missing ' + key)
            rid, day, size = (query[k][0] for k in ('restaurant_id', 'date', 'party_size'))
            if not rid or len(rid) > 64:
                invalid('Invalid restaurant_id')
            calendar_date(day)
            if not re.fullmatch('[0-9]+', size):
                invalid('Party size must use decimal digits')
            try:
                size = party_size(int(size))
            except ValueError:
                invalid('Invalid party size')
            restaurant = reservations.restaurant_for(state, rid)
            return 200, get_availability(restaurant, list(state['reservations'].values()), day, size)
        user = auth.authenticate(state, headers.get('Authorization'))
        if method == 'GET' and path == '/reservations':
            records = [r for r in state['reservations'].values() if r['user_id'] == user]
            records.sort(key=lambda r: datetime.fromisoformat(r['starts_at']).astimezone(timezone.utc), reverse=True)
            return 200, {'reservations': [reservations.public(r) for r in records]}
        if method == 'POST' and path in ('/reservations', '/reservation-moves'):
            operation = reservations.create if path == '/reservations' else reservations.moves
            return reservations.idempotent(state, user, method, path, headers.get('Idempotency-Key'), body,
                                           lambda: operation(state, user, body))
        match = re.fullmatch(r'/reservations/([^/]+)(/cancel)?', path)
        if match:
            reference = unquote(match[1])
            if method == 'GET' and not match[2]:
                return 200, reservations.public(reservations.owned(state, user, reference))
            if method == 'PATCH' and not match[2]:
                return 200, reservations.amend(state, user, reference, body)
            if method == 'POST' and match[2]:
                return 200, reservations.cancel(state, user, reference)
        raise APIError(404, 'not_found')


class Handler(BaseHTTPRequestHandler):
    application = Application()

    def log_message(self, *_):
        # Requests may contain private references; do not write access logs.
        pass

    def handle_request(self):
        try:
            parts = urlsplit(self.path)
            if self.command == 'GET' and (parts.path in ('/', '/signup', '/login', '/lookup') or parts.path.startswith('/static/')):
                root = Path(__file__).resolve().parent.parent / 'static'
                relative = 'index.html' if parts.path in ('/', '/signup', '/login', '/lookup') else unquote(parts.path[len('/static/'):])
                target = (root / relative).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    raise APIError(404, 'not_found')
                content = target.read_bytes()
                self.send_response(200)
                kind = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
                self.send_header('Content-Type', kind + ('; charset=utf-8' if kind.startswith('text/') or kind in ('application/javascript',) else ''))
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                self.wfile.write(content)
                return
            body = None
            if self.command in ('POST', 'PATCH', 'PUT'):
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise APIError(400, 'malformed_request') from None
                if length < 0:
                    raise APIError(400, 'malformed_request')
                raw = self.rfile.read(length)
                # Cancellation permits an empty body; other writes require objects.
                body = {} if not raw and parts.path.endswith('/cancel') else object_body(raw)
            status, response = self.application.dispatch(self.command, parts.path,
                parse_qs(parts.query, keep_blank_values=True), self.headers, body)
        except APIError as error:
            status, response = error.status, {'error': {'code': error.code, 'message': error.message}}
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            status, response = 400, {'error': {'code': 'malformed_request', 'message': 'Invalid request'}}
        encoded = b'' if response is None else json.dumps(response, ensure_ascii=True, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = handle_request


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128


def main():
    Server(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()


if __name__ == '__main__':
    main()
