"""Synthetic real-browser companion checks. Run with prepared Python 3.12.

These tests use public setup/auth APIs, never judge-reset routes. Screenshots
contain only synthetic data. Lost-response checks restart the real service.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT.parent / 'evidence/product/experience'
SECRET = 'synthetic-setup-secret-for-browser-tests-only-123456'
PASSWORD = 'synthetic evening password'


class ExperienceBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()
        EVIDENCE.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='tablekeeper-experience-')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.base = f'http://127.0.0.1:{self.port}'
        self.env = dict(os.environ, PORT=str(self.port), TABLEKEEPER_MODE='development',
                        TABLEKEEPER_PUBLIC_ORIGIN=self.base, TABLEKEEPER_PUBLIC_DEMO='1',
                        TABLEKEEPER_SETUP_SECRET=SECRET, TABLEKEEPER_STORAGE='sqlite',
                        TABLEKEEPER_DB=str(Path(self.directory.name) / 'store.sqlite3'))
        self.start()
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000})
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.errors = []
        self.csp_errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda message: self.csp_errors.append(message.text)
                     if 'content security policy' in message.text.lower() else None)

    def start(self):
        self.process = subprocess.Popen([sys.executable, '-m', 'tablekeeper.server'], cwd=ROOT,
                                        env=self.env, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                urllib.request.urlopen(self.base + '/health/ready', timeout=.5).close()
                return
            except OSError:
                if self.process.poll() is not None:
                    raise RuntimeError(self.process.stderr.read().decode())
                time.sleep(.05)
        raise RuntimeError('Service readiness timed out')

    def stop(self):
        self.process.terminate()
        self.process.wait(timeout=10)
        self.process.stderr.close()

    def tearDown(self):
        try:
            self.context.close()
        finally:
            self.stop()
            self.directory.cleanup()
        self.assertEqual([], self.errors)
        self.assertEqual([], self.csp_errors)

    def screenshot(self, name, width=1440):
        self.page.set_viewport_size({'width': width, 'height': 1000 if width > 375 else 900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
        self.page.screenshot(path=str(EVIDENCE / f'{name}-{width}.png'), full_page=True)

    def setup_venue(self):
        self.page.goto(self.base + '/setup')
        self.page.locator('#setup-secret').fill(SECRET)
        self.page.locator('#setup-name').fill('Synthetic Owner')
        self.page.locator('#setup-email').fill('owner@experience.test')
        self.page.locator('#setup-password').fill(PASSWORD)
        self.page.locator('#venue-name').fill('The Synthetic Orangery')
        # Never capture a filled secret or password, including masked screenshots.
        self.page.get_by_test_id('setup-submit').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.page.get_by_test_id('manager-restaurant').wait_for()

    def login(self, email='owner@experience.test'):
        self.page.goto(self.base + '/login')
        self.page.get_by_test_id('login-email').fill(email)
        self.page.get_by_test_id('login-password').fill(PASSWORD)
        self.page.get_by_test_id('login-submit').click()
        self.page.get_by_test_id('current-user').wait_for()

    def search(self, date='2035-06-14', party=2):
        self.page.goto(self.base + '/')
        self.page.get_by_test_id('restaurant-select').locator('option').first.wait_for(state='attached')
        self.page.wait_for_function("document.querySelector('#restaurant')?.value !== ''")
        self.page.get_by_test_id('date-input').fill(date)
        self.page.get_by_test_id('party-size-input').fill(str(party))
        self.page.get_by_test_id('search-button').click()
        self.page.get_by_test_id('availability-grid').wait_for()

    def book(self, slot='slot-table_1-18:00'):
        self.search()
        self.page.get_by_test_id(slot).click()
        self.page.get_by_test_id('booking-submit').click()
        return self.page.get_by_test_id('confirmation-reference').inner_text()

    def test_setup_booking_edit_roster_and_mobile(self):
        self.page.goto(self.base + '/setup')
        self.page.get_by_test_id('setup-submit').wait_for()
        self.screenshot('setup', 1440)
        self.screenshot('setup', 375)
        self.page.set_viewport_size({'width': 1440, 'height': 1000})
        self.setup_venue()
        cookies = self.context.cookies()
        self.assertTrue(any(c['name'] == '__session' and c['httpOnly'] for c in cookies))
        self.assertEqual([], self.page.evaluate("Object.keys(localStorage).filter(k=>k==='tablekeeper.session')"))
        reference = self.book()
        self.page.goto(self.base + '/bookings')
        self.page.get_by_test_id('booking-list-item').wait_for()
        self.assertIn(reference, self.page.locator('#bookings-list').inner_text())
        self.screenshot('bookings', 1440)
        self.screenshot('bookings', 375)
        self.page.get_by_role('link', name=f'View or edit {reference}').click()
        self.page.get_by_test_id('edit-search').click()
        self.page.get_by_test_id('edit-choice').select_option(label='19:30 · Garden table')
        self.page.get_by_test_id('edit-terms').wait_for()
        self.screenshot('edit-review', 375)
        self.page.get_by_test_id('edit-confirm').focus()
        self.page.keyboard.press('Enter')
        self.page.get_by_test_id('edit-success').wait_for()
        self.assertIn('19:30', self.page.get_by_test_id('reservation-detail').inner_text())
        self.page.goto(self.base + '/manager')
        self.page.locator('#roster-date').fill('2035-06-14')
        self.page.get_by_test_id('roster-load').click()
        self.page.get_by_test_id('roster-row').wait_for()
        self.assertIn(reference, self.page.locator('.roster-results').inner_text())
        self.screenshot('manager-roster', 1440)
        self.screenshot('manager-roster', 375)

    def test_lost_booking_response_reload_restart_and_account_isolation(self):
        self.setup_venue()
        self.search()
        self.page.get_by_test_id('slot-table_1-18:00').click()
        requests, receipts = [], []

        def lose(route):
            requests.append((route.request.post_data, route.request.headers.get('idempotency-key')))
            response = route.fetch()
            receipts.append({'status': response.status, 'body': response.json()})
            route.abort('connectionreset')

        self.page.route('**/reservations', lose)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-uncertain').wait_for()
        self.assertEqual(201, receipts[0]['status'], receipts[0]['body'])
        saved = self.page.evaluate('Object.values(localStorage).map(v=>JSON.parse(v))')
        self.assertEqual(1, len(saved))
        self.assertEqual(requests[0][1], saved[0]['key'])
        self.assertNotIn(PASSWORD, json.dumps(saved))
        self.page.unroute('**/reservations', lose)
        csrf = self.page.evaluate('sessionInfo.csrf_token')
        self.page.evaluate("sessionInfo.csrf_token='deliberately-invalid-test-token'")
        self.page.get_by_test_id('recover-request').click()
        self.page.get_by_test_id('recovery-error').wait_for()
        self.assertEqual(saved, self.page.evaluate('Object.values(localStorage).map(v=>JSON.parse(v))'))
        revoked = self.context.request.post(self.base + '/auth/logout', data={},
                    headers={'Origin': self.base, 'X-CSRF-Token': csrf})
        self.assertEqual(200, revoked.status)
        self.page.get_by_test_id('recover-request').click()
        self.page.get_by_role('link', name='Sign in again to recover this request').wait_for()
        self.assertEqual(saved, self.page.evaluate('Object.values(localStorage).map(v=>JSON.parse(v))'))
        self.login()
        self.page.get_by_test_id('logout-button').click()
        self.page.goto(self.base + '/signup')
        self.page.get_by_test_id('signup-display-name').fill('Another Synthetic Guest')
        self.page.get_by_test_id('signup-email').fill('another@experience.test')
        self.page.get_by_test_id('signup-password').fill(PASSWORD)
        self.page.get_by_test_id('signup-submit').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.assertEqual(0, self.page.get_by_test_id('recover-request').count())
        self.page.get_by_test_id('logout-button').click()
        self.login()
        self.page.get_by_test_id('recover-request').wait_for()
        self.stop()
        self.start()
        self.page.reload()
        self.page.get_by_test_id('recover-request').wait_for()
        self.screenshot('restart-recovery', 375)

        def replay(route):
            requests.append((route.request.post_data, route.request.headers.get('idempotency-key')))
            route.continue_()

        self.page.route('**/reservations', replay)
        self.page.get_by_test_id('recover-request').click()
        self.page.get_by_text('Original result recovered.', exact=True).wait_for()
        self.assertEqual(requests[0], requests[1])
        self.assertIn(receipts[0]['body']['reference'], self.page.locator('#pending-recovery').inner_text())
        self.page.goto(self.base + '/bookings')
        self.page.get_by_test_id('booking-list-item').wait_for()
        self.assertEqual(1, self.page.get_by_test_id('booking-list-item').count())

    def test_demo_closure_series_updated_summary(self):
        self.page.goto(self.base + '/demo')
        self.page.locator('#start-demo').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.page.goto(self.base + '/lookup?reference=EVENING1')
        self.page.get_by_test_id('reservation-detail').wait_for()
        self.page.get_by_test_id('series-count').fill('2')
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_test_id('series-created').get_by_role('link').click()
        self.page.get_by_test_id('series-local-time').fill('18:00')
        self.page.get_by_test_id('series-amend-submit').click()
        self.page.get_by_test_id('series-amend-success').wait_for()
        self.assertEqual(2, self.page.locator('.occurrences h3').filter(has_text='18:00').count())
        self.screenshot('regular-updated', 1440)
        self.screenshot('regular-updated', 375)
        self.page.goto(self.base + '/demo')
        self.page.locator('[data-demo="manager"]').click()
        self.page.get_by_test_id('closure-preview').wait_for()
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        self.screenshot('closure-preview', 1440)
        self.screenshot('closure-preview', 375)
        self.page.get_by_test_id('replan-apply').click()
        self.page.get_by_test_id('replan-success').wait_for()

    def test_demo_reset_isolates_saved_pending_request(self):
        self.page.goto(self.base + '/demo')
        self.page.locator('#start-demo').click()
        self.page.get_by_test_id('current-user').wait_for()
        original_scope = self.page.evaluate('session.account_scope')
        self.search(date='2035-07-15')
        self.page.get_by_test_id('slot-window-17:00').click()
        results = []

        def lose(route):
            response = route.fetch()
            results.append(response.status)
            route.abort('connectionreset')

        self.page.route('**/reservations', lose)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-uncertain').wait_for()
        self.assertEqual([201], results)
        self.page.unroute('**/reservations', lose)
        self.page.goto(self.base + '/demo')
        self.page.locator('#reset-demo').click()
        self.page.locator('#confirm-reset').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.assertNotEqual(original_scope, self.page.evaluate('session.account_scope'))
        self.assertEqual(0, self.page.get_by_test_id('recover-request').count())
        self.assertTrue(self.page.evaluate('(scope)=>localStorage.getItem(`tablekeeper.pending.v1.${scope}`)!==null', original_scope))

    def test_material_amendment_and_repair_recover_after_restart(self):
        self.page.goto(self.base + '/demo')
        self.page.locator('#start-demo').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.page.goto(self.base + '/lookup?reference=EVENING1')
        self.page.get_by_test_id('series-count').fill('2')
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_test_id('series-created').get_by_role('link').click()

        def recover_lost(pattern, submit, uncertain):
            attempts, results = [], []

            def lose(route):
                attempts.append((route.request.post_data, route.request.headers.get('idempotency-key')))
                response = route.fetch()
                results.append({'status': response.status, 'body': response.json()})
                route.abort('connectionreset')

            self.page.route(pattern, lose)
            submit.click()
            self.page.get_by_test_id(uncertain).wait_for()
            self.assertEqual(200, results[0]['status'], results[0]['body'])
            self.page.unroute(pattern, lose)
            self.stop()
            self.start()
            self.page.reload()
            self.page.get_by_test_id('recover-request').wait_for()

            def replay(route):
                attempts.append((route.request.post_data, route.request.headers.get('idempotency-key')))
                route.continue_()

            self.page.route(pattern, replay)
            self.page.get_by_test_id('recover-request').click()
            self.page.get_by_text('Original result recovered.', exact=True).wait_for()
            self.assertEqual(attempts[0], attempts[1])
            self.page.unroute(pattern, replay)

        self.page.get_by_test_id('series-local-time').fill('18:00')
        recover_lost('**/series/*/amend', self.page.get_by_test_id('series-amend-submit'), 'series-amend-uncertain')
        self.assertEqual(2, self.page.locator('.occurrences h3').filter(has_text='18:00').count())
        self.page.goto(self.base + '/demo')
        self.page.locator('[data-demo="manager"]').click()
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        recover_lost('**/replans/*/apply', self.page.get_by_test_id('replan-apply'), 'replan-uncertain')


if __name__ == '__main__':
    unittest.main(verbosity=2)
