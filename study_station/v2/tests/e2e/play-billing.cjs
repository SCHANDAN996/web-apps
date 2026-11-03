const assert=require('node:assert/strict'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  for(const mode of ['pending','failed','success','cancelled','empty','unavailable']){
   const page=await browser.newPage({viewport:{width:390,height:844}});let verified=0;
   await page.route('https://billing.test/**',r=>{
    const u=new URL(r.request().url());
    if(u.pathname.endsWith('/config'))return r.fulfill({json:{enabled:true,package_name:'com.studystation.app',obfuscated_account_id:'a'.repeat(64),products:[]}});
    if(u.pathname.endsWith('/verify')){
     verified++;assert.equal(r.request().method(),'POST');assert.deepEqual(r.request().postDataJSON(),{purchase_token:'isolated-test-token-value'});
     return r.fulfill({json:{verified:true,entitled:mode==='success',acknowledged:mode==='success'}});
    }
    return r.fulfill({contentType:'text/html',body:'<html><body><section data-play-billing hidden></section></body></html>'});
   });
   await page.goto('https://billing.test');
   await page.evaluate(mode=>{
    window.renewals=0;window.purchases=0;window.SS={t:{}};
    for(const key of ['loading','restore','unavailable','buy','monthly','yearly','pending','success','verify_failed','cancelled','empty'])SS.t['play_billing_'+key]=key;
    const result=()=>mode==='cancelled'?{ok:false,error:'cancelled'}:{ok:true,purchases:mode==='empty'?[]:[{purchaseToken:'isolated-test-token-value',state:mode==='pending'?'pending':'purchased'}]};
    window.SSMembershipRenew=async()=>{renewals++;return true;};
    window.StudyStationBilling={query:async()=>({ok:true,products:mode==='unavailable'?[]:[{plan_id:'monthly',price:'₹9.00'},{plan_id:'yearly',price:'₹51.00'}]}),purchase:async()=>{purchases++;return result();},restore:async()=>result()};
   },mode);
   await page.addScriptTag({content:fs.readFileSync('app/static/js/play-billing.js','utf8')});
   await page.evaluate(()=>SSPlayBillingInit(document));
   if(mode==='unavailable'){
    await page.getByRole('status').filter({hasText:'unavailable'}).waitFor();assert.equal(await page.locator('[data-play-plan]').count(),0);
   }else{
    const buy=page.locator('[data-play-plan=monthly]');await buy.waitFor();assert.match(await buy.textContent(),/₹9\.00/);
    assert.equal(await page.evaluate(()=>purchases),0,'query must never launch checkout');
    await buy.click();
    const expected=mode==='failed'?'verify_failed':mode;
    await page.getByRole('status').filter({hasText:expected}).waitFor();
   }
   assert.equal(verified,['failed','success'].includes(mode)?1:0,'pending/cancelled/empty never verify');
   assert.equal(await page.evaluate(()=>renewals),mode==='success'?1:0,'only acknowledged backend entitlement renews access');
   if(mode==='success'){
    await page.getByRole('button',{name:'restore',exact:true}).click();await page.waitForFunction(()=>renewals===2);
    assert.equal(verified,2);
   }
   await page.close();
  }
  console.log('PASS Play UI: localized prices, explicit checkout only, pending/cancelled/failed never grant, acknowledged server entitlement renews, restore verifies existing purchases, unavailable products cannot buy.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
