const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_PATH || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 for(const mode of ['website','native-bridge','native-ua','play-false','native-string','direct','direct-late']){
  const native=mode!=='website';
  const checkoutAllowed=!native||mode==='direct'||mode==='direct-late';
  const context=await browser.newContext({viewport:{width:360,height:740},
    ...(native?{userAgent:'Mozilla/5.0 Android WebView StudyStationApp/1.3.0'}:{})});
  await context.addCookies([{name:'ss_lang',value:'en',url:'http://127.0.0.1:8773'}]);
  const page=await context.newPage();let orders=0;
  if(mode==='native-bridge')await page.addInitScript(()=>{window.StudyStationAuth={configured:()=>true};});
  await page.addInitScript(selected=>{
   const policy=selected==='direct'||(selected==='direct-late'&&sessionStorage.getItem('test-direct-ready')==='1');
   if(policy||selected==='play-false'||selected==='native-string')Object.defineProperty(window,'StudyStationMembership',{value:Object.freeze({allowPayu:()=>selected==='native-string'?'true':policy,required:()=>false,openPayuWebsite:()=>{window.externalPayuOpened=(window.externalPayuOpened||0)+1;return Promise.resolve({ok:true});}}),configurable:false});
  },mode);
  if(checkoutAllowed)await page.addInitScript(()=>{HTMLFormElement.prototype.submit=function(){window.sentCheckout={action:this.action,method:this.method,fields:Array.from(this.elements).map(x=>x.name)};};});
  await page.route('**/api/v1/payments/payu/config',route=>route.fulfill({json:{enabled:true,channel:'website',auto_renew:false}}));
  await page.route('**/api/v1/payments/payu/orders',route=>{orders++;const d=route.request().postDataJSON();assert.equal(d.contact_consent,true);assert.equal(d.plan_id,'monthly');return route.fulfill({json:{action_url:'https://test.payu.in/_payment',fields:{key:'not-real-key',txnid:'SS_test',amount:'9.00',hash:'not-real-hash'}}});});
  const signup=await context.request.post('http://127.0.0.1:8773/api/v1/classroom/signup',{data:{username:'payui'+Date.now(),password:'only-local-ui-tests'}});assert.equal(signup.status(),200);
  const home=await page.goto('http://127.0.0.1:8773/');
  assert.match(home.headers()['content-security-policy'],/form-action 'self';/);
  await page.waitForFunction(()=>window.SS&&window.SS.go);
  await page.evaluate(()=>{window.beforeMembershipDocument=true;const link=document.createElement('a');link.id='test-membership-link';link.href='/membership';link.textContent='Membership';document.getElementById('main').prepend(link);});
  if(!native||mode==='direct'){
   const documentResponse=page.waitForResponse(r=>r.request().isNavigationRequest()&&new URL(r.url()).pathname==='/membership');
   await page.locator('#test-membership-link').click();
   const membershipResponse=await documentResponse;
   assert.match(membershipResponse.headers()['content-security-policy'],/form-action 'self' https:\/\/secure\.payu\.in https:\/\/test\.payu\.in/);
   await page.waitForURL('**/membership');
   assert.equal(await page.evaluate(()=>window.beforeMembershipDocument),undefined,'Website/direct membership must replace document');
  }else{
   await page.locator('#test-membership-link').click();await page.waitForURL('**/membership');
   assert.equal(await page.evaluate(()=>window.beforeMembershipDocument),true,'Native navigation keeps frame');
   if(mode==='native-ua')assert.equal(await page.evaluate(()=>!!window.StudyStationAuth),false);
  }
  if(mode==='direct-late'){
   await page.locator('[data-membership-start]').waitFor({state:'visible'});
   assert.equal(await page.locator('[data-membership-checkout] form').count(),0);
   assert.equal(orders,0);
   await page.evaluate(()=>{Object.defineProperty(window,'StudyStationMembership',{value:Object.freeze({allowPayu:()=>true,required:()=>false,openPayuWebsite:()=>{window.externalPayuOpened=(window.externalPayuOpened||0)+1;return Promise.resolve({ok:true});}}),configurable:false});window.dispatchEvent(new Event('ss-membership-ready'));window.dispatchEvent(new Event('ss-membership-ready'));});
  }
  if(checkoutAllowed&&native){
   const slot=page.locator('[data-membership-checkout]');await slot.locator('button').first().waitFor();
   assert.equal(await slot.locator('form').count(),0,'Direct APK must use external website, never hosted form');
   assert.equal(await slot.locator('button').count(),2);
   await page.evaluate(()=>{window.SSMembershipRenew=async()=>{window.testLeaseRenewals=(window.testLeaseRenewals||0)+1;return true;};window.dispatchEvent(new Event('ss-membership-ready'));window.dispatchEvent(new Event('ss-membership-ready'));});
   assert.equal(await slot.locator('button').count(),2,'Repeated ready events must not duplicate controls');
   await page.screenshot({path:'C:/Users/Admin/AppData/Local/Temp/ss-direct-payu-external.png',fullPage:true});
   await slot.locator('button').first().click();
   assert.equal(await page.evaluate(()=>window.externalPayuOpened),1);
   assert.equal(orders,0,'Opening external website must not create orders or send login tokens');
   await slot.locator('button').last().click();await page.waitForFunction(()=>window.testLeaseRenewals===1);
   await page.evaluate(()=>window.dispatchEvent(new Event('ss-payu-return')));
   await page.waitForFunction(()=>window.testLeaseRenewals===2);
  }
  else if(!checkoutAllowed){await page.locator('[data-membership-start]').waitFor({state:'visible'});assert.equal(await page.locator('[data-membership-checkout] button').count(),0);assert.equal(orders,0);}
  else {
   const form=page.locator('[data-membership-checkout] form');await form.waitFor();
   await page.evaluate(()=>{window.dispatchEvent(new Event('ss-membership-ready'));window.dispatchEvent(new Event('ss-membership-ready'));});
   assert.equal(await form.count(),1,'Repeated native ready events must not duplicate checkout');
   assert.equal(orders,0,'Opening checkout never creates a payment order');
   await form.locator('[name=name]').fill('Local Test');await form.locator('[name=email]').fill('local@example.com');await form.locator('[name=phone]').fill('9876543210');
   await form.locator('button').click();assert.equal(orders,0,'Consent must be explicit');
   await form.locator('[name=contact_consent]').check();await form.locator('button').click();
   await page.waitForFunction(()=>!!window.sentCheckout);const sent=await page.evaluate(()=>window.sentCheckout);
   assert.equal(sent.action,'https://test.payu.in/_payment');assert.equal(sent.method,'post');assert.equal(orders,1);
   assert.equal(await page.evaluate(()=>localStorage.getItem('email')),null);
   await page.screenshot({path:'C:/Users/Admin/AppData/Local/Temp/ss-membership-checkout.png',fullPage:true});
  }
  await context.close();
 }
 console.log('PASS browser CSP/consent/form; direct APK external-only native handoff/manual and return refresh/late bridge; Play and unknown flags hidden; no duplicate controls, real orders or provider request');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
