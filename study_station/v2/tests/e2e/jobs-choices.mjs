import {createRequire} from 'node:module';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url),{chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const base=process.env.BASE_URL||'http://127.0.0.1:8012';
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
try {
 const context=await browser.newContext({viewport:{width:384,height:771},isMobile:true,hasTouch:true});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const open=async name=>{await page.locator(`[data-choice-trigger="jobs_${name}"]`).click();await page.locator('dialog.choice-dialog[open]').waitFor();};
 const choose=async(name,value)=>{await open(name);await page.locator(`[data-choice-value="${value}"]`).click();};
 for(const lang of ['hi','en']) {
  await context.addCookies([{name:'ss_lang',value:lang,url:base}]);
  await page.goto(base+'/jobs?status=active&qualification=all');await page.locator('[data-choice-trigger="jobs_category"]').waitFor();
  assert.equal(await page.locator('#jobFilters [data-choice-trigger]').count(),2);
  for(const viewport of [{width:384,height:771},{width:788,height:344}])for(const theme of ['light','dark','paper']) {
   await page.setViewportSize(viewport);await page.evaluate(t=>SSTheme.set(t),theme);await open('category');
   await page.locator('[data-choice-value]').last().scrollIntoViewIfNeeded();
   const rect=await page.locator('[data-choice-value]').last().evaluate(e=>({bottom:e.getBoundingClientRect().bottom,listBottom:e.parentElement.getBoundingClientRect().bottom,dialogBottom:e.closest('dialog').getBoundingClientRect().bottom,viewport:innerHeight}));
   assert.ok(rect.bottom<=rect.listBottom+1&&rect.dialogBottom<=rect.viewport-8,JSON.stringify(rect));
   if(process.env.QA_SCREENSHOT_DIR&&theme==='light')await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,`jobs-choice-${lang}-${viewport.width}.png`)});
   await page.keyboard.press('Escape');assert.equal(await page.locator('[data-choice-trigger="jobs_category"]').evaluate(e=>e===document.activeElement),true);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  }
 }
 await open('category');await page.locator('[data-choice-search]').fill('NO_SUCH_CATEGORY_123');assert.equal(await page.locator('[data-choice-value]').count(),0);await page.locator('[data-choice-cancel]').click();
 await choose('qualification','graduate');await choose('category','ssc');await page.locator('#jobFilters [type=submit]').click();
 await page.waitForURL(u=>u.searchParams.get('qualification')==='graduate'&&u.searchParams.get('category')==='ssc');await page.locator('[data-choice-trigger="jobs_category"]').waitFor();
 assert.equal(new URL(page.url()).searchParams.get('status'),'active');assert.equal(await page.locator('#jobFilters [data-choice-trigger]').count(),2);
 assert.equal(await page.locator('select[name=qualification]').inputValue(),'graduate');assert.equal(await page.locator('select[name=category]').inputValue(),'ssc');
 await choose('category','');await choose('qualification','all');await page.locator('#jobFilters [type=submit]').click();
 await page.waitForURL(u=>u.searchParams.get('qualification')==='all'&&u.searchParams.get('category')==='');await page.locator('[data-choice-trigger="jobs_category"]').waitFor();
 await page.goBack();await page.locator('[data-choice-trigger="jobs_category"]').waitFor();assert.equal(await page.locator('#jobFilters [data-choice-trigger]').count(),2);assert.equal(await page.locator('dialog[open]').count(),0);
 assert.deepEqual(errors,[]);console.log('Jobs custom choices: themes/languages, scrolling, search/cancel, filter values/All, SPA cleanup and history passed.');
} finally {await browser.close();}
