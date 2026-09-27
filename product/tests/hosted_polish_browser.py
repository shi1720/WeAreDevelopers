"""Operator follow-up regression, outside both accepted BAND runs.

Run from product with a Python environment containing pytest, httpx and Playwright:
python -m pytest tests/hosted_polish_browser.py -q
Uses the existing durable SQLite service harness and synthetic demo, not mocks of
reservation state. Only transport faults are injected at the browser boundary.
"""
import pytest
from playwright.sync_api import sync_playwright, expect
from acceptance_http import Service


@pytest.fixture
def demo(tmp_path):
    service = Service(tmp_path, demo=True)
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            page = context.new_page()
            page.set_default_timeout(8000)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            try:
                page.goto(service.url + '/demo')
                page.locator('#start-demo').click()
                page.get_by_test_id('current-user').wait_for()
                page.goto(service.url + '/demo')
                page.locator('[data-demo="manager"]').click()
                page.get_by_test_id('closure-preview').wait_for()
                yield service, page
                assert not errors, 'Unexpected browser JavaScript error'
            finally:
                context.close()
                browser.close()
    finally:
        service.close()


@pytest.mark.parametrize('fault', ['none', 'roster_refresh', 'lost_apply_response'])
def test_confirmed_repair_updates_labels_and_selected_date_roster(demo, fault):
    service, page = demo
    selected_date = '2035-06-14'
    page.locator('#roster-date').fill(selected_date)
    page.get_by_test_id('roster-load').click()
    row = page.get_by_test_id('roster-row').filter(has_text='EVENING1')
    expect(row).to_contain_text('Window nook')
    page.get_by_test_id('closure-preview').click()
    plan = page.get_by_test_id('replan-preview')
    expect(plan.locator('.section-heading .eyebrow')).to_contain_text('Preview only')
    expect(plan.locator('.map-closed')).to_contain_text('Proposed closure')

    attempts = []
    def apply_transport(route):
        request = route.request
        attempts.append((request.post_data_json, request.headers.get('idempotency-key')))
        if fault == 'lost_apply_response' and len(attempts) == 1:
            headers = {key: value for key, value in request.all_headers().items()
                       if key.lower() not in ('content-length', 'transfer-encoding')}
            response = route.fetch(headers=headers)
            assert response.status == 201
            route.abort('failed')
        else:
            route.continue_()

    page.route('**/replans/*/apply', apply_transport)
    if fault == 'roster_refresh':
        page.route('**/api/roster?*', lambda route: route.abort('failed'))
    page.get_by_test_id('replan-apply').click()
    if fault == 'lost_apply_response':
        page.get_by_test_id('replan-uncertain').wait_for()
        expect(plan.locator('.section-heading .status')).to_have_text('Not applied')
        page.get_by_test_id('replan-apply').click()
    page.get_by_test_id('replan-success').wait_for()
    expect(plan.locator('.section-heading .status')).to_have_text('Applied')
    expect(plan.locator('.section-heading .eyebrow')).to_contain_text('Applied')
    expect(plan.locator('.section-heading .eyebrow')).not_to_contain_text('Preview only')
    expect(plan.locator('.map-closed')).to_contain_text('Closed for the selected interval')
    expect(plan.locator('.map-closed')).not_to_contain_text('Proposed closure')
    expect(page.get_by_test_id('replan-apply')).to_be_disabled()
    expect(page.locator('#roster-date')).to_have_value(selected_date)
    expect(page.get_by_test_id('replan-uncertain')).to_have_count(0)
    expect(page.get_by_test_id('replan-error')).to_have_count(0)
    expect(page.get_by_test_id('recover-request')).to_have_count(0)

    if fault == 'roster_refresh':
        expect(page.get_by_test_id('roster-error')).to_contain_text('seating repair is saved')
        expect(page.get_by_test_id('replan-success')).to_be_visible()
        page.unroute('**/api/roster?*')
        page.get_by_test_id('roster-load').click()
    # This is a real server read after mutation, without reloading the page or
    # clicking Load roster in the ordinary and exact-retry cases.
    expect(row).to_contain_text('Garden table')
    expect(row).not_to_contain_text('Window nook')
    expect(row).to_contain_text('19:00')
    expect(row).to_contain_text('2 guests')
    assert len(attempts) == (2 if fault == 'lost_apply_response' else 1)
    if fault == 'lost_apply_response':
        assert attempts[0] == attempts[1] and attempts[0][1]
    # Persistence and exact receipt handling remain the durable service's job.
    service.restart()
    page.reload()
    page.locator('#roster-date').fill(selected_date)
    page.get_by_test_id('roster-load').click()
    expect(page.get_by_test_id('roster-row').filter(has_text='EVENING1')).to_contain_text('Garden table')
