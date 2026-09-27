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
from . import auth, reservations, policies, series, replans
from .availability import get_availability
from .state import Store, from_fixture, import_envelope
from .validation import APIError, calendar_date, invalid, object_body, party_size
from .companion import Companion
from .storage import StoreError
import signal
import socket
import threading


class Application:
    def __init__(self):
        self.companion = Companion(self.route)
        self.store = self.companion.store

    def dispatch(self, method, path, query, headers, body):
        return self.companion.dispatch(method, path, query, headers, body)

    def route(self, state, method, path, query, headers, body):
        if method == 'POST' and path == '/auth/signup':
            return 201, auth.signup(state, body)
        if method == 'POST' and path == '/auth/login':
            return 200, auth.login(state, body)
        if method == 'GET' and path == '/restaurants':
            return 200, {'restaurants': [{k: r[k] for k in ('id', 'name', 'timezone')} for r in state['restaurants']]}
        policy_route = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
        if method == 'GET' and policy_route:
            restaurant = reservations.restaurant_for(state, unquote(policy_route[1]))
            return 200, {'policies': deepcopy(state['policies'][restaurant['id']])}
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
            if 'explain' in query and query['explain'] != ['true']:
                invalid('explain accepts only true')
            return 200, get_availability(restaurant, list(state['reservations'].values()), day, size,
                                        policy=policies.select_terms(state, restaurant, day), explain='explain' in query, closures=state['closures'])
        private_detail = re.fullmatch(r'/reservations/([^/]+)/(history|decision)', path)
        series_detail = re.fullmatch(r'/series/([^/]+)', path)
        if method == 'GET' and (private_detail or series_detail):
            try:
                user = auth.authenticate(state, headers.get('Authorization'))
            except APIError:
                raise APIError(404, 'not_found') from None
            if series_detail:
                return 200, series.response(state, series.owned(state, user, unquote(series_detail[1])))
            record = reservations.owned(state, user, unquote(private_detail[1]))
            if private_detail[2] == 'history':
                return 200, {'reference': record['reference'], 'entries': deepcopy(state['histories'][record['reference']])}
            return 200, {k: deepcopy(record[k]) for k in ('reference', 'revision', 'accepted_terms')}
        user = auth.authenticate(state, headers.get('Authorization'))
        preview_route = re.fullmatch(r'/restaurants/([^/]+)/replans', path)
        apply_route = re.fullmatch(r'/restaurants/([^/]+)/replans/([^/]+)/apply', path)
        detail_route = re.fullmatch(r'/api/restaurants/([^/]+)/replans/([^/]+)', path)
        amend_route = re.fullmatch(r'/series/([^/]+)/amend', path)
        if method == 'GET' and detail_route:
            return 200, replans.detail(state, user, unquote(detail_route[1]), unquote(detail_route[2]))
        if method == 'POST' and (preview_route or apply_route or amend_route):
            def operation():
                if preview_route:
                    return replans.preview(state, user, unquote(preview_route[1]), body)
                if apply_route:
                    return replans.apply(state, user, unquote(apply_route[1]), unquote(apply_route[2]))
                return series.amend(state, user, unquote(amend_route[1]), body)
            return reservations.idempotent(state, user, method, path, headers.get('Idempotency-Key'), body, operation)
        if method == 'GET' and path == '/api/series':
            return 200, {'series': [series.response(state, agreement) for agreement in state['series'].values()
                                    if agreement['user_id'] == user]}
        if method == 'POST' and policy_route:
            return reservations.idempotent(state, user, method, path, headers.get('Idempotency-Key'), body,
                lambda: policies.publish(state, user, reservations.restaurant_for(state, unquote(policy_route[1])), body))
        if method == 'POST' and path == '/series':
            return reservations.idempotent(state, user, method, path, headers.get('Idempotency-Key'), body,
                lambda: series.adopt(state, user, body))
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
    application = None

    def setup(self):
        super().setup()
        self.connection.settimeout(5)
        self.deadline = threading.Timer(15, self.expire_connection)
        self.deadline.daemon = True
        self.deadline.start()

    def expire_connection(self):
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def finish(self):
        self.deadline.cancel()
        super().finish()

    def parse_request(self):
        if not super().parse_request():
            return False
        if len(self.path) > 4096 or sum(len(k) + len(v) for k, v in self.headers.items()) > 16384:
            self.send_error(431, 'Request headers too large')
            return False
        return True

    def end_headers(self):
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if self.application.companion.mode == 'production':
            self.send_header('Strict-Transport-Security', 'max-age=31536000')
        super().end_headers()

    def log_message(self, *_):
        # Requests may contain private references; do not write access logs.
        pass

    def handle_request(self):
        cookie = None
        try:
            parts = urlsplit(self.path)
            if self.command == 'GET' and (parts.path in ('/', '/signup', '/login', '/lookup', '/manager', '/series', '/setup', '/bookings', '/account', '/demo') or parts.path.startswith('/static/')):
                root = Path(__file__).resolve().parent.parent / 'static'
                relative = 'index.html' if not parts.path.startswith('/static/') else unquote(parts.path[len('/static/'):])
                target = (root / relative).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    raise APIError(404, 'not_found')
                content = target.read_bytes()
                self.send_response(200)
                kind = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
                self.send_header('Content-Type', kind + ('; charset=utf-8' if kind.startswith('text/') or kind in ('application/javascript',) else ''))
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            body = None
            if self.command in ('POST', 'PATCH', 'PUT'):
                if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) > 1:
                    raise APIError(400, 'malformed_request')
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise APIError(400, 'malformed_request') from None
                if not 0 <= length <= 65536:
                    raise APIError(413, 'request_too_large')
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise APIError(400, 'malformed_request')
                # Cancellation permits an empty body; other writes require objects.
                body = {} if not raw else object_body(raw)
            status, response, cookie = self.application.dispatch(self.command, parts.path,
                parse_qs(parts.query, keep_blank_values=True), self.headers, body)
        except APIError as error:
            status, response = error.status, {'error': {'code': error.code, 'message': error.message}}
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            status, response = 400, {'error': {'code': 'malformed_request', 'message': 'Invalid request'}}
        except (StoreError, OSError):
            status, response = 503, {'error': {'code': 'store_unavailable', 'message': 'Durable storage is unavailable. Retry the unchanged request to recover its outcome.'}}
        encoded = b'' if response is None else json.dumps(response, ensure_ascii=True, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = handle_request


class Server(ThreadingHTTPServer):
    daemon_threads = False
    request_queue_size = 32
    slots = threading.BoundedSemaphore(32)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


def main():
    Handler.application = Application()
    server = Server((os.environ.get('TABLEKEEPER_BIND', '0.0.0.0'), int(os.environ.get('PORT', '8080'))), Handler)
    def shutdown(*_):
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        Handler.application.store.close()


if __name__ == '__main__':
    main()
