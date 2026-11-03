const assert=require('node:assert/strict'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  async function fixture(hash,mode){
   const page=await browser.newPage({viewport:{width:390,height:844}});let renews=0;
   await page.route('https://lease.test/**',async r=>{
    const u=new URL(r.request().url());
    if(u.pathname==='/api/v1/membership/lease'){renews++;return r.fulfill({status:mode==='renew'?200:401,contentType:'application/json',body:JSON.stringify({lease:'signed-test-response'})});}
    if(u.pathname==='/offline-content/catalog.json')return r.fulfill({json:{subjects:[]}});
    if(u.pathname==='/offline-content/books/index.json')return r.fulfill({json:[]});
    if(u.pathname==='/offline-content/manifest.json')return r.fulfill({json:{}});
    if(u.pathname==='/static/js/offline-study.js')return r.fulfill({contentType:'text/javascript',body:fs.readFileSync('app/static/js/offline-study.js','utf8')});
    return r.fulfill({contentType:'text/html',body:`<html><head><meta name="ss-membership-required" content="true"></head><body><a class="brand"></a><section id="offlineStudy"></section><script id="ss-boot" type="application/json">{"lang":"en","t":{"membership_access_title":"Daily access check","membership_access_note":"Connect to renew your study access or sign in.","membership_access_action":"Manage access","membership_access_retry":"Try again"}}</script><script>window.testMode=${JSON.stringify(mode)};window.leaseOkay=['valid','wrong','cold'].includes(testMode);window.SSWorkspaceScope=()=>testMode==='cold'?'guest':'account:'+'a'.repeat(48);window.SSMembershipRenew=async()=>{const response=await fetch('/api/v1/membership/lease');if(!response.ok)return false;const saved=await StudyStationMembership.storeLease((await response.json()).lease);return saved.ok;};if(testMode!=='missing')window.StudyStationMembership={required:()=>true,status:async()=>({ok:leaseOkay,expiresIn:86400,namespace:(testMode==='wrong'?'b':'a').repeat(48)}),clear:async()=>{leaseOkay=false;return{ok:true};},storeLease:async()=>{leaseOkay=true;return{ok:true,expiresIn:86400}}};window.SSWorkspace={mount:r=>{r.textContent='Private workspace';}};</script><script src="/static/js/offline-study.js?v=test"></script></body></html>`});
   });
   await page.goto('https://lease.test/offline-study#'+hash);await page.waitForFunction(()=>document.querySelector('#offlineStudy').dataset.screen);
   return {page,getRenews:()=>renews};
  }
  for(const route of ['books','book/sample','chapter/sample/chapter','question/1/2','shared/2','practice','mock','revision','session','result','saved']){
   const {page}=await fixture(route,'expired');await page.getByRole('heading',{name:'Daily access check'}).waitFor();assert.equal(await page.locator('a[href="/membership"]').count(),1);await page.close();
  }
  const wrong=await fixture('books','wrong');await wrong.page.getByRole('heading',{name:'Daily access check'}).waitFor();assert.equal(await wrong.page.locator('.offline-book-search').count(),0);await wrong.page.close();
  const absent=await fixture('question/1/2','missing');await absent.page.getByRole('heading',{name:'Daily access check'}).waitFor();assert.equal(absent.getRenews(),0);await absent.page.close();
  const late=await fixture('books','missing');await late.page.getByRole('heading',{name:'Daily access check'}).waitFor();await late.page.evaluate(()=>{window.StudyStationMembership={required:()=>true,status:async()=>({ok:true,expiresIn:86400,namespace:'a'.repeat(48)})};window.dispatchEvent(new Event('ss-membership-ready'));});await late.page.locator('.offline-book-search').waitFor();assert.equal(late.getRenews(),0);await late.page.close();
  const cold=await fixture('books','cold');await cold.page.locator('.offline-book-search').waitFor();assert.equal(cold.getRenews(),0);await cold.page.evaluate(()=>window.dispatchEvent(new Event('workspace-scope-changed')));await cold.page.getByRole('heading',{name:'Daily access check'}).waitFor();await cold.page.close();
  const valid=await fixture('books','valid');await valid.page.locator('.offline-book-search').waitFor();assert.equal(valid.getRenews(),0);await valid.page.close();
  const renewed=await fixture('books','renew');await renewed.page.locator('.offline-book-search').waitFor();assert.equal(renewed.getRenews(),1);await renewed.page.close();
  const workspace=await fixture('workspace','expired');await workspace.page.getByText('Private workspace',{exact:true}).waitFor();assert.equal(workspace.getRenews(),0);assert.equal(await workspace.page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).format),'study-station-offline-backup');await workspace.page.close();
  const progress=await fixture('progress','expired');await progress.page.locator('.offline-history').waitFor({state:'attached'});assert.equal(await progress.page.getByRole('heading',{name:'Daily access check'}).count(),0);assert.equal(progress.getRenews(),0);await progress.page.close();
  console.log('PASS: study/deep-link routes gated; absent native bridge fails closed; valid lease works offline without server; renewal works; private workspace/progress/export accessible.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
