"""Independent optional stage-3 product walkthrough and responsive checks."""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright,expect
from independent_policies import policy_fixture
from independent_contract import PASSWORD

BASE=os.environ.get('TABLEKEEPER_BASE_URL','http://127.0.0.1:18094')

async def main():
    async with async_playwright() as p:
        api=await p.request.new_context();assert (await api.post(BASE+'/_test/reset',data=policy_fixture())).status==204
        browser=await p.chromium.launch();page=await browser.new_page(viewport={'width':375,'height':812})
        async def login(email):
            await page.goto(BASE+'/login');await page.get_by_test_id('login-email').fill(email)
            await page.get_by_test_id('login-password').fill(PASSWORD);await page.get_by_test_id('login-submit').click()
            await expect(page.get_by_test_id('current-user')).to_be_visible()
        await login('bea@example.test');await page.goto(BASE+'/manager')
        await expect(page.get_by_test_id('policy-publish')).to_be_visible()
        await page.get_by_test_id('policy-effective').fill('2032-06-01')
        await page.get_by_test_id('policy-duration').fill('120')
        for width in (375,1440):
            await page.set_viewport_size({'width':width,'height':900})
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            await page.screenshot(path=str(Path('evidence/stage-3')/f'manager-{width}.png'),full_page=True)
        await page.get_by_test_id('policy-publish').click();await expect(page.get_by_test_id('policy-success')).to_contain_text('Policy 1')
        await page.get_by_test_id('policy-publish').click();await expect(page.get_by_test_id('policy-success')).to_contain_text('Policy 1')
        assert len((await (await api.get(BASE+'/restaurants/r-independent/policies')).json())['policies'])==1
        print('PASS manager-policy-responsive-original-replay')
        await page.get_by_test_id('logout-button').click();await login('ada@example.test')
        auth=await (await api.post(BASE+'/auth/login',data={'email':'ada@example.test','password':PASSWORD})).json()
        booking=await (await api.post(BASE+'/reservations',headers={'Authorization':'Bearer '+auth['token'],'Idempotency-Key':'product'},data={'restaurant_id':'r-independent','table_id':'table-a','starts_at_local':'2032-06-17T18:00','party_size':2})).json()
        await page.goto(BASE+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(booking['reference']);await page.get_by_test_id('lookup-submit').click()
        await expect(page.get_by_test_id('accepted-terms')).to_contain_text('120 minutes')
        await expect(page.get_by_test_id('reservation-history')).to_contain_text('Reserved')
        await page.get_by_test_id('series-count').fill('3');await page.get_by_test_id('series-create').click()
        await expect(page.get_by_test_id('series-created')).to_contain_text('3 visits')
        await page.get_by_test_id('series-created').get_by_role('link').click()
        await expect(page.get_by_test_id('series-detail')).to_contain_text('3 visits')
        await page.set_viewport_size({'width':375,'height':812})
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.screenshot(path='evidence/stage-3/series-375.png',full_page=True)
        print('PASS guest-terms-history-series-adoption-responsive')
        await page.goto(BASE+'/manager');await expect(page.locator('#manager-content')).to_contain_text('does not manage')
        await expect(page.get_by_test_id('policy-publish')).to_have_count(0)
        print('PASS diner-manager-screen-permission')
        await browser.close();await api.dispose()

if __name__=='__main__':asyncio.run(main())
