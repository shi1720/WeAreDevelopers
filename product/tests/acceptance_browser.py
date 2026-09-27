"""Verifier-owned real Chromium checks; source selected by ACCEPTANCE_PRODUCT_ROOT.

Use prepared Python3.12 with Playwright. Screenshots contain synthetic data only.
"""
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from acceptance_http import Service, PASSWORD


@pytest.fixture
def ui(tmp_path):
    service = Service(tmp_path)
    with sync_playwright() as play:
        browser = play.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        page.set_default_timeout(8000)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        yield service, page
        try:
            context.close()
            browser.close()
        finally:
            service.close()
        assert not errors, 'browser JavaScript errors'


def capture(page, name):
    directory = Path(os.environ.get('ACCEPTANCE_SCREENSHOTS', '/tmp/verifier-browser-screenshots'))
    directory.mkdir(parents=True, exist_ok=True)
    for width in (1440, 375):
        page.set_viewport_size({'width': width, 'height': 1000 if width > 375 else 900})
        assert page.evaluate('document.documentElement.scrollWidth') <= width, f'overflow on {name} at {width}'
        page.screenshot(path=str(directory / f'{name}-{width}.png'), full_page=True)
    page.set_viewport_size({'width': 1440, 'height': 1000})


def setup(service, page):
    page.goto(service.url + '/setup')
    page.get_by_test_id('setup-submit').wait_for()
    capture(page, 'setup')
    page.locator('#setup-secret').fill(service.secret)
    page.locator('#setup-name').fill('Synthetic Owner')
    page.locator('#setup-email').fill('owner@acceptance.test')
    page.locator('#setup-password').fill(PASSWORD)
    page.locator('#venue-name').fill('Verifier Hearth')
    page.locator('#venue-timezone').fill('Etc/UTC')
    page.get_by_test_id('setup-submit').click()
    page.get_by_test_id('manager-restaurant').wait_for()
    assert all(cookie['name'] == '__session' and cookie['httpOnly'] for cookie in page.context.cookies())


def search(service, page):
    page.goto(service.url + '/')
    page.wait_for_function("document.querySelector('#restaurant')?.value")
    page.get_by_test_id('date-input').fill('2032-06-17')
    page.get_by_test_id('party-size-input').fill('2')
    page.get_by_test_id('search-button').click()
    page.get_by_test_id('availability-grid').wait_for()
    page.get_by_test_id('slot-table_1-18:00').click()


def test_real_setup_booking_list_edit_roster_keyboard(ui):
    service, page = ui
    setup(service, page)
    search(service, page)
    page.get_by_test_id('booking-submit').focus()
    assert page.get_by_test_id('booking-submit').evaluate('(e)=>document.activeElement===e')
    page.keyboard.press('Enter')
    reference = page.get_by_test_id('confirmation-reference').inner_text()
    capture(page, 'confirmation')
    page.goto(service.url + '/bookings')
    page.get_by_test_id('booking-list-item').wait_for()
    assert reference in page.locator('#bookings-list').inner_text()
    capture(page, 'bookings')
    page.get_by_role('link', name=f'View or edit {reference}').click()
    page.get_by_test_id('edit-search').click()
    page.get_by_test_id('edit-choice').select_option(label='19:30 · Garden table')
    page.get_by_test_id('edit-terms').wait_for()
    capture(page, 'edit-terms')
    page.get_by_test_id('edit-confirm').click()
    page.get_by_test_id('edit-success').wait_for()
    assert '19:30' in page.get_by_test_id('reservation-detail').inner_text()
    page.goto(service.url + '/manager')
    page.locator('#roster-date').fill('2032-06-17')
    page.get_by_test_id('roster-load').click()
    page.get_by_test_id('roster-row').wait_for()
    assert reference in page.locator('.roster-results').inner_text()
    capture(page, 'manager-roster')


def test_lost_committed_response_reload_restart_exact_retry(ui):
    service, page = ui
    setup(service, page)
    search(service, page)
    observed = []
    def lose(route):
        request = route.request
        # Let Playwright's forwarding client calculate framing. Reusing browser
        # Content-Length can duplicate the header in the forwarded request.
        headers = {k: v for k, v in request.all_headers().items() if k.lower() not in ('content-length', 'transfer-encoding')}
        response = route.fetch(headers=headers)
        assert response.status == 201, f'forwarded booking status={response.status}, error={response.json().get("error")}'
        observed.append((request.post_data_json, request.headers['idempotency-key'], response.json()))
        route.abort('failed')
    page.route('**/reservations', lose)
    page.get_by_test_id('booking-submit').click()
    page.get_by_test_id('booking-uncertain').wait_for()
    assert len(observed) == 1
    saved = page.evaluate("Object.entries(localStorage).filter(([k])=>k.startsWith('tablekeeper.pending.v1.')).map(([k,v])=>JSON.parse(v))")
    assert len(saved) == 1 and saved[0]['body'] == observed[0][0] and saved[0]['key'] == observed[0][1]
    page.unroute('**/reservations', lose)
    service.restart()
    page.reload()
    page.get_by_test_id('recover-request').wait_for()
    retried = []
    def record(route):
        request = route.request
        retried.append((request.post_data_json, request.headers.get('idempotency-key')))
        route.continue_()
    page.route('**/reservations', record)
    page.get_by_test_id('recover-request').click()
    page.get_by_role('link', name='View booking ' + observed[0][2]['reference']).wait_for()
    assert retried == [(observed[0][0], observed[0][1])]
    page.unroute('**/reservations', record)
    page.goto(service.url + '/bookings')
    page.get_by_test_id('booking-list-item').wait_for()
    assert page.get_by_test_id('booking-list-item').count() == 1
    capture(page, 'recovered-booking')
