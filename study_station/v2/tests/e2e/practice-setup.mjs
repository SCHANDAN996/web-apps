import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url),{chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const assets=path.join(process.cwd(),'android/app/src/main/assets');
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
try {
 const context=await browser.newContext({viewport:{width:412,height:915},isMobile:true,hasTouch:true}),page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));let failTopic=false;
 await context.route('**/*',async route=>{
  const u=new URL(route.request().url());let file;
  if(failTopic&&u.pathname.startsWith('/offline-content/questions/'))return route.fulfill({status:503,body:'Unavailable'});
  if(u.pathname==='/offline-study')file=path.join(assets,'offline',u.searchParams.get('lang')==='en'?'en.html':'hi.html');
  else if(u.pathname.startsWith('/offline-content/'))file=path.join(assets,'study',u.pathname.slice(17));
  else if(u.pathname.startsWith('/static/'))file=path.join(process.cwd(),'app/static',u.pathname.slice(8));
  if(!file||!fs.existsSync(file))throw Error('Unexpected network request: '+u.pathname);
  const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'};
  await route.fulfill({body:fs.readFileSync(file),contentType:types[path.extname(file)]||'application/octet-stream'});
 });
 for(const lang of ['hi','en']) {
  await page.goto('https://practice.test/offline-study?lang='+lang+'#practice/1');
  await page.locator('[data-practice-start]').waitFor();
  for(const widthHeight of [[360,740],[412,915],[844,330]]) {
   await page.setViewportSize({width:widthHeight[0],height:widthHeight[1]});
   const header=await page.evaluate(()=>({gap:parseFloat(getComputedStyle(document.querySelector('.top-actions')).gap),controls:Array.from(document.querySelectorAll('#langBtn,.theme-picker > summary,.top-actions > a')).map(e=>{const r=e.getBoundingClientRect();return {width:r.width,height:r.height,right:r.right};})}));
   assert.equal(header.gap,4);assert.ok(header.controls.every(r=>r.width>=44&&r.height>=44&&r.right<=widthHeight[0]));
   for(const theme of ['light','dark','paper']) {
    await page.evaluate(x=>SSTheme.set(x),theme);
    const start=page.locator('[data-practice-start]');await start.scrollIntoViewIfNeeded();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    const geometry=await start.evaluate(el=>{const r=el.getBoundingClientRect(),n=document.querySelector('.tabbar').getBoundingClientRect();return {top:r.top,bottom:r.bottom,nav:n.top,height:r.height};});
    assert.ok(geometry.height>=44);assert.ok(geometry.top>=0&&geometry.bottom<=geometry.nav+1,JSON.stringify({lang,widthHeight,theme,geometry}));
    if(process.env.QA_SCREENSHOT_DIR&&theme==='light')await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,`practice-setup-${lang}-${widthHeight[0]}.png`)});
   }
  }
 }
 await page.goto('https://practice.test/offline-study?lang=en#practice/1');await page.locator('[data-practice-start]').waitFor();
 await page.locator('[data-practice-count="50"]').click();assert.equal(await page.locator('[data-practice-count="50"]').getAttribute('aria-pressed'),'true');
 await page.setViewportSize({width:412,height:915});assert.equal(await page.locator('[data-practice-count="50"]').getAttribute('aria-pressed'),'true');
 const choose=async(key,value)=>{await page.locator(`[data-choice-trigger="${key}"]`).click();await page.locator(`[data-choice-value="${value}"]`).click();};
 await page.locator('[data-choice-trigger="subject"]').click();
 assert.equal(await page.locator('[data-choice-trigger="subject"]').getAttribute('aria-expanded'),'true');
 assert.equal(await page.locator('[data-choice-search]').evaluate(e=>e===document.activeElement),false);
 if(process.env.QA_SCREENSHOT_DIR){
  await page.setViewportSize({width:412,height:915});await page.evaluate(()=>SSTheme.set('light'));
  await page.locator('dialog.choice-dialog').evaluate(async e=>{await Promise.allSettled(e.getAnimations().map(a=>a.finished));});
  await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'practice-choice-portrait.png')});
  await page.setViewportSize({width:844,height:330});await page.evaluate(()=>SSTheme.set('dark'));
  await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'practice-choice-landscape-dark.png')});await page.evaluate(()=>SSTheme.set('light'));
 }
 await page.locator('[data-choice-search]').fill('NO_SUCH_SUBJECT_123');await page.getByText('No options found',{exact:true}).waitFor();
 await page.keyboard.press('Escape');assert.equal(await page.locator('[data-choice-trigger="subject"]').evaluate(e=>e===document.activeElement),true);
 await choose('subject','2');assert.equal(await page.locator('[data-practice-start]').isDisabled(),true);
 await choose('subject','1');assert.equal(await page.locator('[data-practice-start]').isDisabled(),true);
 await page.locator('[data-choice-trigger="topic"]').click();
 await page.locator('[data-choice-value]').last().scrollIntoViewIfNeeded();
 const lastChoice=await page.locator('[data-choice-value]').last().evaluate(e=>({bottom:e.getBoundingClientRect().bottom,listBottom:e.parentElement.getBoundingClientRect().bottom,dialogBottom:e.closest('dialog').getBoundingClientRect().bottom,viewport:innerHeight}));
 assert.ok(lastChoice.bottom<=lastChoice.listBottom+1&&lastChoice.dialogBottom<=lastChoice.viewport-8,JSON.stringify(lastChoice));
 await page.locator('[data-choice-cancel]').click();
 await choose('topic','1');await page.locator('[data-practice-count="20"]').click();
 failTopic=true;await page.reload();await page.getByText('Questions could not load. Try again.',{exact:true}).waitFor();
 assert.equal(await page.locator('[data-practice-start]').isDisabled(),true);failTopic=false;
 await page.locator('[data-practice-retry]').click();await page.locator('[data-practice-count="20"]').click();
 await page.locator('[data-practice-start]').click();await page.locator('.offline-options').waitFor();
 assert.equal(await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active.ids.length),20);
 await page.evaluate(()=>location.hash='#practice/1');await page.locator('[data-practice-start]').waitFor();
 await page.setViewportSize({width:412,height:915});
 const resumeHeading=await page.locator('.practice-resume strong').evaluate(e=>({height:e.getBoundingClientRect().height,lineHeight:parseFloat(getComputedStyle(e).lineHeight)}));
 assert.ok(resumeHeading.height<=resumeHeading.lineHeight*2+1);
 if(process.env.QA_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'practice-resume-portrait.png')});
 await page.locator('[data-practice-start]').click();await page.locator('[data-dialog-cancel]').click();
 assert.equal(await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active.ids.length),20);
 await page.getByRole('button',{name:'Resume',exact:true}).click();await page.locator('.offline-options').waitFor();
 assert.equal(await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active.ids.length),20);
 assert.deepEqual(errors,[]);console.log('Practice setup: portrait/landscape themes, reachable Start, count selection, empty state, retry, resume passed.');
} finally {await browser.close();}
