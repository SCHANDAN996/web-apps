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
 let hideQuestionIndex=false, sharedTopicRequests=[];
 await context.route('**/offline-content/question-index.json',async route=>{if(hideQuestionIndex)return route.fulfill({status:404,contentType:'application/json',body:'{}'});return route.fallback();});
 p.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/offline-content/questions/'))sharedTopicRequests.push(request.url());});
 const go=async hash=>{await p.goto('https://study-station.test/offline-study#'+hash);};
 await go('home');await p.locator('.home-image-card').first().waitFor();assert.equal(await p.locator('.home-image-card').count(),12);if(process.env.QA_SCREENSHOT_DIR)for(const theme of ['light','dark','paper']){await p.evaluate(x=>SSTheme.set(x),theme);await p.waitForTimeout(350);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'offline-home-hi-'+theme+'.png'),fullPage:true});}
 await go('books');await p.locator('.offline-list a').first().waitFor();if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(400);await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-library.png')});}await p.locator('.offline-list a').first().click();await p.locator('.offline-chapter-link').first().waitFor();if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(400);await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-chapters.png')});}await p.locator('.offline-list a').first().click();await p.locator('.offline-reader').waitFor();if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(400);await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-reader.png')});}assert.ok((await p.locator('.offline-reader').innerText()).length>100);
 await p.getByRole('button',{name:'पढ़ लिया चिह्नित करें'}).click();
 await go('practice/1');await p.getByRole('button',{name:'शुरू करें',exact:true}).click();await p.locator('.offline-card').first().evaluate(async e=>{await Promise.allSettled(e.getAnimations().map(a=>a.finished));});const actionGap=await p.locator('.offline-session-actions').evaluate(e=>e.getBoundingClientRect().top-e.previousElementSibling.getBoundingClientRect().bottom);assert.ok(actionGap>=12);await p.locator('.offline-options button').first().click();if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(400);await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-practice.png')});}await p.locator('.rough-toggle').click();assert.ok(await p.locator('canvas').isVisible());
 await p.reload();await p.locator('.offline-options [aria-pressed=true]').waitFor();
 p.on('dialog',async d=>{errors.push('Unexpected native browser popup');await d.dismiss();});await p.getByRole('button',{name:'जमा करें',exact:true}).click();await p.locator('[data-dialog-confirm]').click();await p.locator('.offline-score').waitFor();
 assert.equal(await p.locator('.offline-review-card').count(),10);assert.equal(await p.locator('.offline-review-number').first().innerText(),'सवाल 1');assert.equal(await p.locator('.offline-review-card .offline-answer-pair').count(),10);assert.equal(await p.locator('.offline-review-card .offline-solution').count(),10);assert.equal(await p.locator('.offline-answer-status[data-status=unanswered]').count(),9);
 if(process.env.QA_SCREENSHOT_DIR)for(const theme of ['light','dark']){await p.evaluate(x=>SSTheme.set(x),theme);await p.evaluate(()=>scrollTo(0,0));await p.waitForTimeout(250);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-result-hi-'+theme+'.png')});await p.locator('.offline-review-card').first().screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-review-hi-'+theme+'.png')});}
 await go('questions/1');await p.locator('.offline-list .offline-option').first().click();await p.locator('.offline-options button').first().waitFor();assert.equal(await p.locator('.offline-options [data-result]').count(),0);
 const savedId=await p.locator('[data-favorite-question]').getAttribute('data-favorite-question');await p.locator('[data-favorite-question]').click();await p.waitForFunction(async id=>await SSQuestionActions.isSaved(id),savedId);await go('saved');await p.locator('.offline-saved-question').waitFor();assert.equal(await p.locator('.offline-saved-card').count(),1);await p.reload();await p.locator('.offline-saved-question').waitFor();assert.equal(await p.locator('[data-favorite-question]').getAttribute('aria-pressed'),'true');
 const shared=await p.evaluate(()=>SSQuestionActions.payload({id:123,topic_id:1,text_hi:'सवाल',options_hi:['एक','दो'],answer_index:1,solution_hi:'SECRET_SOLUTION'},{lang:'hi'}));assert.ok(shared.text.includes('A. एक'));assert.ok(!shared.text.includes('SECRET_SOLUTION'));assert.ok(!Object.hasOwn(shared,'answer_index'));assert.match(shared.url,/\/q\/123\?lang=hi$/);
 await go('mock');await p.locator('.mock-exam-card').first().waitFor();assert.ok(await p.locator('.mock-exam-card').count()>1);assert.match(await p.locator('.mock-exam-metrics').first().innerText(),/80/);if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(350);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-mock-cards.png')});}await p.getByRole('button',{name:/SSC GD/}).click();await p.locator('.offline-options button').first().waitFor({timeout:60000});
 const active=await p.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active);assert.equal(active.ids.length,80);
 const catalog=JSON.parse(fs.readFileSync(path.join(assets,'study/catalog.json'))),byId=new Map();
 for(const subject of catalog.subjects)for(const topic of subject.topics)for(const q of JSON.parse(fs.readFileSync(path.join(assets,'study',topic.questions_path))))if(active.ids.slice(0,2).includes(q.id))byId.set(q.id,q);
 const first=byId.get(active.ids[0]),second=byId.get(active.ids[1]);
 await p.locator('.offline-options button').nth(first.answer_index).click();assert.equal(await p.locator('.offline-options [data-result]').count(),0);
 await p.getByRole('button',{name:'अगला',exact:true}).click();await p.locator('.offline-options button').nth((second.answer_index+1)%(second.options_hi||second.options_en).length).click();
 await p.locator('.offline-palette button').nth(11).click();
 await p.waitForFunction(()=>{var a=document.querySelector('.offline-palette [aria-current]'),n=a&&a.parentElement,r=a&&a.getBoundingClientRect(),b=n&&n.getBoundingClientRect();return a&&a.textContent==='12'&&r.left>=b.left-1&&r.right<=b.right+1&&n.scrollLeft>0;});
 await p.reload();await p.waitForFunction(()=>{var a=document.querySelector('.offline-palette [aria-current]'),r=a&&a.getBoundingClientRect(),b=a&&a.parentElement.getBoundingClientRect();return a&&a.textContent==='12'&&r.left>=b.left-1&&r.right<=b.right+1;});
 await p.locator('.offline-palette button').nth(1).click();await p.locator('.offline-options [aria-pressed=true]').waitFor();

 await p.reload();await p.locator('.offline-options [aria-pressed=true]').waitFor();assert.ok((await p.getByRole('timer').innerText()).length>0);await p.getByRole('button',{name:'जमा करें',exact:true}).click();await p.locator('[data-dialog-confirm]').click();await p.locator('.offline-score').waitFor();assert.equal(await p.locator('.offline-score').innerText(),'1.75 / 160');assert.equal(await p.locator('.offline-review-card').count(),80);assert.equal(await p.locator('.offline-review-card[data-status=correct]').count(),1);assert.equal(await p.locator('.offline-review-card[data-status=incorrect]').count(),1);assert.equal(await p.locator('.offline-review-card[data-status=unanswered]').count(),78);
 await go('settings');await p.locator('.offline-stack').first().waitFor();
 const settingsGaps=await p.locator('#offlineStudy[data-screen="settings"]').evaluate(async root=>{
  await Promise.allSettled(root.getAnimations({subtree:true}).map(animation=>animation.finished));
  const blocks=Array.from(root.children).filter(element=>element.matches('a.btn,button,.offline-card,.offline-stack')&&element.getBoundingClientRect().height>0);
  return blocks.slice(1).map((element,index)=>({before:blocks[index].tagName,after:element.tagName,gap:element.getBoundingClientRect().top-blocks[index].getBoundingClientRect().bottom}));
 });
 assert.ok(settingsGaps.length>=3,'Settings must include direct actions and cards');
 for(const pair of settingsGaps)assert.ok(pair.gap>=12,`Offline Settings ${pair.before}/${pair.after} gap ${pair.gap}px is below 12px`);
 const backup=await p.evaluate(()=>SSOffline.exportBackup());assert.equal(JSON.parse(backup).favorites.length,1);
 await p.getByRole('button',{name:'पुराना progress इस मोबाइल में लाएँ · ऑनलाइन',exact:true}).click();await p.locator('dialog.ss-dialog[open]').waitFor();assert.equal(await p.locator('[data-dialog-cancel]').evaluate(e=>e===document.activeElement),true);if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(350);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-popup-import.png')});}await p.keyboard.press('Escape');assert.deepEqual(JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress,JSON.parse(backup).progress);await p.locator('[data-choice-trigger="reset_scope"]').click();await p.locator('[data-choice-value="all"]').click();await p.getByRole('button',{name:'Progress reset करें',exact:true}).click();if(process.env.QA_SCREENSHOT_DIR){await p.waitForTimeout(350);await p.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'ui-popup-reset.png')});}await p.locator('[data-dialog-cancel]').click();assert.deepEqual(JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress,JSON.parse(backup).progress);await p.getByRole('button',{name:'Progress reset करें',exact:true}).click();await p.locator('[data-dialog-confirm]').click();await p.reload();await p.locator('.offline-stack').first().waitFor();assert.equal(JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress.history.length,0);assert.equal(await p.evaluate(async()=> (await SSQuestionActions.list()).length),1);
 await p.locator('input[type=file]').setInputFiles({name:'restore.json',mimeType:'application/json',buffer:Buffer.from(backup)});await p.locator('[data-dialog-confirm]').click();await p.waitForFunction(()=>JSON.parse(SSOffline.exportBackup()).progress.history.length===2);assert.equal(await p.evaluate(async()=> (await SSQuestionActions.list()).length),1);
 await p.goto('https://study-station.test/offline-study?lang=en');await p.locator('.home-image-card').first().waitFor();assert.equal((await p.locator('#langBtn').innerText()).trim(),'HI');
 for(const width of [360,412])for(const theme of ['light','dark','paper']){await p.setViewportSize({width,height:800});await p.evaluate(x=>SSTheme.set(x),theme);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 // App links must resolve directly with one topic, without submitting an answer.
 const beforeShared=JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress;
 for(const lang of ['hi','en']){sharedTopicRequests=[];await p.goto('https://study-station.test/offline-study?lang='+lang+'#shared/'+first.id);await p.locator('.offline-options button').first().waitFor();assert.equal(await p.evaluate(()=>SS.lang),lang);assert.equal(sharedTopicRequests.length,1);assert.equal(await p.locator('.offline-options [data-result]').count(),0);assert.deepEqual(JSON.parse(await p.evaluate(()=>SSOffline.exportBackup())).progress.answers,beforeShared.answers);}
 for(const id of ['0','abc','001','999999999999999','1/extra']){sharedTopicRequests=[];await go('shared/'+id);await p.locator('.offline-alert').first().waitFor();assert.equal(await p.locator('.offline-options').count(),0);assert.equal(sharedTopicRequests.length,0);}
 hideQuestionIndex=true;await go('shared/'+first.id);await p.getByText('SS-'+first.id,{exact:true}).waitFor();assert.equal(await p.locator('.offline-options').count(),0);hideQuestionIndex=false;
 const nativeSource=fs.readFileSync(path.join(root,'android/app/src/main/java/com/studystation/app/OfflineStudy.kt'),'utf8');
 const nativeNavigation=/val navigationScript = """([\s\S]*?)"""\.trimIndent/.exec(nativeSource)[1];
 await context.route('**/jobs',r=>r.fulfill({contentType:'text/html',body:'<a href="/">Home</a>'}));
 await p.goto('https://study-station.test/jobs');await p.evaluate(nativeNavigation);await p.getByRole('link',{name:'Home',exact:true}).click();await p.locator('.home-image-card').first().waitFor();assert.match(p.url(),/offline-study#home$/);
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);console.log('PASS: offline reader, exact question access, practice/rough work/resume, 80-question mock/negative marking/timer state, reset/restore, EN and themes; zero server requests.');
} finally {await browser.close();}
