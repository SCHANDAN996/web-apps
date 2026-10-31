import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const browser = await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL || 'chrome',headless:true});
try {
  const page = await browser.newPage();
  await page.route('https://favorites.test/**',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><body></body>'}));
  await page.goto('https://favorites.test/');
  await page.addScriptTag({content:await readFile(new URL('../../app/static/js/question-actions.js',import.meta.url),'utf8')});
  const result = await page.evaluate(async()=>{
    const question={id:123,topic_id:'math/fractions',text_en:'Choose a fraction',options_en:['1/2','2/3'],answer_index:1,solution_en:'SECRET_SOLUTION',private:'SECRET_PRIVATE'};
    const events=[]; addEventListener('ss-question-favorites-changed',event=>events.push(event.detail));
    const saved=await SSQuestionActions.toggle(question,{lang:'en'});
    const records=await SSQuestionActions.list();
    const state=await SSQuestionActions.isSaved(123);
    const payload=SSQuestionActions.payload(question,{lang:'en'});
    const row=SSQuestionActions.render(question,{lang:'en'});document.body.append(row);
    await new Promise(resolve=>setTimeout(resolve,30));
    const pressed=row.querySelector('button').getAttribute('aria-pressed');
    const removed=await SSQuestionActions.toggle(question,{lang:'en'});
    return {saved,records,state,payload,pressed,removed,remaining:await SSQuestionActions.list(),events,icons:row.querySelectorAll('svg[aria-hidden=true]').length,labels:Array.from(row.querySelectorAll('button')).map(b=>b.getAttribute('aria-label'))};
  });
  assert.equal(result.icons,2);assert.ok(result.labels.every(Boolean));
  assert.equal(result.saved,true);assert.equal(result.state,true);assert.equal(result.pressed,'true');
  assert.deepEqual(Object.keys(result.records[0]).sort(),['id','lang','savedAt','topicId','version']);
  assert.equal(result.records[0].topicId,'math/fractions');
  assert.equal(result.payload.url,'https://studystation.ebookcart.in/q/123?lang=en');
  assert.match(result.payload.text,/A\. 1\/2\nB\. 2\/3/);
  assert.doesNotMatch(JSON.stringify(result),/SECRET_SOLUTION|SECRET_PRIVATE|answer_index/);
  assert.equal(result.removed,false);assert.equal(result.remaining.length,0);
  assert.deepEqual(result.events,[{id:'123',saved:true},{id:'123',saved:false}]);
  const backup = await page.evaluate(async()=>{
    const rows=[{version:1,id:'456',topicId:'math/fractions',lang:'hi',savedAt:123456}];
    await SSQuestionActions.restoreRecords(rows.concat(rows));
    await SSQuestionActions.restoreRecords(rows);
    const before=JSON.stringify(await SSQuestionActions.list());let rejected=0;
    for(const invalid of [rows.concat([{...rows[0],answer_index:0}]),[{...rows[0],topicId:'<script>'}],[{...rows[0],savedAt:-1}],Array(5001).fill(rows[0])]) {
      try { await SSQuestionActions.restoreRecords(invalid); } catch (_) { rejected++; }
    }
    const after=JSON.stringify(await SSQuestionActions.exportRecords());
    return {before,after,rejected,snapshot:SSQuestionActions.exportSnapshot()};
  });
  assert.equal(backup.rejected,4);assert.equal(backup.before,backup.after);assert.equal(backup.snapshot.length,1);
  const nativeShare = await page.evaluate(async()=>{
    let sent;
    window.SSNativeShare={shareQuestion:async data=>{sent=data;return {ok:true};}};
    const ok=await SSQuestionActions.share({id:123,text_en:'Public question',options_en:['One','Two'],answer_index:1,solution_en:'PRIVATE_NATIVE_SOLUTION'},{lang:'en'});
    delete window.SSNativeShare;
    return {ok,sent};
  });
  assert.equal(nativeShare.ok,true);
  assert.deepEqual(Object.keys(nativeShare.sent).sort(),['id','lang','options','question']);
  assert.doesNotMatch(JSON.stringify(nativeShare),/answer_index|PRIVATE_NATIVE_SOLUTION/);
  await page.reload();
  await page.addScriptTag({content:await readFile(new URL('../../app/static/js/question-actions.js',import.meta.url),'utf8')});
  assert.equal(await page.evaluate(async()=>{await SSQuestionActions.ready();return SSQuestionActions.exportSnapshot()[0].id;}),'456');
  console.log('Question actions: favorites persistence, state, events and answer-free sharing passed.');
} finally { await browser.close(); }
