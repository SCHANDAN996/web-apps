/* Source-only Workspace v2 regression harness. No app/server or learner data used. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const root = process.cwd();
const source = name => fs.readFileSync(path.join(root, 'app/static', name), 'utf8');
const python = path.join(root, '.venv', 'Scripts', 'python.exe');
const copy = spawnSync(python, ['-X', 'utf8', '-c', 'import json; from app.i18n import client_strings; print(json.dumps({x:client_strings(x) for x in ("hi","en")},ensure_ascii=True))'], {encoding:'utf8'});
assert.equal(copy.status, 0, copy.stderr);
const strings = JSON.parse(copy.stdout);
const browserErrors = [];
let browser;
async function boot(page, lang='en') {
  await page.goto('https://workspace.test/');
  await page.evaluate(({lang, strings}) => { window.SS={lang,t:strings}; window.SSWorkspaceScope=()=> 'qa'; }, {lang,strings:strings[lang]});
  for (const name of ['css/app.css','css/dialogs.css','css/workspace.css']) await page.addStyleTag({content:source(name)});
  for (const name of ['workspace-store.js','workspace-renderer.js','workspace-gestures.js','workspace-editor.js','workspace.js']) await page.addScriptTag({content:source('js/'+name)});
}
async function saved(page,id,count) {
  for(let i=0;i<100;i++) { if(await page.evaluate(async ({id,count}) => (await SSWorkspaceStore.get(id)).pages[0].strokes.length===count,{id,count}))break; await page.waitForTimeout(30); }
  assert.equal(await page.evaluate(async id=>(await SSWorkspaceStore.get(id)).pages[0].strokes.length,id),count,'Expected committed stroke count');
  await page.evaluate(()=>SSWorkspaceStore.flush());
}
async function documentEquals(page,id,expected,equal=true) {
 for(let i=0;i<100;i++) {
  const actual=await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id);
  if((actual===expected)===equal)return;
  await page.waitForTimeout(30);
 }
 assert.fail(equal?'Document did not return to its prior state':'Document did not change');
}
async function touch(cdp,type,points) {
  await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points.map(p=>({id:p.id,x:p.x,y:p.y,radiusX:4,radiusY:4,force:1}))});
}
async function geometry(page,selector) {
 return page.locator(selector).evaluate(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};});
}
async function gestureRegression(context) {
 const page=await context.newPage();await boot(page);
 await page.evaluate(()=>{
  document.body.replaceChildren();const stage=document.createElement('div'),canvas=document.createElement('canvas');
  stage.id='gesture-test';Object.assign(stage.style,{position:'fixed',inset:'10px',overflow:'hidden'});canvas.width=900;canvas.height=1200;stage.append(canvas);document.body.append(stage);
  window.gestureEvents={starts:0,cancels:0,ends:0,moves:0};window.gestureTool='pen';
  window.gesture=SSWorkspaceGestures.attach(stage,canvas,{getTool:()=>gestureTool,onStart:()=>gestureEvents.starts++,onMove:()=>gestureEvents.moves++,onEnd:()=>gestureEvents.ends++,onCancel:()=>gestureEvents.cancels++});
 });
 const cdp=await context.newCDPSession(page),a={id:1,x:110,y:300},b={id:2,x:230,y:300};
 const initial=await page.evaluate(()=>gesture.getView());
 await touch(cdp,'touchStart',[a]);await touch(cdp,'touchMove',[{...a,y:320}]);
 await touch(cdp,'touchStart',[{...a,y:320},b]);
 await touch(cdp,'touchMove',[{...a,x:70,y:330},{...b,x:285,y:330}]);
 await touch(cdp,'touchEnd',[{...a,x:70,y:330}]);
 await touch(cdp,'touchMove',[{...a,x:90,y:350}]);await touch(cdp,'touchEnd',[]);
 const after=await page.evaluate(()=>({events:gestureEvents,view:gesture.getView()}));
 assert.equal(after.events.cancels,1,'Second finger cancels uncommitted preview');assert.equal(after.events.ends,0,'Remaining gesture finger never commits ink');assert.equal(after.events.starts,1,'Remaining gesture finger never starts new ink');assert.ok(after.view.zoom>initial.zoom,'Real two-touch pinch changes zoom');
 await touch(cdp,'touchStart',[a]);await touch(cdp,'touchMove',[{...a,y:330}]);await touch(cdp,'touchEnd',[]);
 assert.equal(await page.evaluate(()=>gestureEvents.ends),1,'Drawing resumes after all fingers lift');
 await touch(cdp,'touchStart',[a]);await touch(cdp,'touchCancel',[]);
 assert.equal(await page.evaluate(()=>gestureEvents.ends),1,'Cancelled touch never commits ink');
 await page.evaluate(()=>gestureTool='hand');const beforePan=await page.evaluate(()=>({...gestureEvents}));
 await touch(cdp,'touchStart',[a]);await touch(cdp,'touchMove',[{...a,y:100}]);await touch(cdp,'touchEnd',[]);
 assert.deepEqual(await page.evaluate(()=>gestureEvents),beforePan,'Hand navigation never calls drawing callbacks');
 await page.evaluate(()=>gesture.destroy());await page.close();
}
async function rendererRegression(page) {
 const pixels=await page.evaluate(()=>{
  const c=document.createElement('canvas');c.width=900;c.height=1200;
  const pen={id:'p',tool:'pen',color:'#000000',width:30,points:[[.1,.2],[.9,.2]]};
  const erase={id:'e',tool:'erase',color:'#000000',width:30,points:[[.5,.1],[.5,.3]]};
  const hi={id:'h',tool:'highlighter',color:'#000000',width:30,opacity:.25,points:[[.1,.4],[.9,.4]]};
  SSWorkspaceRender.paint(c,{paper:'grid',strokes:[pen,erase,hi]});
  const ctx=c.getContext('2d'),pixel=(x,y)=>Array.from(ctx.getImageData(x,y,1,1).data);
  return {erased:pixel(450,240),paperLine:pixel(32,400),highlight:pixel(450,482),ink:pixel(200,240),png:c.toDataURL('image/png')};
 });
 assert.deepEqual(pixels.erased,[255,255,255,255],'Eraser removes only ink and retains opaque paper');
 assert.ok(pixels.paperLine[0]<250&&pixels.paperLine[3]===255,'Grid is rendered into image pixels');
 assert.ok(pixels.highlight[0]>170&&pixels.highlight[0]<210,'Highlighter opacity is retained');
 assert.deepEqual(pixels.ink,[0,0,0,255]);assert.ok(pixels.png.startsWith('data:image/png;base64,'));
}
async function editorRegression(context) {
 const page=await context.newPage();await boot(page);await rendererRegression(page);
 const id=await page.evaluate(async()=>{const b=await SSWorkspaceStore.create('QA drawing');await SSWorkspace.open({id:b.id});return b.id;});
 await page.locator('.workspace-canvas').waitFor();
 await page.waitForTimeout(100);const box=await geometry(page,'.workspace-stage'),paper=await geometry(page,'.workspace-canvas');const x=paper.x+paper.width*.4,y=Math.max(box.y+30,paper.y+paper.height*.18);
 await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+45,y+30,{steps:8});await page.mouse.up();await saved(page,id,1);
 const original=await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id);
 const cdp=await context.newCDPSession(page),a={id:1,x,y},b={id:2,x:x+75,y};
 await touch(cdp,'touchStart',[a]);await touch(cdp,'touchMove',[{...a,y:y+15}]);await touch(cdp,'touchStart',[{...a,y:y+15},b]);await touch(cdp,'touchMove',[{...a,x:x-20,y:y+20},{...b,x:x+105,y:y+20}]);await touch(cdp,'touchEnd',[{...a,x:x-20,y:y+20}]);await touch(cdp,'touchMove',[{...a,x:x-10,y:y+45}]);await touch(cdp,'touchEnd',[]);
 await page.evaluate(()=>SSWorkspaceStore.flush());assert.equal(await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id),original,'Pinch including preview cancellation leaves saved strokes byte-identical');
 // Selection edits change the document once and remain reversible.
 await page.locator('.workspace-pages [data-action="fit"]').click();
 await page.locator('[data-tool="select"]').click();
 async function selectStroke() {
  const stroke=await page.evaluate(async id=>(await SSWorkspaceStore.get(id)).pages[0].strokes[0],id);
  const r=await geometry(page,'.workspace-canvas'),xs=stroke.points.map(p=>p[0]),ys=stroke.points.map(p=>p[1]);
  const left=r.x+(Math.min(...xs)-.02)*r.width,top=r.y+(Math.min(...ys)-.02)*r.height;
  await page.mouse.move(left,top);await page.mouse.down();await page.mouse.move(r.x+(Math.max(...xs)+.02)*r.width,r.y+(Math.max(...ys)+.02)*r.height,{steps:5});await page.mouse.up();
  await page.locator('[data-action="copy-selection"]').waitFor({state:'visible'});
  await page.waitForTimeout(80); // Selection action rail changes the available canvas viewport.
 }
 await selectStroke();await page.locator('[data-action="copy-selection"]').click();await saved(page,id,2);
 await page.locator('[data-action="delete-selection"]').click();await saved(page,id,1);
 await page.locator('[data-action="undo"]').click();await saved(page,id,2);
 await page.locator('[data-action="redo"]').click();await saved(page,id,1);
 await selectStroke();
 const beforeMove=await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id);
 const stroke=JSON.parse(beforeMove)[0],r=await geometry(page,'.workspace-canvas'),point=stroke.points[Math.floor(stroke.points.length/2)];
 await page.mouse.move(r.x+point[0]*r.width,r.y+point[1]*r.height);await page.mouse.down();await page.mouse.move(r.x+(point[0]+.06)*r.width,r.y+(point[1]+.04)*r.height,{steps:5});await page.mouse.up();
 await documentEquals(page,id,beforeMove,false);
 await page.locator('[data-action="undo"]').click();await documentEquals(page,id,beforeMove);
 await page.locator('[data-action="redo"]').click();await documentEquals(page,id,beforeMove,false);
 await selectStroke();
 const beforeResize=await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id);
 const resizeStroke=JSON.parse(beforeResize)[0],resizePaper=await geometry(page,'.workspace-canvas');
 const maxX=Math.max(...resizeStroke.points.map(p=>p[0])),maxY=Math.max(...resizeStroke.points.map(p=>p[1]));
 const beforeResizeImage=await page.locator('.workspace-canvas').evaluate(canvas=>canvas.toDataURL());
 await page.mouse.move(resizePaper.x+maxX*resizePaper.width,resizePaper.y+maxY*resizePaper.height);await page.mouse.down();
 await page.mouse.move(resizePaper.x+(maxX+.08)*resizePaper.width,resizePaper.y+(maxY+.06)*resizePaper.height,{steps:6});await page.mouse.up();
 await documentEquals(page,id,beforeResize,false);await page.waitForTimeout(60);
 const afterResize=await page.evaluate(async id=>JSON.stringify((await SSWorkspaceStore.get(id)).pages[0].strokes),id);
 const resizedStroke=JSON.parse(afterResize)[0];
 assert.ok(resizedStroke.points.every(p=>p.every(n=>Number.isFinite(n)&&n>=0&&n<=1)),'Resize retains normalized document coordinates');
 assert.ok(Math.max(...resizedStroke.points.map(p=>p[0]))>maxX+.05,'Resize handle expands selection width');
 assert.ok(Math.max(...resizedStroke.points.map(p=>p[1]))>maxY+.035,'Resize handle expands selection height');
 assert.notEqual(await page.locator('.workspace-canvas').evaluate(canvas=>canvas.toDataURL()),beforeResizeImage,'Resize updates rendered ink and selection');
 await page.locator('[data-action="undo"]').click();await documentEquals(page,id,beforeResize);
 await page.locator('[data-action="redo"]').click();await documentEquals(page,id,afterResize);
 for (const lang of ['hi','en']) {
  await page.evaluate(({lang,t})=>{SS.lang=lang;SS.t=t;},{lang,t:strings[lang]});
  // Reopen to create controls in the selected locale.
  await page.locator('[data-action="close"]').click();await page.locator('.workspace-editor').waitFor({state:'detached'});await page.evaluate(id=>SSWorkspace.open({id}),id);
  for (const [width,height] of [[360,640],[390,844],[412,915],[844,330]]) {
   await page.setViewportSize({width,height});
   for (const theme of ['light','dark','paper']) {
    await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
    await page.waitForTimeout(60);
    const boxes=await page.locator('.workspace-top button,.workspace-toolbar button,.workspace-stage').evaluateAll(nodes=>nodes.map(el=>{const r=el.getBoundingClientRect();return {label:el.getAttribute('aria-label'),tag:el.tagName,x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height};}));
    for(const r of boxes){assert.ok(r.x>=-1&&r.y>=-1&&r.right<=width+1&&r.bottom<=height+1,JSON.stringify({lang,theme,width,height,r}));if(r.tag==='BUTTON'){assert.ok(r.width>=44&&r.height>=44,JSON.stringify(r));assert.ok(r.label&&!/^workspace_/.test(r.label),'Icon buttons have localized accessible labels');}}
    assert.equal(await page.locator('[data-action="help"]').getAttribute('aria-label'),strings[lang].workspace_help);
    if(process.env.QA_SCREENSHOT_DIR&&theme==='light') {
     fs.mkdirSync(process.env.QA_SCREENSHOT_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,`workspace-v2-${lang}-${width}x${height}.png`)});
    }
   }
  }
  await page.locator('[data-action="help"]').click();
  const help=page.locator('dialog').last();assert.ok((await help.innerText()).length>180,'Help explains usage beyond a heading');
  await page.keyboard.press('Escape');await page.locator('.workspace-editor').waitFor();assert.equal(await page.locator('dialog[open]').count(),1,'Help cancellation preserves editor');
  await page.locator('[data-action="more"]').click();const menu=page.locator('dialog').last();const last=menu.getByRole('button').last();await last.scrollIntoViewIfNeeded();const lastBox=await last.boundingBox();assert.ok(lastBox.y>=0&&lastBox.y+lastBox.height<=330+1,'Last menu action remains reachable in landscape');await page.keyboard.press('Escape');
 }
 await page.close();
}
async function exportRegression(context) {
 const page=await context.newPage();await boot(page);
 await page.evaluate(async()=>{
  const board=await SSWorkspaceStore.create('QA export');board.pages[0].paper='grid';
  board.pages[0].strokes=[
   {id:'ink',tool:'pen',color:'#000000',width:30,points:[[.1,.2],[.9,.2]]},
   {id:'rubber',tool:'erase',color:'#000000',width:30,points:[[.5,.1],[.5,.3]]},
   {id:'highlight',tool:'highlighter',color:'#000000',width:30,opacity:.25,points:[[.1,.4],[.9,.4]]}
  ];await SSWorkspaceStore.save(board);await SSWorkspace.open({id:board.id});
 });
 for(const kind of ['PNG','SVG']) {
  await page.locator('[data-action="more"]').click();
  const downloadPromise=page.waitForEvent('download');await page.locator(`[data-export="${kind}"]`).click();
  const download=await downloadPromise,buffer=fs.readFileSync(await download.path());
  assert.ok(download.suggestedFilename().endsWith('.'+kind.toLowerCase()));
  let dataUrl;
  if(kind==='PNG')dataUrl='data:image/png;base64,'+buffer.toString('base64');
  else {const svg=buffer.toString('utf8');assert.ok(svg.startsWith('<svg'));assert.ok(svg.includes('width="900" height="1200"'));dataUrl=svg.match(/href="([^"]+)"/)[1];}
  const pixels=await page.evaluate(async url=>{
   const image=new Image();image.src=url;await image.decode();const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);const pixel=(x,y)=>Array.from(ctx.getImageData(x,y,1,1).data);
   return {size:[c.width,c.height],erased:pixel(450,240),line:pixel(32,400),highlight:pixel(450,482)};
  },dataUrl);
  assert.deepEqual(pixels.size,[900,1200]);assert.deepEqual(pixels.erased,[255,255,255,255],kind+' retains paper under erasing');assert.ok(pixels.line[0]<250,kind+' includes grid');assert.ok(pixels.highlight[0]>170&&pixels.highlight[0]<210,kind+' preserves highlighter opacity');
 }
 await page.close();
}
(async()=>{
 browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true});
 context.on('page',p=>p.on('pageerror',e=>browserErrors.push(e.message)));
 await context.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,'https://workspace.test','No external network');return route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body></body></html>'});});
 await gestureRegression(context);await editorRegression(context);await exportRegression(context);assert.deepEqual(browserErrors,[]);
 console.log('PASS Workspace v2: real touch gestures, no phantom ink, autosave, selection/undo/redo, PNG/SVG paper/opacity exports, localized icons/help, portrait/short-landscape geometry');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});



