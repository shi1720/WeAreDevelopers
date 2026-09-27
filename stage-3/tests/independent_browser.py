"""Independent real-browser stage-2 scenarios, including a live stage-1 upgrade.

Run separately from unittest HTTP discovery:
TABLEKEEPER_BASE_URL=http://127.0.0.1:18092 \
TABLEKEEPER_STAGE1_URL=http://127.0.0.1:18091 \
  /tmp/proofline-official-spec/.venv/bin/python stage-2/tests/independent_browser.py

Uses disposable services. No token, export, or request body is written to disk.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit, parse_qs

from playwright.async_api import async_playwright, expect
from independent_combinations import combination_fixture
from independent_contract import PASSWORD


TARGET = os.environ.get("TABLEKEEPER_BASE_URL", "http://127.0.0.1:18092").rstrip("/")
SOURCE = os.environ.get("TABLEKEEPER_STAGE1_URL", "http://127.0.0.1:18091").rstrip("/")
LEGACY_UI = os.environ.get("TABLEKEEPER_STAGE2_URL", "http://127.0.0.1:18092").rstrip("/")
DATE = "2032-06-17"


def ui_fixture():
    data = combination_fixture()
    data["restaurants"][0]["opening_hours"] = [
        {"weekday": d, "opens": "18:00", "closes": "21:00"}
        for d in "mon tue wed thu fri sat sun".split()]
    second = copy.deepcopy(data["restaurants"][0])
    second.update(id="r-second", name="Second Dining Room", timezone="Asia/Kolkata",
                  tables=[{"id": "second-table", "label": "Terrace", "capacity": 8}], combinable=[])
    data["restaurants"].append(second)
    return data


async def reset(api, base=TARGET, data=None):
    response = await api.post(base + "/_test/reset", data=data or ui_fixture())
    assert response.status == 204, "fixture reset failed"


async def login(page):
    await page.goto(TARGET + "/login")
    await page.get_by_test_id("login-email").fill("ada@example.test")
    await page.get_by_test_id("login-password").fill(PASSWORD)
    await page.get_by_test_id("login-submit").click()
    await expect(page.get_by_test_id("current-user")).to_contain_text("Ada")


async def search(page, party=5, restaurant="r-independent", date=DATE):
    if urlsplit(page.url).path != "/":
        await page.goto(TARGET + "/")
    await page.get_by_test_id("restaurant-select").select_option(restaurant)
    await page.get_by_test_id("date-input").fill(date)
    await page.get_by_test_id("party-size-input").fill(str(party))
    await page.get_by_test_id("search-button").click()
    await expect(page.get_by_test_id("availability-grid")).to_be_visible()


def cell(pair):
    return "slot-table-a+table-z-18:00" if pair else "slot-table-m-18:00"


async def select(page, pair=True):
    await page.get_by_test_id(cell(pair)).click()
    await expect(page.get_by_test_id("booking-form")).to_be_visible()
    if pair:
        await expect(page.get_by_test_id("booking-summary")).to_contain_text("Garden")
        await expect(page.get_by_test_id("booking-summary")).to_contain_text("Window")
    await expect(page.get_by_test_id("booking-summary")).to_contain_text("18:00")


async def scenario_routes_grid_visual(browser, api):
    await reset(api)
    context = await browser.new_context(viewport={"width": 375, "height": 812})
    page = await context.new_page()
    external = []
    page.on("request", lambda request: external.append(request.url)
            if request.url.startswith("http") and not request.url.startswith(TARGET + "/") else None)
    await login(page)
    for path, hook in (("/", "search-button"), ("/signup", "signup-submit"),
                       ("/login", "login-submit"), ("/lookup", "lookup-submit")):
        await page.goto(TARGET + path)
        await expect(page.get_by_test_id(hook)).to_be_visible()
        await expect(page.get_by_test_id("current-user")).to_contain_text("Ada")
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "horizontal page scroll at 375px"
    await search(page)
    response = await api.get(TARGET + "/availability", params={"restaurant_id": "r-independent", "date": DATE, "party_size": 5})
    slots = (await response.json())["slots"]
    for slot in slots:
        for table in ("table-z", "table-a", "table-m"):
            hook = f"slot-{table}-{slot['starts_at_local'][-5:]}"
            expected = "true" if table in slot["available_table_ids"] else "false"
            await expect(page.get_by_test_id(hook)).to_have_attribute("data-available", expected)
    await select(page)
    await expect(page.get_by_test_id("booking-party-size")).to_have_value("5")
    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "booking form overflows mobile"
    labels = await page.locator("input:visible,select:visible").evaluate_all("els => els.map(e => Boolean((e.labels && e.labels.length) || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby')))")
    assert all(labels), "visible input without a programmatic label"
    await page.get_by_test_id("booking-submit").focus()
    assert await page.get_by_test_id("booking-submit").evaluate("e => e === document.activeElement"), "submit is not focusable"
    output = os.environ.get("TABLEKEEPER_SCREENSHOTS")
    if output:
        folder = Path(output); folder.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(folder / "stage2-mobile.png"), full_page=True)
        await page.set_viewport_size({"width": 1440, "height": 1000})
        await page.screenshot(path=str(folder / "stage2-desktop.png"), full_page=True)
    assert not external, "browser requested external runtime assets"
    await context.close()


async def scenario_lost_response(browser, api, pair):
    await reset(api)
    context = await browser.new_context()
    page = await context.new_page()
    await login(page); await search(page); await select(page, pair)
    observed = []
    committed = {}
    async def intercept(route):
        request = route.request
        if request.method != "POST":
            await route.continue_(); return
        observed.append((request.headers.get("idempotency-key"), json.loads(request.post_data)))
        response = await route.fetch()
        if len(observed) == 1:
            assert response.status == 201, "first write must commit before lost response"
            committed.update(await response.json())
            await route.abort("failed")
        else:
            await route.fulfill(response=response)
    await page.route("**/reservations", intercept)
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("booking-uncertain")).to_be_visible()
    assert (await page.get_by_test_id("booking-uncertain").inner_text()).strip()
    await expect(page.get_by_test_id("booking-error")).to_have_count(0)
    await expect(page.get_by_test_id("confirmation")).to_have_count(0)
    await expect(page.get_by_test_id("booking-party-size")).to_have_value("5")
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("confirmation-reference")).to_have_text(committed["reference"])
    assert len(observed) == 2 and observed[0] == observed[1], "uncertain retry changed exact JSON/key"
    await expect(page.get_by_test_id("booking-uncertain")).to_have_count(0)
    await expect(page.get_by_test_id("booking-error")).to_have_count(0)
    await expect(page.get_by_test_id("booking-form")).to_be_visible()
    # Another unchanged submit must reach the server and recover the same receipt.
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("confirmation-reference")).to_have_text(committed["reference"])
    await page.wait_for_timeout(100)
    assert len(observed) == 3 and observed[2] == observed[0], "success replay was not sent unchanged"
    await page.get_by_test_id("booking-party-size").fill("1")
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("booking-error")).to_be_visible()
    assert observed[-1][0] != observed[0][0], "edited form retained old idempotency key"
    await context.close()


async def scenario_conflict(browser, api, pair):
    await reset(api)
    context = await browser.new_context(); page = await context.new_page()
    await login(page); await search(page); await select(page, pair)
    login_response = await api.post(TARGET + "/auth/login", data={"email": "bea@example.test", "password": PASSWORD})
    token = (await login_response.json())["token"]
    body = {"restaurant_id": "r-independent", "table_id": "table-a" if pair else "table-m",
            "starts_at_local": DATE + "T18:00", "party_size": 2}
    response = await api.post(TARGET + "/reservations", data=body,
                              headers={"Authorization": "Bearer " + token, "Idempotency-Key": "competing-browser"})
    assert response.status == 201
    refreshes = []
    page.on("request", lambda request: refreshes.append(request.url) if "/availability?" in request.url else None)
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("booking-error")).to_be_visible()
    await expect(page.get_by_test_id("confirmation")).to_have_count(0)
    await expect(page.get_by_test_id("booking-form")).to_be_visible()
    await expect(page.get_by_test_id("booking-party-size")).to_have_value("5")
    await page.wait_for_timeout(150)
    assert refreshes, "confirmed conflict did not refresh availability"
    await expect(page.get_by_test_id("booking-summary")).to_contain_text("18:00")
    await context.close()


async def scenario_stale_search(browser, api):
    await reset(api)
    context = await browser.new_context(); page = await context.new_page()
    await login(page); await page.goto(TARGET + "/")
    entered, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
    async def delayed(route):
        query = parse_qs(urlsplit(route.request.url).query)
        if query.get("restaurant_id") != ["r-independent"]:
            await route.continue_(); return
        response = await route.fetch()
        entered.set()
        await release.wait()
        try:
            await route.fulfill(response=response)
        except Exception:
            # Aborting obsolete fetches is also valid stale-response protection.
            pass
        finally:
            finished.set()
    await page.route("**/availability?*", delayed)
    await page.get_by_test_id("restaurant-select").select_option("r-independent")
    await page.get_by_test_id("date-input").fill(DATE)
    await page.get_by_test_id("party-size-input").fill("2")
    await page.get_by_test_id("search-button").click()
    await asyncio.wait_for(entered.wait(), 10)
    await search(page, party=2, restaurant="r-second")
    await page.get_by_test_id("slot-second-table-18:00").click()
    await expect(page.get_by_test_id("booking-summary")).to_contain_text("Terrace")
    release.set(); await asyncio.wait_for(finished.wait(), 10)
    await page.wait_for_timeout(150)
    await expect(page.get_by_test_id("restaurant-select")).to_have_value("r-second")
    await expect(page.get_by_test_id("slot-second-table-18:00")).to_be_visible()
    await expect(page.get_by_test_id("booking-summary")).to_contain_text("Terrace")
    await expect(page.get_by_test_id("slot-table-z-18:00")).to_have_count(0)
    await context.close()


async def scenario_live_stage1_upgrade(browser, api):
    data = ui_fixture()
    for restaurant in data["restaurants"]:
        restaurant.pop("combinable", None)
    await reset(api, SOURCE, data)
    await reset(api)
    context = await browser.new_context(); page = await context.new_page()
    upgrading = {"source": True, "drop": True}
    writes, original = [], {}
    async def backend(route):
        request = route.request
        path = urlsplit(request.url).path
        # Retain the actual predecessor browser code through upgrade. A new
        # stage-3 page expects policies that the stage-1 source never offered.
        if path in ('/', '/login', '/lookup') or path.startswith('/static/'):
            response = await route.fetch(url=LEGACY_UI + path)
            await route.fulfill(response=response)
            return
        if path not in ("/auth/login", "/restaurants", "/availability", "/reservations") and not path.startswith("/restaurants/") and not path.startswith("/reservations/"):
            await route.continue_(); return
        base = SOURCE if upgrading["source"] else TARGET
        parsed = urlsplit(request.url)
        response = await route.fetch(url=base + parsed.path + ("?" + parsed.query if parsed.query else ""))
        if path == "/reservations" and request.method == "POST":
            writes.append((request.headers.get("idempotency-key"), json.loads(request.post_data)))
            if upgrading["drop"]:
                assert response.status == 201, "stage1 must commit the pending request"
                original.update(await response.json()); upgrading["drop"] = False
                await route.abort("failed"); return
        await route.fulfill(response=response)
    await page.route(TARGET + "/**", backend)
    await login(page); await search(page); await select(page, pair=False)
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("booking-uncertain")).to_be_visible()
    assert "table_ids" not in original, "source must be actual accepted stage1 service"
    exported = await (await api.get(SOURCE + "/_test/export")).json()
    imported = await api.post(TARGET + "/_test/import", data=exported)
    assert imported.status == 204, "stage2 rejected genuine stage1 export"
    upgrading["source"] = False
    # No page navigation/reload between loss, migration, and retry.
    await expect(page.get_by_test_id("current-user")).to_contain_text("Ada")
    await expect(page.get_by_test_id("booking-party-size")).to_have_value("5")
    await page.get_by_test_id("booking-submit").click()
    await expect(page.get_by_test_id("confirmation-reference")).to_have_text(original["reference"])
    assert len(writes) == 2 and writes[0] == writes[1], "upgrade altered pending request identity"
    await expect(page.get_by_test_id("confirmation-details")).to_contain_text("Hearth")
    await expect(page.get_by_test_id("booking-uncertain")).to_have_count(0)
    await page.goto(TARGET + "/lookup")
    await page.get_by_test_id("lookup-reference-input").fill(original["reference"])
    await page.get_by_test_id("lookup-submit").click()
    await expect(page.get_by_test_id("reservation-status")).to_have_text("confirmed")
    await expect(page.get_by_test_id("reservation-tables")).to_contain_text("Hearth")
    await page.get_by_test_id("reservation-cancel-button").click()
    await expect(page.get_by_test_id("reservation-status")).to_have_text("cancelled")
    await expect(page.get_by_test_id("reservation-cancel-button")).to_have_count(0)
    await context.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        api = await p.request.new_context()
        cases = [
            ("routes-grid-mobile-desktop-assets", lambda: scenario_routes_grid_visual(browser, api)),
            ("single-lost-response", lambda: scenario_lost_response(browser, api, False)),
            ("pair-lost-response", lambda: scenario_lost_response(browser, api, True)),
            ("single-conflict-refresh", lambda: scenario_conflict(browser, api, False)),
            ("pair-conflict-refresh", lambda: scenario_conflict(browser, api, True)),
            ("stale-search-result", lambda: scenario_stale_search(browser, api)),
            ("live-stage1-upgrade-pending-retry", lambda: scenario_live_stage1_upgrade(browser, api)),
        ]
        failed = []
        for name, call in cases:
            started = time.monotonic()
            try:
                await call()
                print(f"PASS {name} duration_seconds={time.monotonic()-started:.3f}", flush=True)
            except Exception as error:
                failed.append(name)
                print(f"FAIL {name} {type(error).__name__}: {error}", flush=True)
            finally:
                for context in browser.contexts:
                    await context.close()
        await browser.close(); await api.dispose()
        print(f"scenarios={len(cases)} passed={len(cases)-len(failed)} failed={len(failed)}", flush=True)
        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
