/* Isolated event/Promise regression tests; no browser, server or credentials. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').resolve(__dirname,'../../app/static/js/membership.js'),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const defer=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
function setup(initialScope,initialState){
 const events={},calls={fetch:[],clear:0,store:[]},pending=[];
 let scope=initialScope,state=initialState;
 const bridge={required:()=>true,status:async()=>state,clear:async()=>{calls.clear++;state={ok:false};return {ok:true};},storeLease:async value=>{calls.store.push(value);return {ok:true};}};
 const window={StudyStationMembership:bridge,SSWorkspaceScope:()=>scope,addEventListener:(name,fn)=>{events[name]=fn;}};
 const context={window,fetch:(...args)=>{calls.fetch.push(args);const d=defer();pending.push(d);return d.promise;}};
 vm.runInNewContext(source,context);
 return {window,calls,pending,event:()=>events['workspace-scope-changed'](),scope:value=>{scope=value;},state:value=>{state=value;}};
}
(async()=>{
 // Every new document starts priorScope=null: a matching valid native lease wins.
 for(let document=0;document<2;document++){
  const h=setup('account:alice',{ok:true,namespace:'alice'});h.event();await tick();
  assert.equal(h.calls.fetch.length,0);assert.equal(h.calls.clear,0);assert.equal(h.calls.store.length,0);
 }
 const expired=setup('account:alice',{ok:false,namespace:'alice'});expired.event();await tick();
 assert.equal(expired.calls.fetch.length,1);
 expired.pending[0].resolve({ok:true,json:async()=>({lease:'signed-renewal'})});await tick();await tick();
 assert.deepEqual(expired.calls.store,['signed-renewal']);
 const changed=setup('account:bob',{ok:true,namespace:'alice'});changed.event();await tick();
 assert.equal(changed.calls.clear,1);assert.equal(changed.calls.fetch.length,1);
 changed.pending[0].resolve({ok:true,json:async()=>({lease:'bob-lease'})});await tick();
 const guest=setup('guest',{ok:true,namespace:'alice'});guest.event();await tick();
 assert.equal(guest.calls.clear,1);assert.equal(guest.calls.fetch.length,0);
 // Merely loading the file offline must leave native state untouched.
 const cold=setup('guest',{ok:true,namespace:'alice'});await tick();
 assert.equal(cold.calls.clear,0);assert.equal(cold.calls.fetch.length,0);
 for(const status of [401,402]){
  const h=setup('account:alice',{ok:false,namespace:'alice'});h.event();await tick();
  assert.equal(h.calls.fetch.length,1);
  h.scope('account:bob');h.state({ok:true,namespace:'bob'});h.event();await tick();
  const clearBefore=h.calls.clear;
  h.pending[0].resolve({ok:false,status});await tick();await tick();
  assert.equal(h.calls.clear,clearBefore,'Late denial from previous account must not clear Bob');
  assert.equal(h.calls.store.length,0);
 }
 // An old in-flight renewal must neither block nor replace a new account's request.
 const parallel=setup('account:alice',{ok:false,namespace:'alice'});parallel.event();await tick();
 parallel.scope('account:bob');parallel.state({ok:false,namespace:'bob'});parallel.event();await tick();
 assert.equal(parallel.calls.fetch.length,2);
 parallel.pending[0].resolve({ok:false,status:401});await tick();
 parallel.pending[1].resolve({ok:true,json:async()=>({lease:'bob-lease'})});await tick();await tick();
 assert.deepEqual(parallel.calls.store,['bob-lease']);
 console.log('PASS valid daily lease survives fresh documents; expiry/account switch/logout renew safely; stale 401/402 cannot clear new account');
})().catch(error=>{console.error(error);process.exitCode=1;});
