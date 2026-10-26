/* Fresh mobile smoke of the shared Home-style surface, without learner data. */
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.BASE_URL||'http://127.0.0.1:8023';
(async()=>{const browser=await chromium.launch({channel:'chrome'});try{
 const ctx=await browser.newContext({viewport:{width:360,height:800}}),page=await ctx.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 for(const path of ['/','/login','/books','/practice','/mock','/jobs','/settings','/progress']){
  const response=await page.goto(base+path,{waitUntil:'domcontentloaded'});assert.equal(response.status(),200,path);
  await page.waitForFunction(()=>window.SSTheme);
  for(const theme of ['light','dark','paper']){
   await page.evaluate(t=>SSTheme.set(t),theme);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),path+' '+theme+' overflow');
   const surfaces=await page.locator('main .card,main .home-image-card,main .jobs-discovery,main .empty').evaluateAll(cards=>cards.map(card=>{
    const style=getComputedStyle(card);return {image:style.backgroundImage,radius:style.borderRadius};
   }));
   assert.ok(surfaces.length,path+' needs cards');
   assert.ok(surfaces.some(s=>s.image.includes('linear-gradient')),path+' shared glass surface');
   if(process.env.QA_SCREENSHOT_DIR&&theme==='light'){
    fs.mkdirSync(process.env.QA_SCREENSHOT_DIR,{recursive:true});
    await page.screenshot({path:process.env.QA_SCREENSHOT_DIR+'/shared-'+(path.slice(1)||'home')+'.png',fullPage:true});
   }
  }
 }
 assert.deepEqual(errors,[]);console.log('PASS 8 main mobile pages: shared card surfaces, 3 themes, no horizontal overflow or JS errors');
 await ctx.close();
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});
