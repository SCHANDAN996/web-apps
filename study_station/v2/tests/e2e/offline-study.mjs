import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const root=process.cwd(),assets=path.join(root,'android/app/src/main/assets');
if(!fs.existsSync(path.join(assets,'study/manifest.json')))throw Error('Generate the public study pack first.');
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
try {
 const context=await browser.newContext({viewport:{width:360,height:800}}),p=await context.newPage(),errors=[],network=[];
 p.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',async route=>{
  const u=new URL(route.request().url());let file;
  if(u.pathname==='/offline-study')file=path.join(assets,'offline',u.searchParams.get('lang')==='en'?'en.html':'hi.html');
  else if(u.pathname.startsWith('/offline-content/'))file=path.join(assets,'study',u.pathname.slice(17));
  else if(u.pathname.startsWith('/static/'))file=path.join(root,'app/static',u.pathname.slice(8));
  if(!file||!fs.existsSync(file)){network.push(u.pathname);return route.abort();}
  const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'};
  return route.fulfill({body:fs.readFileSync(file),contentType:types[path.extname(file)]||'application/octet-stream'});
 });
 const go=async hash=>{await p.goto('https://study-station.test/offline-study#'+hash);};
 await go('home');await p.locator('.home-image-card').first().waitFor();assert.equal(await p.locator('.home-image-card').count(),8);if(process.env.QA_SCREENSHOT_DIR)for(const theme of ['light','dark','paper']){await p.evaluate(x=>SSTheme.set(x),theme);await p.waitForTimeout(350);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'offline-home-hi-'+theme+'.png'),fullPage:true});}
 await go('books');await p.locator('.offline-list a').first().click();await p.locator('.offline-list a').first().click();await p.locator('.offline-reader').waitFor();assert.ok((await p.locator('.offline-reader').innerText()).length>100);
 await p.getByRole('button',{name:'पढ़ लिया चिह्नित करें'}).click();
 await go('practice/1');await p.getByRole('button',{name:'शुरू करें',exact:true}).click();await p.locator('.offline-options button').first().click();await p.locator('.rough-toggle').click();assert.ok(await p.locator('canvas').isVisible());
 await p.reload();await p.locator('.offline-options [aria-pressed=true]').waitFor();
 p.on('dialog',d=>d.accept());await p.getByRole('button',{name:'जमा करें',exact:true}).click();await p.locator('.offline-score').waitFor();
 await go('questions/1');await p.locator('.offline-list .offline-option').first().click();await p.locator('.offline-options button').first().waitFor();assert.equal(await p.locator('.offline-options [data-result]').count(),0);
 await go('mock');await p.locator('main button').filter({hasText:'SSC GD'}).click();await p.locator('.offline-options button').first().waitFor({timeout:60000});
 const active=await p.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active);assert.equal(active.ids.length,80);
 const catalog=JSON.parse(fs.readFileSync(path.join(assets,'study/catalog.json'))),byId=new Map();
 for(const subject of catalog.subjects)for(const topic of subject.topics)for(const q of JSON.parse(fs.readFileSync(path.join(assets,'study',topic.questions_path))))if(active.ids.slice(0,2).includes(q.id))byId.set(q.id,q);
 const first=byId.get(active.ids[0]),second=byId.get(active.ids[1]);
 await p.locator('.offline-options button').nth(first.answer_index).click();assert.equal(await p.locator('.offline-options [data-result]').count(),0);
 await p.getByRole('button',{name:'अगला',exact:true}).click();await p.locator('.offline-options button').nth((second.answer_index+1)%(second.options_hi||second.options_en).length).click();
 await p.reload();await p.locator('.offline-options [aria-pressed=true]').waitFor();assert.ok((await p.getByRole('timer').innerText()).length>0);await p.getByRole('button',{name:'जमा करें',exact:true}).click();await p.locator('.offline-score').waitFor();assert.equal(await p.locator('.offline-score').innerText(),'1.75 / 160');
 await go('settings');await p.locator('.offline-stack').first().waitFor();const backup=await p.evaluate(()=>SSOffline.exportBackup());
 await p.locator('select[aria-label="क्या reset करें"]').selectOption('all');await p.getByRole('button',{name:'Progress reset करें',exact:true}).click();await p.reload();await p.locator('.offline-stack').first().waitFor();assert.equal(JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress.history.length,0);
 await p.locator('input[type=file]').setInputFiles({name:'restore.json',mimeType:'application/json',buffer:Buffer.from(backup)});await p.waitForFunction(()=>JSON.parse(SSOffline.exportBackup()).progress.history.length===2);
 await p.goto('https://study-station.test/offline-study?lang=en');await p.locator('.home-image-card').first().waitFor();assert.equal((await p.locator('#langBtn').innerText()).trim(),'HI');
 for(const width of [360,412])for(const theme of ['light','dark','paper']){await p.setViewportSize({width,height:800});await p.evaluate(x=>SSTheme.set(x),theme);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);console.log('PASS: offline reader, exact question access, practice/rough work/resume, 80-question mock/negative marking/timer state, reset/restore, EN and themes; zero server requests.');
} finally {await browser.close();}
