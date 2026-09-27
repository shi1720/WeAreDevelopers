"""Spec-derived browser checks. Run explicitly with the prepared Playwright Python.

Coverage: screen URLs and auth; singles/pairs; replay; conflict refresh; uncertain
retry through import; out-of-order search; lookup/cancel; 375px layout and labels.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        cls.base = f'http://127.0.0.1:{cls.port}'
        cls.process = subprocess.Popen([sys.executable, '-m', 'tablekeeper.server'], cwd=ROOT,
                                       env=dict(os.environ, PORT=str(cls.port)), stdout=subprocess.DEVNULL)
        for _ in range(100):
            try:
                urllib.request.urlopen(cls.base + '/health', timeout=1).close()
                break
            except OSError:
                time.sleep(.05)
        else:
            raise RuntimeError('Service did not start')
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.process.terminate()
        cls.process.wait(timeout=5)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000})
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        fixture = {'users': [{'id': 'u', 'email': 'guest@example.test', 'password': 'test evening', 'display_name': 'Robin'}],
                   'restaurants': [], 'reservations': []}
        for rid, name in [('r', 'The Test Garden'), ('other', 'The Second Room')]:
            fixture['restaurants'].append({'id': rid, 'name': name, 'timezone': 'Europe/Berlin',
                'manager_user_ids': ['u'] if rid == 'r' else [],
                'slot_minutes': 30, 'reservation_duration_minutes': 90, 'cancellation_cutoff_minutes': 60,
                'opening_hours': [{'weekday': d, 'opens': '18:00', 'closes': '23:00'}
                                  for d in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')],
                'tables': [{'id': 'a', 'label': name + ' Window', 'capacity': 2},
                           {'id': 'b', 'label': name + ' Garden', 'capacity': 2},
                           {'id': 'c', 'label': name + ' Alcove', 'capacity': 6}],
                'combinable': [['b', 'a']]})
        self.assertEqual(204, self.context.request.post(self.base + '/_test/reset', data=fixture).status)

    def tearDown(self):
        self.assertEqual([], self.errors)
        self.context.close()

    def login(self):
        self.page.goto(self.base + '/login')
        self.page.get_by_test_id('login-email').fill('guest@example.test')
        self.page.get_by_test_id('login-password').fill('test evening')
        self.page.get_by_test_id('login-submit').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.assertIn('Robin', self.page.get_by_test_id('current-user').inner_text())

    def search(self, party=2):
        self.page.get_by_test_id('restaurant-select').select_option('r')
        self.page.get_by_test_id('date-input').fill('2035-06-14')
        self.page.get_by_test_id('party-size-input').fill(str(party))
        self.page.get_by_test_id('search-button').click()
        self.page.get_by_test_id('availability-grid').wait_for()

    def test_pair_confirmation_replay_lookup_cancel_mobile(self):
        self.login()
        self.search(4)
        self.assertEqual('false', self.page.get_by_test_id('slot-a-18:00').get_attribute('data-available'))
        self.page.get_by_test_id('slot-b+a-18:00').click()
        self.assertIn('Garden', self.page.get_by_test_id('booking-summary').inner_text())
        self.assertIn('Window', self.page.get_by_test_id('booking-summary').inner_text())
        self.page.get_by_test_id('booking-submit').click()
        reference = self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.get_by_test_id('booking-party-size').fill('4')
        self.page.get_by_test_id('booking-submit').click()
        self.page.wait_for_function('(ref) => document.querySelector("[data-testid=confirmation-reference]")?.textContent === ref', arg=reference)
        self.assertEqual(0, self.page.get_by_test_id('booking-error').count())
        self.page.set_viewport_size({'width': 375, 'height': 900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 375)
        self.page.goto(self.base + '/lookup')
        self.page.get_by_test_id('lookup-reference-input').fill(reference)
        self.page.get_by_test_id('lookup-submit').click()
        self.assertEqual('confirmed', self.page.get_by_test_id('reservation-status').inner_text())
        self.assertIn('Garden', self.page.get_by_test_id('reservation-tables').inner_text())
        self.page.get_by_test_id('reservation-cancel-button').click()
        self.page.wait_for_function('document.querySelector("[data-testid=reservation-status]")?.textContent === "cancelled"')
        self.assertEqual(0, self.page.get_by_test_id('reservation-cancel-button').count())
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 375)

    def test_lost_response_exact_retry_survives_import(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        requests = []
        def lose(route):
            requests.append((route.request.post_data, route.request.headers.get('idempotency-key')))
            response = route.fetch()
            self.assertEqual(201, response.status)
            route.abort('connectionreset')
        self.page.route('**/reservations', lose, times=1)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-uncertain').wait_for()
        self.assertEqual(0, self.page.get_by_test_id('booking-error').count())
        self.assertEqual(0, self.page.get_by_test_id('confirmation').count())
        snapshot = self.context.request.get(self.base + '/_test/export').json()
        self.assertEqual(204, self.context.request.post(self.base + '/_test/import', data=snapshot).status)
        def retry(route):
            requests.append((route.request.post_data, route.request.headers.get('idempotency-key')))
            route.continue_()
        self.page.route('**/reservations', retry, times=1)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('confirmation-reference').wait_for()
        self.assertEqual(requests[0], requests[1])
        self.assertEqual(0, self.page.get_by_test_id('booking-uncertain').count())
        state = self.context.request.get(self.base + '/_test/export').json()['state']
        self.assertEqual(1, len(state['reservations']))

    def test_conflict_refresh_keeps_form(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        session = self.page.evaluate('JSON.parse(localStorage.getItem("tablekeeper.session"))')
        result = self.context.request.post(self.base + '/reservations', data={
            'restaurant_id':'r','table_id':'a','starts_at_local':'2035-06-14T18:00','party_size':2},
            headers={'Authorization':'Bearer ' + session['token'], 'Idempotency-Key':'competing-client'})
        self.assertEqual(201, result.status)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-error').wait_for()
        self.page.wait_for_function('document.querySelector(\'[data-testid="slot-a-18:00"]\')?.dataset.available === "false"')
        self.assertEqual('2', self.page.get_by_test_id('booking-party-size').input_value())
        self.assertIn('18:00', self.page.get_by_test_id('booking-summary').inner_text())
        self.assertEqual(0, self.page.get_by_test_id('confirmation').count())

    def test_late_search_cannot_restore_old_restaurant(self):
        self.login()
        held = []
        def hold(route):
            held.append((route, route.fetch()))
        self.page.route('**/availability?restaurant_id=r&**', hold, times=1)
        self.page.get_by_test_id('restaurant-select').select_option('r')
        self.page.get_by_test_id('date-input').fill('2035-06-14')
        self.page.get_by_test_id('search-button').click()
        self.page.wait_for_timeout(150)
        self.page.get_by_test_id('restaurant-select').select_option('other')
        self.page.get_by_test_id('search-button').click()
        self.page.get_by_test_id('availability-grid').wait_for()
        self.assertEqual(1, len(held))
        held[0][0].fulfill(response=held[0][1])
        self.page.wait_for_timeout(100)
        self.page.get_by_test_id('slot-a-18:00').click()
        self.assertIn('The Second Room', self.page.get_by_test_id('booking-summary').inner_text())
        self.assertNotIn('The Test Garden', self.page.get_by_test_id('availability-grid').inner_text())

    def test_signup_and_signed_out_booking(self):
        self.page.goto(self.base)
        self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        self.page.get_by_test_id('auth-error').wait_for()
        self.page.goto(self.base + '/signup')
        self.page.get_by_test_id('signup-display-name').fill('Morgan')
        self.page.get_by_test_id('signup-email').fill('morgan@example.test')
        self.page.get_by_test_id('signup-password').fill('a synthetic password')
        self.page.get_by_test_id('signup-submit').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.assertIn('Morgan', self.page.get_by_test_id('current-user').inner_text())
        self.page.get_by_test_id('logout-button').click()
        self.page.get_by_role('link', name='Sign in', exact=True).wait_for()

    def test_changed_form_new_key_and_empty_day(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-c-18:00').click()
        requests = []
        def capture(route):
            requests.append((route.request.post_data, route.request.headers.get('idempotency-key')))
            route.continue_()
        self.page.route('**/reservations', capture)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('confirmation-reference').wait_for()
        self.page.get_by_test_id('booking-party-size').fill('3')
        self.assertEqual(0, self.page.get_by_test_id('confirmation').count())
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-error').wait_for()
        self.assertNotEqual(requests[0][1], requests[1][1])
        self.assertEqual(3, json.loads(requests[1][0])['party_size'])
        self.assertEqual(0, self.page.get_by_test_id('confirmation').count())
        def closed(route):
            response = route.fetch(); body = response.json(); body['slots'] = []
            route.fulfill(response=response, json=body)
        self.page.route('**/availability?**', closed, times=1)
        self.page.get_by_test_id('search-button').click()
        self.page.get_by_test_id('no-slots').wait_for()
        self.assertEqual(0, self.page.get_by_test_id('availability-grid').count())

    def test_pair_lost_response_retry(self):
        self.login(); self.search(4)
        self.page.get_by_test_id('slot-b+a-18:00').click()
        original = []
        def lose(route):
            original.append((route.request.post_data, route.request.headers['idempotency-key']))
            self.assertEqual(201, route.fetch().status)
            route.abort('connectionreset')
        self.page.route('**/reservations', lose, times=1)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('booking-uncertain').wait_for()
        def recover(route):
            self.assertEqual(original[0], (route.request.post_data, route.request.headers['idempotency-key']))
            route.continue_()
        self.page.route('**/reservations', recover, times=1)
        self.page.get_by_test_id('booking-submit').click()
        self.page.get_by_test_id('confirmation-reference').wait_for()
        self.assertEqual(0, self.page.get_by_test_id('booking-uncertain').count())
        self.assertIn('Garden', self.page.get_by_test_id('confirmation-tables').inner_text())
        self.assertIn('Window', self.page.get_by_test_id('confirmation-tables').inner_text())

    def test_manager_policy_and_immutable_guest_terms(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-c-18:00').click()
        self.page.get_by_test_id('booking-submit').click()
        reference = self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.goto(self.base + '/manager')
        self.page.get_by_test_id('policy-effective').fill('2035-06-14')
        self.page.get_by_test_id('policy-duration').fill('120')
        self.page.get_by_test_id('policy-publish').click()
        self.page.get_by_test_id('policy-success').wait_for()
        self.assertIn('Version 1', self.page.get_by_test_id('policy-list').inner_text())
        self.page.get_by_test_id('policy-publish').click()
        self.page.get_by_test_id('policy-success').wait_for()
        policies = self.context.request.get(self.base + '/restaurants/r/policies').json()['policies']
        self.assertEqual(1, len(policies))
        self.page.set_viewport_size({'width':375,'height':900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 375)
        self.page.goto(self.base + '/lookup?reference=' + reference)
        self.assertIn('90 minutes', self.page.get_by_test_id('accepted-terms').inner_text())
        self.page.get_by_test_id('reservation-history').get_by_text('Reserved', exact=True).wait_for()
        self.assertIn('Version 0', self.page.get_by_test_id('accepted-terms').inner_text())

    def test_series_adoption_replay_list_and_history(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        self.page.get_by_test_id('booking-submit').click()
        reference = self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.goto(self.base + '/lookup?reference=' + reference)
        self.page.get_by_test_id('series-count').fill('3')
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_test_id('series-created').wait_for()
        self.assertIn('3 visits', self.page.get_by_test_id('series-created').inner_text())
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_test_id('series-created').wait_for()
        self.page.get_by_role('link', name='View your regular evenings').click()
        self.page.get_by_test_id('series-detail').wait_for()
        self.assertEqual(3, self.page.locator('.occurrences > li').count())
        self.assertIn(reference, self.page.get_by_test_id('series-detail').inner_text())
        self.page.set_viewport_size({'width':375,'height':900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),375)
        self.page.goto(self.base + '/series')
        self.page.get_by_test_id('series-detail').wait_for()
        self.assertEqual(1, self.page.get_by_test_id('series-detail').count())

    def test_closure_apply_lost_response_and_mobile(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        self.page.get_by_test_id('booking-submit').click()
        reference = self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.goto(self.base + '/manager')
        self.page.get_by_test_id('closure-from').fill('2035-06-14T18:00')
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        self.assertEqual('1', self.page.get_by_test_id('replan-moved-count').inner_text())
        self.assertIn(reference, self.page.get_by_test_id('replan-assignment').inner_text())
        self.assertIn('90 minutes', self.page.get_by_test_id('replan-preserved').inner_text())
        self.page.set_viewport_size({'width':375,'height':900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),375)
        requests = []
        def lose(route):
            requests.append((route.request.post_data, route.request.headers['idempotency-key']))
            self.assertEqual(201, route.fetch().status); route.abort('connectionreset')
        self.page.route('**/replans/*/apply',lose,times=1)
        self.page.get_by_test_id('replan-apply').click()
        self.page.get_by_test_id('replan-uncertain').wait_for()
        def retry(route):
            self.assertEqual(requests[0],(route.request.post_data,route.request.headers['idempotency-key']))
            route.continue_()
        self.page.route('**/replans/*/apply',retry,times=1)
        self.page.get_by_test_id('replan-apply').click()
        self.page.get_by_test_id('replan-success').wait_for()
        self.assertTrue(self.page.get_by_test_id('replan-apply').is_disabled())
        self.assertEqual(0,self.page.get_by_test_id('replan-uncertain').count())

    def test_deterministic_demo_and_accessible_preview(self):
        from tablekeeper.demo import fixture
        self.assertEqual(204,self.context.request.post(self.base+'/_test/reset',data=fixture()).status)
        self.page.goto(self.base+'/login')
        self.page.get_by_test_id('login-email').fill('manager@tablekeeper.test')
        self.page.get_by_test_id('login-password').fill('a thoughtful service')
        self.page.get_by_test_id('login-submit').click()
        self.page.get_by_test_id('current-user').wait_for()
        self.page.goto(self.base+'/manager')
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        self.assertEqual('1',self.page.get_by_test_id('replan-moved-count').inner_text())
        self.assertEqual(3,self.page.get_by_test_id('replan-assignment').count())
        moved=self.page.locator('.assignment-moved')
        self.assertIn('EVENING1',moved.inner_text())
        self.assertIn('Window nook',moved.inner_text())
        self.assertIn('Garden table',moved.inner_text())
        self.assertTrue(all(self.page.locator('input:visible,select:visible').evaluate_all(
            'els=>els.map(e=>Boolean(e.labels?.length || e.getAttribute("aria-label")))')))
        self.page.get_by_test_id('replan-apply').focus()
        self.assertTrue(self.page.get_by_test_id('replan-apply').evaluate('e=>e===document.activeElement'))
        output=os.environ.get('TABLEKEEPER_SCREENSHOTS')
        if output:
            folder=Path(output);folder.mkdir(parents=True,exist_ok=True)
            self.page.screenshot(path=str(folder/'stage4-manager-desktop.png'),full_page=True)
        self.page.set_viewport_size({'width':375,'height':900})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),375)
        if output:self.page.screenshot(path=str(folder/'stage4-manager-mobile.png'),full_page=True)
        self.page.get_by_test_id('replan-apply').click()
        self.page.get_by_test_id('replan-success').wait_for()

    def test_closure_stale_refresh_and_impossible(self):
        self.login(); self.page.goto(self.base + '/manager')
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        session=self.page.evaluate('JSON.parse(localStorage.getItem("tablekeeper.session"))')
        self.assertEqual(201,self.context.request.post(self.base+'/reservations',data={
            'restaurant_id':'r','table_id':'c','starts_at_local':'2035-06-14T19:00','party_size':6},
            headers={'Authorization':'Bearer '+session['token'],'Idempotency-Key':'stale-repair'}).status)
        self.page.get_by_test_id('replan-apply').click()
        self.page.get_by_test_id('replan-refresh').wait_for()
        self.page.get_by_test_id('replan-refresh').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        self.page.get_by_test_id('closure-table').select_option('c')
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('closure-error').wait_for()
        self.assertIn('No safe seating plan',self.page.get_by_test_id('closure-error').inner_text())
        self.assertEqual(0,self.page.get_by_test_id('replan-apply').count())

    def test_closure_preview_retry_and_timezone_boundaries(self):
        self.login(); self.page.goto(self.base+'/manager')
        self.page.get_by_test_id('closure-preview').wait_for()
        self.assertEqual('2035-06-14T17:00:00.000+00:00',self.page.evaluate(
            'restaurantInstant("2035-06-14T19:00","Europe/Berlin")'))
        self.assertEqual('2035-10-28T00:30:00.000+00:00',self.page.evaluate(
            'restaurantInstant("2035-10-28T02:30","Europe/Berlin")'))
        self.assertIn('does not exist',self.page.evaluate('''() => {
            try { restaurantInstant("2035-03-25T02:30","Europe/Berlin"); return "bad"; }
            catch(error) { return error.message; }
        }'''))
        requests=[]
        def lose(route):
            requests.append((route.request.post_data,route.request.headers['idempotency-key']))
            self.assertEqual(201,route.fetch().status);route.abort('connectionreset')
        self.page.route('**/restaurants/r/replans',lose,times=1)
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('closure-uncertain').wait_for()
        def retry(route):
            self.assertEqual(requests[0],(route.request.post_data,route.request.headers['idempotency-key']))
            route.continue_()
        self.page.route('**/restaurants/r/replans',retry,times=1)
        self.page.get_by_test_id('closure-preview').click()
        self.page.get_by_test_id('replan-preview').wait_for()
        self.assertEqual('0',self.page.get_by_test_id('replan-moved-count').inner_text())

    def test_series_amend_lost_response_and_refresh(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        self.page.get_by_test_id('booking-submit').click()
        reference=self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.goto(self.base+'/lookup?reference='+reference)
        self.page.get_by_test_id('series-count').fill('3')
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_role('link',name='View your regular evenings').click()
        self.page.get_by_test_id('series-local-time').fill('19:00')
        requests=[]
        def lose(route):
            requests.append((route.request.post_data,route.request.headers['idempotency-key']))
            self.assertEqual(201,route.fetch().status);route.abort('connectionreset')
        self.page.route('**/series/*/amend',lose,times=1)
        self.page.get_by_test_id('series-amend-submit').click()
        self.page.get_by_test_id('series-amend-uncertain').wait_for()
        def retry(route):
            self.assertEqual(requests[0],(route.request.post_data,route.request.headers['idempotency-key']))
            route.continue_()
        self.page.route('**/series/*/amend',retry,times=1)
        self.page.get_by_test_id('series-amend-submit').click()
        self.page.get_by_test_id('series-amend-success').wait_for()
        self.page.get_by_test_id('series-refresh').click()
        self.page.get_by_test_id('series-refreshed').wait_for()
        self.assertIn('revision 2',self.page.get_by_test_id('series-eligibility').inner_text())

    def test_series_stale_revision_and_cancelled_eligibility(self):
        self.login(); self.search()
        self.page.get_by_test_id('slot-a-18:00').click()
        self.page.get_by_test_id('booking-submit').click()
        reference=self.page.get_by_test_id('confirmation-reference').inner_text()
        self.page.goto(self.base+'/lookup?reference='+reference)
        self.page.get_by_test_id('series-count').fill('3')
        self.page.get_by_test_id('series-create').click()
        self.page.get_by_role('link',name='View your regular evenings').click()
        self.page.get_by_test_id('series-local-time').fill('19:00')
        session=self.page.evaluate('JSON.parse(localStorage.getItem("tablekeeper.session"))')
        headers={'Authorization':'Bearer '+session['token']}
        self.assertEqual(200,self.context.request.post(self.base+'/reservations/'+reference+'/cancel',data={},headers=headers).status)
        self.page.get_by_test_id('series-amend-submit').click()
        self.page.get_by_test_id('series-amend-error').wait_for()
        self.assertIn('changed since',self.page.get_by_test_id('series-amend-error').inner_text())
        self.page.get_by_test_id('series-refresh').click()
        self.page.get_by_test_id('series-refreshed').wait_for()
        self.assertIn('Skipped: cancelled',self.page.get_by_test_id('series-eligibility').inner_text())
        self.page.get_by_test_id('series-amend-submit').click()
        self.page.get_by_test_id('series-amend-success').wait_for()

    def test_policy_uncertain_retry_and_permission_screen(self):
        self.login(); self.page.goto(self.base + '/manager')
        self.page.get_by_test_id('policy-effective').fill('2036-02-20')
        original = []
        def lose(route):
            original.append((route.request.post_data,route.request.headers['idempotency-key']))
            self.assertEqual(201,route.fetch().status);route.abort('connectionreset')
        self.page.route('**/restaurants/r/policies',lose,times=1)
        self.page.get_by_test_id('policy-publish').click()
        self.page.get_by_test_id('policy-uncertain').wait_for()
        def recover(route):
            self.assertEqual(original[0],(route.request.post_data,route.request.headers['idempotency-key']))
            route.continue_()
        self.page.route('**/restaurants/r/policies',recover,times=1)
        self.page.get_by_test_id('policy-publish').click()
        self.page.get_by_test_id('policy-success').wait_for()
        self.assertEqual(0,self.page.get_by_test_id('policy-uncertain').count())
        self.page.get_by_test_id('logout-button').click()
        self.page.goto(self.base + '/manager')
        self.assertEqual(0,self.page.get_by_test_id('policy-publish').count())
        self.page.get_by_role('heading',name='A place to return to.').wait_for()


if __name__ == '__main__':
    unittest.main(verbosity=2)
