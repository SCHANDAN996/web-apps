import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const source=await readFile(new URL('../../android/app/src/main/java/com/studystation/app/QuestionShareBridge.kt',import.meta.url),'utf8');
const script=/private val script = """([\s\S]*?)"""\.trimIndent/.exec(source)[1];
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
try {
  const p=await browser.newPage();
  await p.route('https://native-share.test/**',r=>r.fulfill({contentType:'text/html',body:'<button id="share">Share question</button>'}));
  await p.goto('https://native-share.test/');
  const cdp=await p.context().newCDPSession(p);
  await cdp.send('Runtime.evaluate',{userGesture:false,expression:`
    window.requests=[];
    window.SSQuestionShareNative={postMessage(text){requests.push(JSON.parse(text));setTimeout(()=>SSQuestionShareNative.onmessage({data:JSON.stringify({ok:true})}),10);}};
    ${script}
  `});
  const inactive=await cdp.send('Runtime.evaluate',{userGesture:false,awaitPromise:true,returnByValue:true,expression:'SSNativeShare.shareQuestion({id:1})'});
  assert.deepEqual(inactive.result.value,{ok:false,error:'gesture_required'});
  assert.equal((await cdp.send('Runtime.evaluate',{userGesture:false,returnByValue:true,expression:'requests.length'})).result.value,0);
  await p.addScriptTag({content:await readFile(new URL('../../app/static/js/question-actions.js',import.meta.url),'utf8')});
  await p.evaluate(()=>document.querySelector('#share').onclick=async()=>{
    window.shared=await SSQuestionActions.share({id:10950,text_en:'Public question',options_en:['A','B'],answer_index:1,solution_en:'SECRET_NATIVE_SOLUTION',private:'PRIVATE_USER_DATA'},{lang:'en'});
  });
  await p.locator('#share').click();
  await p.waitForFunction(()=>window.shared===true);
  const requests=await p.evaluate(()=>window.requests);
  assert.deepEqual(requests,[{id:10950,lang:'en',question:'Public question',options:['A','B']}]);
  assert.doesNotMatch(JSON.stringify(requests),/SECRET_NATIVE_SOLUTION|PRIVATE_USER_DATA|answer_index/);
  console.log('Native share wrapper: gesture required; explicit click sends public question only.');
} finally {await browser.close();}
