const {createRequire}=require('module');const assert=require('assert/strict');const fs=require('fs');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
(async()=>{const browser=await chromium.launch({channel:'chrome'});try{
 for(const lang of ['hi','en']){const ctx=await browser.newContext({viewport:{width:360,height:800}});const page=await ctx.newPage();let signed=false,active=false,starts=0,failStatus=false;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const account={id:9901,name:'QA Learner',username:'qa',storage_namespace:'a'.repeat(48)};
 await page.route('**/api/v1/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let data={},code=200;
 if(path.endsWith('/classroom/me'))data={account:signed?account:null};
 else if(path.endsWith('/google/config'))data={enabled:false,web_enabled:false};
 else if(path.endsWith('/classroom/login')||path.endsWith('/classroom/signup')){const body=req.postDataJSON();if(body.password==='incorrect'){code=401;data={detail:'invalid_credentials'};}else{signed=true;data={account};}}
 else if(path.endsWith('/membership/status')||path.endsWith('/membership/start')){if(failStatus){code=503;data={detail:'unavailable'};}else{if(path.endsWith('/start')){active=true;starts++;}data={enabled:true,state:active?'trial':'available',premium_access:active,trial_ends_at:'2027-01-26T12:00:00Z',remaining_seconds:8000000,trial_period:{unit:'calendar_month',count:3}};}}
 return route.fulfill({status:code,contentType:'application/json',body:JSON.stringify(data)});});
 await page.goto('http://127.0.0.1:8023/login?return_to=%2Fbooks'+(lang==='en'?'&lang=en':''));
 const words=await page.evaluate(()=>JSON.parse(document.getElementById('ss-boot').textContent).t);
 await page.getByRole('button',{name:words.login_password_option,exact:true}).click();
 await page.locator('input[name=username]').fill('qa');await page.locator('input[name=password]').fill('incorrect');await page.locator('form button[type=submit]').click();await page.getByText(words.login_wrong_password,{exact:true}).waitFor();
 await page.locator('input[name=password]').fill('valid-test-password');failStatus=true;await page.locator('form button[type=submit]').click();await page.getByText(words.login_activation_failed,{exact:true}).waitFor();
 failStatus=false;await page.getByRole('button',{name:words.login_retry,exact:true}).click();await page.getByText(words.login_trial_active,{exact:true}).waitFor();assert.equal(starts,1);
 assert.equal(await page.getByRole('link',{name:words.login_continue_existing,exact:true}).getAttribute('href'),'/books');
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.reload();await page.getByText(words.login_trial_active,{exact:true}).waitFor();assert.equal(starts,1);
 for(const theme of ['light','dark','paper']){await page.evaluate(x=>SSTheme.set(x),theme);await page.screenshot({path:process.env.QA_SCREENSHOT_DIR+'/login-'+lang+'-'+theme+'.png',fullPage:true});}
 assert.deepEqual(errors,[]);await ctx.close();
 }
 console.log('PASS login: HI/EN, wrong password, login-success/access-failure, retry, automatic single activation, reload, safe study return, three themes, no overflow or JS errors');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});

