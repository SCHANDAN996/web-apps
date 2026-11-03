/* Actual account template and assets; all account/payment responses are isolated mocks. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const root = path.resolve(__dirname, '../..');
const base = process.env.BASE_URL || 'http://127.0.0.1:8023';
const python = process.env.QA_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const render = `from app.main import render, app
from starlette.requests import Request
from types import SimpleNamespace
import sys
lang=sys.argv[1]
request=Request({'type':'http','method':'GET','scheme':'http','server':('127.0.0.1',8023),'path':'/membership','query_string':b'','headers':[(b'cookie',('ss_lang='+lang).encode())],'app':app})
sys.stdout.write(render('membership.html',request,None,membership_account=SimpleNamespace(name='QA Learner',username='qa')).body.decode('utf8'))`;

(async () => {
  const browser = await chromium.launch({channel:'chrome', headless:true});
  try {
    for (const lang of ['hi', 'en']) {
      // Rendering needs no DB queries; an in-memory URL prevents fixture persistence.
      const html = execFileSync(python, ['-X', 'utf8', '-c', render, lang], {
        cwd:root, encoding:'utf8', env:{...process.env, DATABASE_URL:'sqlite:///:memory:'}, maxBuffer:2*1024*1024
      });
      const context = await browser.newContext({viewport:{width:360,height:800},serviceWorkers:'block'});
      const page = await context.newPage();
      const errors = [], mutations = [];
      let state = 'trial', failing = false, statusRequests = 0;
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/*', route => route.request().isNavigationRequest() && new URL(route.request().url()).pathname==='/membership' ? route.fulfill({contentType:'text/html; charset=utf-8', body:html}) : route.continue());
      await page.route('**/api/v1/**', route => {
        const request = route.request(), url = new URL(request.url());
        if (request.method() !== 'GET') mutations.push(url.pathname);
        let value = {}, status = 200;
        if (url.pathname === '/api/v1/membership/status') {
          statusRequests++;
          if (failing) {status=503;value={detail:'unavailable'};}
          else value={enabled:state!=='disabled', state, premium_access:['trial','paid'].includes(state),
            trial_ends_at:'2027-01-26T12:00:00Z', paid_until:'2027-05-01T12:00:00Z',
            remaining_seconds:92*86400, trial_period:{unit:'calendar_month',count:3}, auto_renew:false};
        } else if (url.pathname === '/api/v1/classroom/me') {
          value={account:{id:9902,name:'QA Learner',username:'google_internal_identity_not_for_display',storage_namespace:'b'.repeat(48)}};
        } else if (url.pathname === '/api/v1/payments/payu/config') value={enabled:false};
        return route.fulfill({status, contentType:'application/json', body:JSON.stringify(value)});
      });
      await page.goto(base+'/membership?qa='+lang);
      const words = await page.evaluate(() => JSON.parse(document.getElementById('ss-boot').textContent).t);
      const panel = page.locator('#membershipPanel'), line = panel.locator('[data-membership-status]');
      await page.getByText('QA Learner', {exact:true}).waitFor();
      assert.equal(await panel.innerText().then(t=>t.includes('google_internal_identity_not_for_display')),false);
      for (const nextState of ['trial','paid','expired','disabled']) {
        state=nextState;
        if (nextState!=='trial') await page.reload();
        await page.waitForFunction(expected => {
          const p=document.querySelector('#membershipPanel');
          if (!p) return false;
          if (expected==='disabled') return p.hidden;
          const t=JSON.parse(document.getElementById('ss-boot').textContent).t;
          return !p.hidden && p.querySelector('[data-membership-status]').textContent.includes(t['membership_'+expected]);
        }, state).catch(async error => {console.error({lang,state,url:page.url(),text:(await page.locator('main').innerText()).slice(0,180)});throw error;});
        if (state==='trial') {
          assert.match(await line.textContent(), /2027/);
          assert.match(await line.textContent(), /92/);
          assert.equal(await panel.locator('[data-membership-start]').isVisible(), false, 'Trial must already be active');
          assert.equal(await panel.locator('[data-membership-checkout]').isVisible(), false, 'No checkout during trial');
        }
        if (state==='paid') assert.match(await line.textContent(), /2027/);
        if (state==='expired') assert.equal(await panel.locator('[data-membership-start]').isVisible(), false, 'Expired trial must not restart');
        for (const theme of ['light','dark','paper']) {
          await page.evaluate(value => SSTheme.set(value), theme);
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth), true, `${lang}/${state}/${theme} overflow`);
          if (process.env.QA_SCREENSHOT_DIR && state==='trial') {
            fs.mkdirSync(process.env.QA_SCREENSHOT_DIR,{recursive:true});
            await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,`account-${lang}-${theme}.png`),fullPage:true});
          }
        }
      }
      state='trial';failing=true;
      await page.reload();
      await page.getByText(words.membership_error,{exact:true}).waitFor();
      const retry=panel.getByRole('button',{name:words.membership_access_retry,exact:true});
      await retry.waitFor();failing=false;await retry.click();
      await page.waitForFunction(() => document.querySelector('[data-membership-status]').textContent.includes('2027'));
      assert.equal(await retry.isVisible(),false);
      assert.equal(await page.locator('.account-tools .home-image-card').count(),2);
      assert.equal(await page.locator('.account-details[open]').count(),0,'Extra data/legal text starts collapsed');
      await page.locator('.account-details summary').first().click();
      assert.equal(await page.locator('a[href="/delete-account"]').isVisible(),true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),true);
      assert.ok(statusRequests>=6);
      assert.deepEqual(mutations,[],'Account view must not activate a new trial or start a payment');
      assert.deepEqual(errors,[]);
      await context.close();
    }
    console.log('PASS account: HI/EN; trial/paid/expired/disabled; failure+Retry; Home cards; collapsed details; three themes; 360px; no account/payment mutations or JS errors');
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
