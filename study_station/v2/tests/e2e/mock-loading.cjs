// Deterministic local-file latency: mock reads overlap, remain bounded, and cancel on leave.
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
 try {
  const context=await browser.newContext({viewport:{width:360,height:800}}),page=await context.newPage();
  const root=process.cwd(),assets=path.join(root,'android/app/src/main/assets');
  let active=0,peak=0,reads=0;
  const topics=Array.from({length:12},(_,i)=>({id:i+1,slug:'topic-'+i,name_hi:'विषय '+i,question_count:25}));
  const catalog={subjects:[{id:1,slug:'quant',name_hi:'गणित',topics}],exams:[{id:1,body:'SSC',name_hi:'जाँच मॉक',stage_en:'Test',level:'10th',duration_min:60,sections:[{subject_id:1,questions:80,marks_per_q:2,negative_per_q:0.5}]}]};
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());let data,file;
   if(u.pathname==='/offline-content/catalog.json')data=catalog;
   else if(u.pathname==='/offline-content/books/index.json')data=[];
   else if(u.pathname==='/offline-content/manifest.json')data={version:1};
   else if(/^\/offline-content\/questions\/\d+\.json$/.test(u.pathname)){
    const topic=Number(path.basename(u.pathname,'.json'));reads++;peak=Math.max(peak,++active);
    await new Promise(resolve=>setTimeout(resolve,100));active--;
    data=Array.from({length:25},(_,i)=>({id:topic*100+i,topic_id:topic,level:'10th',text_hi:'सवाल '+topic+' '+i,options_hi:['क','ख','ग','घ'],answer_index:1,solution_hi:'हल'}));
   } else if(u.pathname==='/offline-study')file=path.join(assets,'offline/hi.html');
   else if(u.pathname.startsWith('/static/'))file=path.join(root,'app',u.pathname);
   if(data!==undefined)return route.fulfill({json:data});
   if(!file||!fs.existsSync(file))return route.fulfill({status:404,body:''});
   if(process.env.MOCK_BASELINE&&u.pathname==='/static/js/offline-study.js')file=process.env.MOCK_BASELINE;
   const type={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'}[path.extname(file)]||'application/octet-stream';
   return route.fulfill({body:fs.readFileSync(file),contentType:type});
  });
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('https://mock.test/offline-study#mock');await page.locator('.mock-exam-start').waitFor();
  const start=Date.now();await page.locator('.mock-exam-start').click();
  if(!process.env.MOCK_BASELINE){assert.equal(await page.locator('.mock-exam-start').getAttribute('aria-busy'),'true');}
  await page.locator('.offline-options button').first().waitFor();
  const elapsed=Date.now()-start;
  assert.equal(await page.locator('.offline-palette button').count(),80);
  if(process.env.QA_SCREENSHOT_DIR)await page.locator('.question-actions').evaluate(el=>el.scrollIntoView({block:'center'}));
  if(process.env.QA_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'question-tools.png'),fullPage:false});
  if(!process.env.MOCK_BASELINE){assert.equal(await page.locator('.question-tools-group button').count(),3);}
  const state=await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active);
  assert.equal(new Set(state.ids).size,80);
  assert.ok(Object.values(state.rules).every(r=>r.marks===2&&r.negative===0.5));
  if(!process.env.MOCK_BASELINE){assert.equal(peak,4);assert.equal(reads,12);}
  console.log(JSON.stringify({mockStartMs:elapsed,topicReads:reads,peakConcurrentReads:peak,questions:80}));
  // Leaving mid-build must neither start a hidden mock nor issue further batches.
  await page.goto('https://mock.test/offline-study#mock');await page.locator('.mock-exam-start').waitFor();
  const beforeCancel=await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active), readsBeforeCancel=reads;
  await page.locator('.mock-exam-start').click();await page.evaluate(()=>{location.hash='#home';});
  await page.locator('#offlineStudy[data-screen="home"]').waitFor();await page.waitForTimeout(450);
  assert.equal(await page.evaluate(()=>location.hash),'#home');
  assert.deepEqual(await page.evaluate(()=>JSON.parse(SSOffline.exportBackup()).progress.active),beforeCancel);
  assert.ok(reads-readsBeforeCancel<=4);assert.deepEqual(errors,[]);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
