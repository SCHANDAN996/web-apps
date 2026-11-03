/* Isolated UI contract: no production traffic or provider charge. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const cid = 'isolated_choice_12345678901234567890';
(async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  try {
    for (const mode of ['valid','invalid','expired','account-change','plain-play']) {
      const p = await browser.newPage({viewport:{width:390,height:844}});
      let orders = 0, sent;
      await p.route('https://choice.test/**', async r => {
        const u = new URL(r.request().url());
        if (u.pathname === '/api/v1/payments/google/alternative/checkout') {
          assert.equal(u.searchParams.get('choice_id'),cid);
          return r.fulfill({status:mode==='invalid'?404:200,json:{enabled:true,choice_id:cid,plan_id:'yearly',states:['BIHAR','UTTAR PRADESH'],expires_at:new Date(Date.now()+(mode==='expired'?-10000:600000)).toISOString()}});
        }
        if (u.pathname === '/api/v1/payments/payu/config') return r.fulfill({json:{enabled:true,channel:'website'}});
        if (u.pathname === '/api/v1/payments/payu/orders') {
          orders++;sent=r.request().postDataJSON();
          return r.fulfill({json:{action_url:'https://secure.payu.in/_payment',fields:{txnid:'isolated-order'}}});
        }
        return r.fulfill({contentType:'text/html',body:'<html><body><script id="ss-boot" type="application/json">{"t":{}}</script><section id="membershipPanel"><div data-membership-checkout></div></section></body></html>'});
      });
      await p.route('https://secure.payu.in/**',r=>r.fulfill({contentType:'text/html',body:'<p>Isolated provider</p>'}));
      await p.goto('https://choice.test/membership'+(mode==='plain-play'?'':'?play_choice='+cid));
      await p.evaluate(()=>{window.StudyStationMembership={allowPayu:()=>false};});
      await p.addScriptTag({content:fs.readFileSync('app/static/js/payu-checkout.js','utf8')});
      await p.evaluate(()=>SSMembershipCheckout(document.querySelector('#membershipPanel'),{enabled:true}));
      assert.equal(orders,0,'opening a page cannot create an order');
      const form = p.locator('.membership-payment-form');
      if (!['valid','account-change'].includes(mode)) {
        assert.equal(await form.count(),0,mode+' must never show checkout');
      } else {
        assert.equal(await form.count(),1);
        assert.equal(await p.locator('[name=plan_id]').inputValue(),'yearly');
        assert.equal(await p.locator('[name=plan_id]').isDisabled(),true);
        await p.locator('[name=billing_state]').selectOption('BIHAR');
        await p.locator('[name=name]').fill('Disposable Test');
        await p.locator('[name=email]').fill('test@example.invalid');
        await p.locator('[name=phone]').fill('9876543210');
        await p.locator('[name=contact_consent]').check();
        if (mode==='account-change') await p.evaluate(()=>window.dispatchEvent(new Event('workspace-scope-changed')));
        await form.locator('[type=submit]').click();
        if (mode==='valid') {
          await p.waitForURL('https://secure.payu.in/_payment');
          assert.equal(orders,1);assert.equal(sent.play_choice_id,cid);assert.equal(sent.plan_id,'yearly');assert.equal(sent.billing_state,'BIHAR');assert.equal(sent.contact_consent,true);
        } else assert.equal(orders,0,'stale-account form cannot submit');
      }
      await p.close();
    }
    for (const unsafe of [false,true]) {
      const p=await browser.newPage();let starts=0;
      const alternative={external_transaction_token:'isolated-sdk-token-value',plan_id:'monthly',product_id:'study_station_monthly',base_plan_id:'monthly-prepaid',country_code:'IN'};
      await p.route('https://choice.test/**',r=>{
        const path=new URL(r.request().url()).pathname;
        if(path.endsWith('/config'))return r.fulfill({json:{enabled:true,user_choice:{enabled:true,countries:['IN']}}});
        if(path.endsWith('/alternative/start')){
          starts++;assert.deepEqual(r.request().postDataJSON(),alternative);
          return r.fulfill({json:{choice_id:cid,checkout_url:unsafe?'https://evil.invalid/pay':'/membership?play_choice='+cid}});
        }
        return r.fulfill({contentType:'text/html',body:'<section data-play-billing></section>'});
      });
      await p.goto('https://choice.test/membership');
      await p.evaluate(alternative=>{
        window.SS={t:{play_billing_loading:'Loading',play_billing_buy:'Buy',play_billing_unavailable:'Unavailable'}};
        window.StudyStationBilling={query:async()=>({ok:true,products:[{plan_id:'monthly',price:'₹9'}]}),purchase:async()=>({ok:true,alternative}),restore:async()=>({ok:true,purchases:[]})};
      },alternative);
      await p.addScriptTag({content:fs.readFileSync('app/static/js/play-billing.js','utf8')});
      await p.evaluate(()=>SSPlayBillingInit(document));await p.locator('[data-play-plan=monthly]').waitFor();
      assert.equal(starts,0);await p.locator('[data-play-plan=monthly]').click();
      if(unsafe){await p.getByRole('status').filter({hasText:'Unavailable'}).waitFor();assert.equal(new URL(p.url()).search,'');}
      else await p.waitForURL('https://choice.test/membership?play_choice='+cid);
      assert.equal(starts,1);await p.close();
    }
    console.log('PASS: SDK-choice bound checkout, locked plan/state/consent, no automatic orders, invalid/expired/plain Play fail closed, account switch blocks stale checkout, SDK result redirects only to server-bound same-origin checkout.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
