"""Independent closure-to-guest browser flow on a disposable frozen service."""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect
from independent_series import IndependentSeries
from independent_contract import PASSWORD


async def main():
    x = IndependentSeries(); x.setUp()
    anchor = x.create(); series = x.adopt(anchor)
    base = os.environ['TABLEKEEPER_BASE_URL']
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width':375,'height':812})
        async def login(email):
            await page.goto(base+'/login')
            await page.get_by_test_id('login-email').fill(email)
            await page.get_by_test_id('login-password').fill(PASSWORD)
            await page.get_by_test_id('login-submit').click()
            await expect(page.get_by_test_id('current-user')).to_be_visible()
        await login('bea@example.test'); await page.goto(base+'/manager')
        await page.get_by_test_id('closure-table').select_option('table-z')
        await page.get_by_test_id('closure-from').fill('2032-06-17T18:00')
        await page.get_by_test_id('closure-to').fill('2032-06-17T19:00')
        await page.get_by_test_id('closure-preview').click()
        await expect(page.get_by_test_id('replan-assignment')).to_have_count(1)
        await expect(page.get_by_test_id('replan-moved-count')).to_have_text('1')
        await expect(page.get_by_test_id('replan-preserved')).to_contain_text('2 guests')
        assert x.current(series) == series, 'preview changed series'
        for width in (375,1440):
            await page.set_viewport_size({'width':width,'height':900})
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            await page.screenshot(path=str(Path('evidence/stage-4')/('independent-repair-'+str(width)+'.png')),full_page=True)
        await page.get_by_test_id('replan-apply').click()
        await expect(page.get_by_test_id('replan-success')).to_be_visible()
        repaired = x.current(series)
        assert repaired['revision'] == 2
        assert repaired['occurrences'][0]['reservation']['table_ids'] != anchor['table_ids']
        await page.get_by_test_id('logout-button').click(); await login('ada@example.test')
        await page.goto(base+'/series?series_id='+series['series_id'])
        await page.get_by_test_id('series-from-index').select_option('1')
        await page.get_by_test_id('series-local-time').fill('20:00')
        await page.get_by_test_id('series-amend-submit').click()
        await expect(page.get_by_test_id('series-amend-success')).to_contain_text('revision 3')
        current = x.current(series)
        assert current['occurrences'][0] == repaired['occurrences'][0]
        assert all(o['reservation']['starts_at_local'].endswith('20:00') and not o['exception'] for o in current['occurrences'][1:])
        await page.set_viewport_size({'width':375,'height':812})
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.screenshot(path='evidence/stage-4/independent-series-375.png',full_page=True)
        await browser.close()
        print('PASS independent manager-preview/apply/guest-series-amend responsive375/1440; API identities and preserved first occurrence verified')


if __name__ == '__main__':
    asyncio.run(main())
