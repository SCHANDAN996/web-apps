(function () {
  'use strict';
  var active = null, scopeAccount = null;
  var scopeRequest=null;
  window.SSWorkspaceEnsure=function(){if(!scopeRequest)scopeRequest=fetch('/api/v1/classroom/me',{credentials:'same-origin',cache:'no-store'}).then(function(r){if(!r.ok)throw Error('auth');return r.json();}).then(function(d){scopeAccount=d.account||null;}).catch(function(){scopeAccount=null;});return scopeRequest;};
  window.SSWorkspaceReady=Promise.resolve();
  window.SSWorkspaceForgetAccount=function(){scopeAccount=null;scopeRequest=null;};

  window.SSWorkspaceScope = function () { return scopeAccount && /^[a-f0-9]{48}$/.test(scopeAccount.storage_namespace||'') ? 'account:' + scopeAccount.storage_namespace : (scopeAccount ? 'locked' : 'guest'); };
  window.SSWorkspaceLegacyScope = function () { return scopeAccount && scopeAccount.legacy_workspace_scope && /^[a-f0-9]{48}$/.test(scopeAccount.storage_namespace||'') ? 'account:' + scopeAccount.id : null; };
  function init() {
    var root = document.getElementById('classroomHub');
    if (!root || root.dataset.ready) return;
    root.dataset.ready = '1';
    if (active) active();
    var alive = true, timer = null, account = null, boot = JSON.parse(document.getElementById('ss-boot').textContent), words = boot.t || {};
    function t(k) { return words['classroom_' + k] || k; }
    function stop() { alive = false; clearTimeout(timer); window.removeEventListener('ss-google-auth-ready', googleReady); }
    var googleReady = function () {};
    active = stop;
    if (window.SS && SS.onLeave) SS.onLeave(stop);
    function node(tag, text, cls) { var e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; }
    function box(title, parent) { var b = node('section', null, 'cr-card'); if (title) b.append(node('h2', title)); (parent || root).append(b); return b; }
    function button(label, fn, parent, primary) { var b = node('button', label, 'btn ' + (primary ? 'btn-primary' : 'btn-secondary')); b.type = 'button'; b.onclick = function () { run(fn, b); }; parent.append(b); return b; }
    var status = node('p', '', 'cr-status'); status.setAttribute('role', 'status');
    async function run(fn, b) { if (b) b.disabled = true; status.textContent = t('loading'); status.classList.remove('cr-error'); try { await fn(); if (alive) status.textContent = ''; } catch (e) { if (alive) { status.textContent = t('error') + ' ' + (words['classroom_error_' + e.message] || t('retry')); status.classList.add('cr-error'); } } finally { if (b && alive) b.disabled = false; } }
    async function api(path, method, data) { var r = await fetch('/api/v1/classroom' + path, {method: method || 'GET', credentials: 'same-origin', cache:'no-store', headers: data ? {'Content-Type':'application/json'} : {}, body: data ? JSON.stringify(data) : undefined}); var d = await r.json(); if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'request_failed'); return d; }
    function op(data) { return Object.assign({op_id: crypto.randomUUID()}, data || {}); }
    function clear(title) { clearTimeout(timer); root.replaceChildren(); root.append(node('h1', title || t('title')), status); status.textContent = ''; }
    function input(form, label, name, type, required) { var l = node('label', label), i = node(type === 'textarea' ? 'textarea' : 'input'); i.name = name; if (type !== 'textarea') i.type = type || 'text'; i.required = required !== false; l.append(i); form.append(l); return i; }
    function form(parent, label, fields, submit) { var f = node('form'); var ins = {}; fields.forEach(function (x) { ins[x[1]] = input(f, t(x[0]), x[1], x[2], x[3]); }); var b = node('button', t(label), 'btn btn-primary'); b.type = 'submit'; f.append(b); f.onsubmit = function(e) { e.preventDefault(); run(function(){ var values={};Object.keys(ins).forEach(function(k){values[k]=k==='password'?ins[k].value:ins[k].value.trim();}); return submit(values); },b); }; parent.append(f); return ins; }
    function back(fn) { button(t('back'), fn || hub, root); }
    function recordName(r) { return r.name || (r.data && r.data.name) || t('untitled'); }
    function data(r) { return r.data || r; }
    function invitation() { var q = new URLSearchParams(location.search); return q.get('join') || q.get('invite') || ''; }
    function sharedToken() { var m = location.pathname.match(/^\/w\/([A-Za-z0-9_-]+)$/); return m ? m[1] : new URLSearchParams(location.search).get('workspace'); }
    async function auth() {
      clear(); root.append(node('p', t('account_note'), 'cr-note'));
      var googleBox=box('',root), googleButton=button(t('google_continue'),googleSignIn,googleBox);
      googleButton.dataset.googleSignin=''; googleButton.disabled=true;
      googleButton.style.cssText='display:flex;align-items:center;justify-content:center;gap:12px;background:#fff;color:#1f1f1f;border:1px solid #747775;min-height:48px;border-radius:12px';
      var svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 48 48');svg.setAttribute('width','20');svg.setAttribute('height','20');svg.setAttribute('aria-hidden','true');svg.style.flex='0 0 20px';
      [['#4285F4','M43.61 20.46H42V20H24v8h11.3A12 12 0 0 1 12.7 32.5l-6.56 5.05A20 20 0 0 0 44 24c0-1.21-.14-2.39-.39-3.54Z'],['#34A853','M24 44c5.39 0 10.3-2.06 13.95-5.43l-6.19-5.24A12 12 0 0 1 12.7 28H4.41A20 20 0 0 0 24 44Z'],['#FBBC05','M12 24c0-1.37.24-2.69.67-3.92L6.1 15A20 20 0 0 0 4 24c0 3.23.77 6.28 2.14 8.98l6.56-5.05A12 12 0 0 1 12 24Z'],['#EA4335','M24 12c3.06 0 5.85 1.15 7.97 3.03l5.66-5.66A20 20 0 0 0 6.1 15l6.57 5.08A12 12 0 0 1 24 12Z']].forEach(function(v){var p=document.createElementNS(svg.namespaceURI,'path');p.setAttribute('fill',v[0]);p.setAttribute('d',v[1]);svg.append(p);});googleButton.prepend(svg);
      var googleNote=node('p',t('google_loading'),'cr-private');googleNote.setAttribute('role','status');googleBox.append(googleNote);
      var googleConfig=null,googleNonce=null,preparing=null;
      function nativeBridge(){var b=window.StudyStationAuth;try{return b&&typeof b.configured==='function'&&b.configured()?b:null;}catch(e){return null;}}
      async function prepareGoogle(){
        if(preparing)return preparing;
        preparing=(async function(){try{googleConfig=await api('/google/config');if(!alive||!document.contains(googleButton))return;
          if(googleConfig.enabled&&nativeBridge()){var challenge=await api('/google/challenge','POST',{});googleNonce=challenge.nonce;}
          if(!alive||!document.contains(googleButton))return;
          googleButton.disabled=!(googleConfig.enabled&&googleNonce&&nativeBridge())&&!(googleConfig.web_enabled&&!window.StudyStationAuth);
          googleNote.textContent=googleButton.disabled?t('google_unavailable'):t('google_privacy');
        }catch(e){if(alive){googleNote.textContent=t('google_unavailable');googleButton.disabled=true;}}finally{preparing=null;}})();return preparing;
      }
      async function googleSignIn(){
        var bridge=nativeBridge();
        if(bridge&&googleNonce){var nonce=googleNonce;googleNonce=null;var result,failureNote='';
          try{result=await bridge.signIn(nonce);if(!alive||!document.contains(googleButton))return;
            if(!result||result.ok!==true||typeof result.idToken!=='string'){var outcome=t(result&&result.error==='cancelled'?'google_cancelled':'google_failed');await prepareGoogle();googleNote.textContent=outcome;return;}
            var token=result.idToken;result.idToken='';try{await api('/google/token','POST',{id_token:token});}finally{token=null;}await start();
          }catch(e){failureNote=t('google_failed');}finally{result=null;if(alive&&document.contains(googleButton)){if(!googleNonce)await prepareGoogle();if(failureNote)googleNote.textContent=failureNote;}}
        }else if(googleConfig&&googleConfig.web_enabled&&!window.StudyStationAuth){var target=location.pathname+location.search;location.assign('/api/v1/classroom/google/start?return_to='+encodeURIComponent(target));}
      }
      window.removeEventListener('ss-google-auth-ready',googleReady);googleReady=function(){if(alive&&document.contains(googleButton))prepareGoogle();};window.addEventListener('ss-google-auth-ready',googleReady);prepareGoogle();
      var authError=new URLSearchParams(location.search).get('google_error');if(authError)googleNote.textContent=t('google_failed');
      var grid=node('div',null,'cr-grid');root.append(grid);
      form(box(t('login'),grid),'login',[['username','username'],['password','password','password']],async function(v){await api('/login','POST',v); await start();});
      var signup=form(box(t('signup'),grid),'signup',[['name','name'],['username','username'],['password','password','password']],async function(v){await api('/signup','POST',v);await start();});signup.password.minLength=10;
    }
    async function rules(returnTo) {
      var safety=await api('/safety');if(!alive)return;
      clear(t('community_rules'));root.append(node('p',safety.terms[boot.lang]||safety.terms.hi,'cr-note'));
      var f=node('form'),label=node('label'),check=node('input');check.type='checkbox';check.required=true;label.append(check,node('span',t('accept_rules')));f.append(label);
      var accept=node('button',t('continue'),'btn btn-primary');accept.type='submit';f.append(accept);root.append(f);
      f.onsubmit=function(e){e.preventDefault();if(!check.checked)return;run(async function(){await api('/safety/terms','POST',{version:safety.version,accept:true});await (returnTo||start)();},accept);};
      button(t('private_only'),async function(){clear(t('my_workspace'));await SSWorkspace.mount(box(t('my_workspace')));button(t('community_rules'),function(){return rules(returnTo);},root);},root);
    }
    function safetyActions(record,parent,token) {
      if(!record)return;
      var row=node('div',null,'cr-row');parent.append(row);
      button(t('report'),function(){var panel=box(t('report'),parent);var reason=node('select');reason.setAttribute('aria-label',t('report_reason'));
        ['abuse','sexual','violence','spam','other'].forEach(function(k){var o=node('option',t('reason_'+k));o.value=k;reason.append(o);});panel.append(reason);
        var fields=form(panel,'send_report',[['report_details','text','textarea',false]],async function(v){await api('/safety/reports','POST',{record_id:record.id,reason:reason.value,text:v.text,token:token});panel.replaceChildren(node('p',t('report_received'),'cr-note'));});fields.text.maxLength=2000;
      },row);
      if(String(record.owner_id)!==String(account.id))button(t('block_user'),async function(){await api('/safety/blocks','POST',{account_id:record.owner_id,blocked:true});await hub();},row);
    }
    async function manageSafety() {
      var safety=await api('/safety');clear(t('community_rules'));back();root.append(node('p',safety.terms[boot.lang]||safety.terms.hi,'cr-note'));
      var list=box(t('blocked_users'));if(!safety.blocked.length)list.append(node('p',t('none_blocked')));
      safety.blocked.forEach(function(x){var row=node('div',null,'cr-row');row.append(node('span',x.name));list.append(row);button(t('unblock'),async function(){await api('/safety/blocks','POST',{account_id:x.account_id,blocked:false});await manageSafety();},row);});
    }
    async function start() { await window.SSWorkspaceEnsure(); var me=await api('/me'); if(!alive)return;account=me.account; scopeAccount=account; window.dispatchEvent(new Event('workspace-scope-changed')); if(!account)return auth(); var safety=await api('/safety');if(!safety.accepted)return rules(); if(sharedToken())return shared(sharedToken()); if(invitation())return joinScreen(invitation());return hub(); }
    async function hub() {
      var h=await api('/hub');if(!alive)return;clear();var view=new URLSearchParams(location.search).get('view')||'';if(view==='workspace'){await SSWorkspace.mount(box(t('my_workspace')));return;}if(view==='groups'||view==='classes')h.groups=h.groups.filter(function(g){return data(g).kind===(view==='classes'?'class':'peer');});
      var row=node('div',null,'cr-row');root.append(row);button(t('community_rules'),manageSafety,row);row.append(node('span',(account.name||account.username)+' · ID '+account.id,'cr-pill'));button(t('logout'),async function(){await api('/logout','POST',{});if(window.StudyStationAuth&&typeof window.StudyStationAuth.signOut==='function'){try{await window.StudyStationAuth.signOut();}catch(e){}}account=null;scopeAccount=null;window.dispatchEvent(new Event('workspace-scope-changed'));auth();},row);
      root.append(node('p',t('private_note'),'cr-private'));var privacyLinks=node('div',null,'cr-row');[['/membership',words.membership_title||'Membership'],['/privacy',words.privacy_title||'Privacy'],['/delete-account',words.deletion_title||'Delete account']].forEach(function(x){var a=node('a',x[1],'btn btn-ghost');a.href=x[0];privacyLinks.append(a);});root.append(privacyLinks);
      var grid=node('div',null,'cr-grid');root.append(grid);
      var create=box(t('create_group'),grid);var fields=form(create,'create',[['group_name','name'],['goal','goal','textarea',false]],async function(v){v.kind=kind.value;await api('/groups','POST',op(v));await hub();});
      var kind=node('select');kind.setAttribute('aria-label',t('kind'));[['peer','peer'],['class','class']].forEach(function(x){var o=node('option',t(x[1]));o.value=x[0];kind.append(o);});create.querySelector('form').prepend(kind);if(view==='classes')kind.value='class';if(view==='shared')grid.hidden=true;
      form(box(t('join'),grid),'join',[['invite_code','token']],async function(v){await api('/join','POST',op(v));await hub();});
      var list=box(t('my_groups'));if(!(h.groups||[]).length)list.append(node('p',t('empty_groups')));(h.groups||[]).forEach(function(g){var c=box(recordName(g),list);c.append(node('p',data(g).goal||''));c.append(node('span',t(data(g).kind==='class'?'class':'peer'),'cr-pill'));button(t('open'),function(){return group(g.id);},c,true);});
      if(view==='shared')list.hidden=true;var local=box(t('my_workspace'));if(view==='shared')local.hidden=true; await window.SSWorkspace.mount(local);
      var w=box(t('shared_work'));if(!(h.workspaces||[]).length)w.append(node('p',t('empty_work')));(h.workspaces||[]).forEach(function(x){var c=box(recordName(x),w);button(t('open'),function(){return workspace(x);},c);});
      button(t('publish_work'),publishPicker, w);
    }
    async function joinScreen(token) { clear(t('join'));root.append(node('p',t('join_note')));button(t('join'),async function(){await api('/join','POST',op({token:token}));await hub();},root,true);back(); }
    async function localSnapshots() {
      var engine=window.SSWorkspaceStore;
      if(!engine)throw new Error('workspace_unavailable');
      if(engine.listSnapshots)return engine.listSnapshots();
      var items=await engine.list();return items.filter(function(x){return !x.deleted;}).map(function(x){return {id:x.id,name:x.name,snapshot:x};});
    }
    async function chooseSnapshot(parent, submit) {
      var items=await localSnapshots();if(!alive)return;if(!items.length){parent.append(node('p',t('empty_local')));return;}
      var select=node('select');select.setAttribute('aria-label',t('select_work'));items.forEach(function(x,i){var o=node('option',x.name||t('untitled'));o.value=String(i);select.append(o);});parent.append(select);
      parent.append(node('p',t('explicit_publish'),'cr-private'));button(t('send_selected'),function(){var x=items[Number(select.value)];return submit(x.snapshot||x,x.name);},parent,true);
    }
    async function publishPicker() {clear(t('publish_work'));back();await chooseSnapshot(box(t('select_work')),async function(snapshot,name){await api('/workspaces','POST',op({name:name||t('untitled'),snapshot:snapshot}));await hub();});}
    async function group(id) {
      var d=await api('/groups/'+id);if(!alive)return;clear(recordName(d.group));back();root.append(node('p',data(d.group).goal||''));safetyActions(d.group,root);
      var members=d.members||[], own=String(d.group.owner_id)===String(account.id), membership=members.find(function(m){return String(m.id)===String(account.id);}), teacher=own||d.role==='teacher';
      var actions=node('div',null,'cr-row');root.append(actions);
      if(teacher)button(t('invite'),async function(){var r=await api('/groups/'+id+'/invite','POST',{});showLink(location.origin+'/classroom?join='+encodeURIComponent(r.token));},actions);
      var assignments=box(t('assignments'));if(!(d.assignments||[]).length)assignments.append(node('p',t('empty_assignments')));(d.assignments||[]).forEach(function(a){button(recordName(a),function(){return assignment(a.id,id,teacher);},assignments);});
      if(teacher)form(box(t('new_assignment')),'publish',[['task_name','name'],['instructions','instructions','textarea'],['question_ids','question_ids','text',false]],async function(v){v.question_ids=v.question_ids?v.question_ids.split(/[\s,]+/).map(Number):[];if(v.question_ids.some(function(n){return !Number.isInteger(n)||n<1;}))throw new Error('invalid_questions');await api('/groups/'+id+'/assignments','POST',op(v));await group(id);});
      var sessions=box(t('sessions'));(d.sessions||[]).forEach(function(s){button(recordName(s),function(){return session(s.id,id,teacher);},sessions);});if(teacher)form(sessions,'start_session',[['session_name','name']],async function(v){var r=await api('/groups/'+id+'/sessions','POST',op(v));return session((r.session||r).id,id,true);});
      var doubts=box(t('discussions'));(d.discussions||[]).forEach(function(x){var dd=data(x);var item=node('section',null,'cr-note');item.append(node('p',(dd.question_id?'SS-'+dd.question_id+' · ':'')+dd.text));doubts.append(item);safetyActions(x,item);});form(doubts,'send_doubt',[['doubt','text','textarea'],['question_id','question_id','number',false]],async function(v){v.question_id=v.question_id?Number(v.question_id):null;await api('/groups/'+id+'/discussions','POST',op(v));await group(id);});
      var roster=box(t('members'));members.forEach(function(m){var r=node('div',null,'cr-row');r.append(node('span',m.name||m.username||String(m.id)),node('span',t(m.role)||m.role,'cr-pill'));roster.append(r);if(String(m.id)!==String(account.id))button(t('block_user'),async function(){await api('/safety/blocks','POST',{account_id:m.id,blocked:true});await group(id);},r);if(own&&String(m.id)!==String(account.id)){button(t(m.role==='teacher'?'make_student':'make_teacher'),async function(){await api('/groups/'+id+'/members','POST',{account_id:m.id,role:m.role==='teacher'?'student':'teacher'});await group(id);},r);}if(own&&String(m.id)!==String(account.id))button(t(m.role==='editor'?'make_student':'grant_write'),async function(){await api('/groups/'+id+'/members','POST',{account_id:m.id,role:m.role==='editor'?'student':'editor'});await group(id);},r);});
    }
    function showLink(url) { var p=node('p',url,'cr-link');root.append(p);button(t('copy_link'),async function(){await navigator.clipboard.writeText(url);status.textContent=t('copied');},root); }
    async function assignment(id,gid,teacher) {
      var d=await api('/assignments/'+id);if(!alive)return;clear(recordName(d.assignment));back(function(){return group(gid);});root.append(node('p',data(d.assignment).instructions||''));safetyActions(d.assignment,root);var answers={}, qs=box(t('questions'));
      (d.questions||[]).forEach(function(q,i){var c=node('fieldset',null,'cr-answer');c.append(node('legend',String(i+1)+'. '+(q['text_'+boot.lang]||q.text_hi||q.text_en||'')));var opts=q['options_'+boot.lang]||q.options_hi||q.options_en||[];if(!Array.isArray(opts))opts=Object.values(opts);opts.forEach(function(o,j){var l=node('label'),r=node('input');r.type='radio';r.name='q'+q.id;r.onchange=function(){answers[q.id]=j;};l.append(r,node('span',typeof o==='string'?o:o.text||''));c.append(l);});qs.append(c);});
      if(!teacher){var send=box(t('submit_work'));send.append(node('p',t('explicit_publish'),'cr-private'));button(t('submit_answers'),async function(){await api('/assignments/'+id+'/submissions','POST',op({answers:answers,snapshot:{pages:[]}}));await assignment(id,gid,false);},send,true);await chooseSnapshot(send,async function(snapshot){await api('/assignments/'+id+'/submissions','POST',op({answers:answers,snapshot:snapshot}));await assignment(id,gid,false);});}
      var submissions=box(t(teacher?'review_work':'my_submissions'));(d.submissions||[]).forEach(function(s){var sd=data(s), c=box((s.name||s.account_name||t('submission'))+' · '+String(s.id),submissions);(Array.isArray(sd.feedback)?sd.feedback:[{text:sd.feedback||''}]).forEach(function(f){if(f.text)c.append(node('p',f.text,'cr-note'));});renderSnapshot(sd.snapshot||{},c);safetyActions(s,c);if(teacher)form(c,'send_feedback',[['feedback','text','textarea']],async function(v){await api('/submissions/'+s.id+'/feedback','POST',op(v));await assignment(id,gid,true);});});
    }
    function renderSnapshot(snapshot,parent) { (snapshot.pages||[]).forEach(function(p,i){var c=node('div',null,'cr-stack');c.append(node('h3',p.name||t('page')+' '+(i+1)));var canvas=node('canvas',null,'cr-board cr-snapshot');canvas.width=900;canvas.height=1200;canvas.setAttribute('aria-label',t('shared_page'));c.append(canvas);parent.append(c);paint(canvas,p);if(p.text)c.append(node('p',p.text));}); }
    function paint(canvas,page) {window.SSWorkspaceRender.paint(canvas,Array.isArray(page)?{paper:'blank',strokes:page}:page);}

    async function workspace(w,token) {var fresh=await api('/workspaces/'+w.id+(token?'?token='+encodeURIComponent(token):''));if(!alive)return;w=fresh.workspace;clear(recordName(w));back();safetyActions(w,root,token);var wd=data(w);if(fresh.source_status)root.append(node('p',t(fresh.source_status==='linked'?'source_linked':'source_revoked'),'cr-note'));renderSnapshot(data(fresh.source||w).snapshot||{},box(t('shared_work')));var row=node('div',null,'cr-row');root.append(row);button(t('open_private_copy'),async function(){var snap=data(fresh.source||w).snapshot;var copy=await SSWorkspaceStore.import({format:'study-station-workspace',version:1,workspace:Object.assign({},snap,{name:recordName(w)})});await SSWorkspace.open({id:copy.id});},row);if(fresh.can_write){button(t('update_work'),async function(){var picker=box(t('select_work'));await chooseSnapshot(picker,async function(snapshot,name){await api('/workspaces/'+w.id,'PUT',op({version:w.version,name:name,snapshot:snapshot}));await workspace(w,token);});},row);}if(String(w.owner_id)===String(account.id)){form(box(t('edit_permission')),'grant_write',[['account_id','account_id','number']],async function(v){await api('/workspaces/'+w.id+'/editors','POST',{account_id:Number(v.account_id),allow:true,version:w.version});await workspace(w,token);});button(t('share'),async function(){var r=await api('/workspaces/'+w.id+'/share','POST',op());showLink(r.url.startsWith('/')?location.origin+r.url:r.url);},row);button(t('revoke'),async function(){await api('/workspaces/'+w.id+'/share','DELETE',{});status.textContent=t('revoked');},row);}button(t('copy_work'),function(){return api('/workspaces/'+w.id+'/copy','POST',op({token:token||undefined,linked:false})).then(hub);},row);button(t('link_work'),function(){return api('/workspaces/'+w.id+'/copy','POST',op({token:token||undefined,linked:true})).then(hub);},row);}
    async function shared(token) {var r=await api('/shared/'+encodeURIComponent(token));if(alive)await workspace(r.workspace,token);}
    async function session(id,gid,teacher) {
      var d=await api('/sessions/'+id+'?after=0');if(!alive)return;clear(recordName(d.session));back(function(){return group(gid);});safetyActions(d.session,root);root.append(node('p',t(teacher?'teacher_board':'follow_board'),'cr-note'));var connection=node('p',t('connected'),'cr-status');root.append(connection);var canvas=node('canvas',null,'cr-board');canvas.width=1000;canvas.height=700;canvas.setAttribute('aria-label',t('live_board'));canvas.setAttribute('aria-disabled',String(!teacher));root.append(canvas);teacher=!!d.can_write;var strokes=[],paper='blank',version=d.session.version,seq=0,ended=!data(d.session).active,points=null,queue=Promise.resolve();var hands=box(t('hands'));
      function ingest(r){version=r.session.version;(r.events||[]).forEach(function(e){if(e.seq<=seq)return;seq=e.seq;var ed=e.data||e, payload=ed.payload||{};if(ed.type==='stroke')strokes.push(payload);if(ed.type==='page'){strokes=[];paper=payload.paper||'blank';}if(ed.type==='snapshot'){var first=payload.pages&&payload.pages[0];strokes=(first&&first.strokes)||[];paper=(first&&first.paper)||'blank';}if(ed.type==='undo'){strokes.pop();}if(ed.type==='hand'){hands.append(node('p',(payload.name||t('student'))+' · '+t('help_requested')));}if(ed.type==='end'){ended=true;connection.textContent=t('ended');}});paint(canvas,{paper:paper,strokes:strokes});}
      ingest(d);
      var pendingKey='ss-live-pending:'+account.id+':'+id,pendingOps=[];try{pendingOps=JSON.parse(localStorage.getItem(pendingKey)||'[]');if(!Array.isArray(pendingOps))pendingOps=[];}catch(e){}var flushing=false;
      function savePending(){localStorage.setItem(pendingKey,JSON.stringify(pendingOps));}
      async function flushPending(){if(flushing||!alive)return;flushing=true;try{while(pendingOps.length&&alive){var item=pendingOps[0],tries=0;while(true){var latest=await api('/sessions/'+id+'?after='+seq);if(!alive)return;ingest(latest);try{await api('/sessions/'+id+'/events','POST',{op_id:item.op_id,version:version,type:item.type,payload:item.payload});break;}catch(e){if((e.message==='version_conflict'||e.message==='concurrent_operation_retry')&&++tries<4)continue;throw e;}}pendingOps.shift();savePending();var fresh=await api('/sessions/'+id+'?after='+seq);if(alive)ingest(fresh);}}finally{flushing=false;}}
      async function event(type,payload){if(pendingOps.length>=50)throw Error('try_later');pendingOps.push({op_id:crypto.randomUUID(),type:type,payload:payload});savePending();return flushPending();}

      if(teacher){canvas.onpointerdown=function(e){if(ended)return;points=[];canvas.setPointerCapture(e.pointerId);point(e);};canvas.onpointermove=function(e){if(points)point(e);};canvas.onpointerup=function(){if(!points)return;var s={points:points,color:'#333333',width:3};points=null;queue=queue.then(function(){return event('stroke',s);}).catch(function(){connection.textContent=t('disconnected');});};canvas.onpointercancel=function(){points=null;};function point(e){var r=canvas.getBoundingClientRect();points.push([Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))]);window.SSWorkspaceRender.paint(canvas,{paper:paper,strokes:strokes},{tool:'pen',points:points,color:'#333333',width:3});}button(t('new_page'),function(){return event('page',{});},root);button(t('end_session'),function(){return event('end',{});},root);}else button(t('raise_hand'),function(){return event('hand',{name:account.name||account.username});},root,true);
      async function poll(){if(!alive||!document.contains(canvas)||ended)return;try{await flushPending();var r=await api('/sessions/'+id+'?after='+seq);if(!alive||!document.contains(canvas))return;ingest(r);if(!ended)connection.textContent=t('connected');}catch(e){if(alive)connection.textContent=t('disconnected');}if(alive&&!ended)timer=setTimeout(poll,2500);}timer=setTimeout(poll,2500);
    }
    run(start);
  }
  window.SSClassroom={init:init};
})();
