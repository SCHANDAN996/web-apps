/* APK-local study engine. Content requests never use the study API or learner cookie. */
(function () {
  'use strict';
  var KEY = 'ss_offline_progress_v1', MAX_BACKUP = 4 * 1024 * 1024;
  var boot = JSON.parse(document.getElementById('ss-boot').textContent), SS = window.SS = {};
  SS.lang = boot.lang === 'en' ? 'en' : 'hi'; SS.t = boot.t || {};
  var assetVersion = new URL(document.querySelector('script[src*="offline-study.js"]').src).searchParams.get('v');
  var root, catalog, books, manifest, subjects = [], topics = [], questions = new Map(), generation = 0, leaving = [], session = null;
  function t(key) { return SS.t['offline_' + key] || SS.t[key] || key; }
  function h(tag, attrs) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var val = attrs[key]; if (val === false || val == null) return;
      if (key.slice(0, 2) === 'on') node.addEventListener(key.slice(2), val);
      else node.setAttribute(key, val === true ? '' : String(val));
    });
    function append(item) {
      if (item == null || item === false) return;
      if (Array.isArray(item)) item.forEach(append);
      else node.appendChild(item instanceof Node ? item : document.createTextNode(String(item)));
    }
    for (var i = 2; i < arguments.length; i++) append(arguments[i]);
    return node;
  }
  SS.h = h;
  SS.icon = function (id, cls) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'icon ' + (cls || ''));
    var use = document.createElementNS(svg.namespaceURI, 'use'); use.setAttribute('href', '#i-' + id); svg.appendChild(use); return svg;
  };
  SS.onLeave = function (fn) { leaving.push(fn); };
  SS.toast = function (msg) { var n = h('div', { class:'toast', role:'status' }, msg); document.body.appendChild(n); setTimeout(function () { n.remove(); }, 3500); };
  function emptyState() { return {version:1,reading:[],last:null,answers:{},history:[],active:null,imported:[],migratedReading:false}; }
  function readState() {
    try { var v = JSON.parse(localStorage.getItem(KEY)); return validateState(v); } catch (e) { return emptyState(); }
  }
  function object(v) { return v && typeof v === 'object' && !Array.isArray(v); }
  function validateState(v) {
    if (!object(v) || v.version !== 1 || !Array.isArray(v.reading) || !Array.isArray(v.history) || !object(v.answers)) throw Error('invalid');
    if (v.reading.length > 5000 || v.history.length > 20000 || Object.keys(v.answers).length > 100000) throw Error('invalid');
    if (!v.reading.every(function (s) { return typeof s === 'string' && /^[a-z0-9-]+\/[a-z0-9-]+$/.test(s); })) throw Error('invalid');
    var clean = emptyState(); clean.reading = Array.from(new Set(v.reading));
    Object.keys(v.answers).forEach(function (id) {
      var a = v.answers[id];
      if (!/^[1-9][0-9]{0,9}$/.test(id) || !object(a) || !Number.isInteger(a.topic) || !Number.isInteger(a.pick) || a.pick < 0 || a.pick > 9 || typeof a.correct !== 'boolean' || !Number.isFinite(a.at)) throw Error('invalid');
      clean.answers[id] = {topic:a.topic,pick:a.pick,correct:a.correct,at:a.at};
    });
    clean.migratedReading = v.migratedReading === true;
    clean.imported = Array.isArray(v.imported)?v.imported.filter(function(x){return typeof x==='string'&&x.length<100;}).slice(0,5000):[];
    clean.history = v.history.map(function (s) {
      if (!object(s) || !Number.isFinite(s.at) || !Number.isInteger(s.total) || s.total < 1 || s.total > 500 || !Number.isInteger(s.correct) || s.correct < 0 || s.correct > s.total || !Array.isArray(s.topics) || !s.topics.every(Number.isInteger)) throw Error('invalid');
      return {at:s.at,total:s.total,correct:s.correct,topics:s.topics.slice(0,100),mode:s.mode === 'mock' ? 'mock' : 'practice',score:Number.isFinite(s.score)?s.score:s.correct,maxScore:Number.isFinite(s.maxScore)?s.maxScore:s.total};
    });
    clean.last = typeof v.last === 'string' && /^[a-z0-9-]+\/[a-z0-9-]+$/.test(v.last) ? v.last : null;
    if (v.active != null) {
      var a = v.active;
      if (!object(a) || !Array.isArray(a.ids) || a.ids.length > 500 || !a.ids.every(function (id) { return Number.isInteger(id) && id > 0; }) || !Array.isArray(a.topicIds) || !a.topicIds.every(Number.isInteger) || !object(a.picks) || !Number.isInteger(a.index) || a.index < 0 || a.index >= a.ids.length) throw Error('invalid');
      var picks = {}; Object.keys(a.picks).forEach(function (id) { var p = a.picks[id]; if (a.ids.indexOf(Number(id)) < 0 || !Number.isInteger(p) || p < 0 || p > 9) throw Error('invalid'); picks[id] = p; });
      var rules={};Object.keys(a.rules||{}).forEach(function(id){var r=a.rules[id];if(a.ids.indexOf(Number(id))<0||!object(r)||!Number.isFinite(r.marks)||r.marks<0||r.marks>100||!Number.isFinite(r.negative)||r.negative<0||r.negative>100)throw Error('invalid');rules[id]={marks:r.marks,negative:r.negative};});
      clean.active = {ids:a.ids,topicIds:a.topicIds,picks:picks,index:a.index,mode:a.mode === 'mock' ? 'mock' : 'practice',deadline:Number.isFinite(a.deadline) ? a.deadline : null,finished:false,rules:rules};
    }
    return clean;
  }
  var state = readState(), progressDB = null, pendingSave = Promise.resolve();
  function openProgress() {
    return new Promise(function(resolve,reject){
      var req=indexedDB.open('ss-offline-progress',1);
      req.onupgradeneeded=function(){req.result.createObjectStore('state');};
      req.onerror=function(){reject(req.error);};
      req.onsuccess=function(){progressDB=req.result;var tx=progressDB.transaction('state','readonly'),r=tx.objectStore('state').get('current');r.onsuccess=function(){try{if(r.result)state=validateState(r.result);var reading=[];try{if(!state.migratedReading)reading=JSON.parse(localStorage.getItem('ss_read_chapters')||'[]');}catch(ignored){}if(Array.isArray(reading))reading.forEach(function(u){var m=typeof u==='string'&&/^\/books\/([a-z0-9-]+\/[a-z0-9-]+)/.exec(u);if(m&&state.reading.indexOf(m[1])<0)state.reading.push(m[1]);});state.migratedReading=true;resolve();}catch(e){reject(e);}};r.onerror=function(){reject(r.error);};};
    });
  }
  function save() {
    if(!progressDB){SS.toast(t('storage_full'));return false;}
    var snapshot=JSON.parse(JSON.stringify(state));
    pendingSave=pendingSave.catch(function(){}).then(function(){return new Promise(function(resolve,reject){var tx=progressDB.transaction('state','readwrite');tx.objectStore('state').put(snapshot,'current');tx.oncomplete=resolve;tx.onerror=function(){reject(tx.error);};tx.onabort=function(){reject(tx.error);};});});
    pendingSave.catch(function(){SS.toast(t('storage_full'));}); return true;
  }
  function name(o) { return o['name_' + SS.lang] || o['title_' + SS.lang] || o.name_hi || o.title_hi || o.slug || ''; }
  function local(path) {
    if (typeof path !== 'string' || !/^[a-zA-Z0-9_./-]+\.json$/.test(path) || path.indexOf('..') >= 0) return Promise.reject(Error('path'));
    return fetch('/offline-content/' + path, {credentials:'omit',cache:'force-cache'}).then(function (r) { if (!r.ok) throw Error('content'); return r.json(); });
  }
  function topicBy(id) { return topics.find(function (o) { return o.id === Number(id); }); }
  function loadTopic(id) {
    id = Number(id); if (questions.has(id)) return Promise.resolve(questions.get(id));
    var topic = topicBy(id); if (!topic) return Promise.resolve([]);
    return local(topic.questions_path || ('questions/' + id + '.json')).then(function (rows) {
      if (!Array.isArray(rows)) throw Error('content'); questions.set(id, rows);
      // Keep only a few topic files in memory on low-RAM phones. The APK remains the source.
      if (questions.size > 3) questions.delete(questions.keys().next().value);
      return rows;
    });
  }
  function button(label, fn, cls) { return h('button', {type:'button',class:'btn ' + (cls || 'btn-secondary'),onclick:fn}, label); }
  function link(label, hash, cls) { return h('a', {href:'#' + hash,class:cls || 'btn btn-secondary'}, label); }
  function heading(label, back) { root.appendChild(h('div', {class:'offline-heading'}, h('h1', {}, label), back ? link(t('back'), back, 'btn btn-ghost') : null)); }
  function card(title, description, hash, image) {
    return h('a',{href:'#'+hash,class:'home-image-card'},h('img',{src:'/static/illustrations/'+image+'.svg?v='+assetVersion,width:72,height:64,alt:'',loading:'lazy'}),h('strong',{class:'home-card-title'},title),h('span',{class:'muted'},description));
  }
  function go(path) { if (path.charAt(0) === '#') location.hash = path; else if (path.charAt(0) === '/') location.href = path; else location.hash = '#' + path; }
  SS.go = go;
  function notice(text) { root.appendChild(h('p',{class:'offline-alert'},text)); }
  function home() {
    heading(t('home_title'));var answered=Object.keys(state.answers).length,wrong=Object.keys(state.answers).filter(function(id){return !state.answers[id].correct;}).length;
    var action=state.active?button(t('resume'),resume,'btn-primary'):link(state.last?t('continue_reading'):t('open_book'),state.last?'chapter/'+state.last:'books','btn btn-primary');
    root.appendChild(h('section',{class:'offline-hero'},h('div',{class:'offline-hero-copy'},h('span',{class:'offline-badge'},SS.icon('check'),t('offline_badge')),h('h2',{},state.last?t('continue_reading'):t('hero_title')),h('p',{},t('hero_hint')),action),h('img',{class:'offline-hero-art',src:'/static/illustrations/read.svg?v='+assetVersion,width:96,height:72,alt:''}),h('div',{class:'offline-summary'},h('span',{},h('b',{},state.reading.length),t('read_chapters')),h('span',{},h('b',{},answered),t('answered')),h('span',{},h('b',{},wrong),t('revision')))));
    root.appendChild(h('h2',{class:'offline-section-title'},t('study_tools')));
    root.appendChild(h('div',{class:'home-card-grid'},[
      card(t('books'),t('books_hint'),'books','read'),card(t('practice'),t('practice_hint'),'practice','practice'),
      card(t('revision'),t('revision_hint'),'revision','revise'),card(t('mock'),t('mock_hint'),'mock','mock')
    ]));
    root.appendChild(h('h2',{class:'offline-section-title'},t('explore')));
    var more=h('div',{class:'home-card-grid offline-secondary-grid'},card(t('questions'),t('questions_hint'),'questions','questions'),card(t('progress'),t('progress_hint'),'progress','progress'));
    [['jobs','jobs_online','jobs'],['current-affairs','ca_online','news']].forEach(function(item){more.appendChild(h('a',{class:'home-image-card',href:'/'+item[0]},h('img',{src:'/static/illustrations/'+item[2]+'.svg?v='+assetVersion,width:72,height:60,alt:'',loading:'lazy'}),h('strong',{class:'home-card-title'},t(item[1])),h('span',{class:'muted'},t('online_updates'))));});root.appendChild(more);
    root.appendChild(link(t('settings'),'settings','btn btn-ghost btn-block'));
  }
  function bookList() {
    heading(t('books'),'home');notice(t('books_hint'));
    var search=h('input',{type:'search',class:'offline-book-search',placeholder:t('search_books'),'aria-label':t('search_books')}),filters=h('div',{class:'offline-tabs'}),list=h('div',{class:'offline-list offline-book-grid'}),level='';
    function paint(){var term=search.value.toLocaleLowerCase();list.replaceChildren();books.filter(function(book){return(!level||book.level===level)&&(!term||name(book).toLocaleLowerCase().indexOf(term)>=0);}).forEach(function(book){list.appendChild(h('a',{href:'#book/'+book.slug,class:'offline-card offline-book-card'},h('img',{src:'/static/illustrations/read.svg?v='+assetVersion,width:72,height:54,alt:'',loading:'lazy'}),h('strong',{},name(book)),h('span',{class:'muted'},book.chapters.length+' '+t('chapters'))));});if(!list.children.length)list.appendChild(h('p',{class:'muted'},t('no_content')));}
    [['',t('all_levels')],['10th',t('level_10th')],['12th',t('level_12th')],['graduate',t('level_graduate')]].forEach(function(item){var b=button(item[1],function(){level=item[0];filters.querySelectorAll('button').forEach(function(o){o.setAttribute('aria-pressed',String(o===b));});paint();},'btn-secondary btn-sm');b.setAttribute('aria-pressed',String(!item[0]));filters.appendChild(b);});search.addEventListener('input',paint);root.append(search,filters,list);paint();
  }
  function chapters(slug) {
    var book = books.find(function (b) { return b.slug === slug; }); if (!book) throw Error('book');
    heading(name(book),'books'); root.appendChild(h('div',{class:'offline-list'},book.chapters.map(function (c) {
      var id = book.slug+'/'+c.slug; return link((state.reading.indexOf(id)>=0?'✓ ':'')+c.number+'. '+name(c),'chapter/'+id,'offline-card');
    })));
  }
  function chapter(bookSlug, chapterSlug, section) {
    var book = books.find(function (b) { return b.slug === bookSlug; });
    var c = book && book.chapters.find(function (o) { return o.slug === chapterSlug; }); if (!c) throw Error('chapter');
    var token = generation; heading(name(c),'book/'+bookSlug);
    return local(c.path).then(function (data) {
      if (token !== generation) return;
      var sections = data.sections || [], chosen = sections.find(function (o) { return o.slug === section; }) || sections[0];
      root.appendChild(h('nav',{class:'offline-tabs','aria-label':t('sections')},sections.map(function (s) {
        var a = link(t('section_'+s.slug) === 'section_'+s.slug ? s.key : t('section_'+s.slug),'chapter/'+bookSlug+'/'+chapterSlug+'/'+s.slug);
        if (s === chosen) a.setAttribute('aria-current','page'); return a;
      })));
      if (!chosen) { notice(t('no_content')); return; }
      var texts = chosen.content || {}, text = texts[SS.lang] || texts['*'] || texts.hi || texts.en || '';
      if (!texts[SS.lang]) notice(t('language_fallback'));
      var reader = h('article',{class:'offline-reader',lang:texts[SS.lang] ? SS.lang : 'und'});
      text.split(/\r?\n\s*\r?\n/).forEach(function (p) { reader.appendChild(h('p',{},p)); }); root.appendChild(reader);
      var id = bookSlug+'/'+chapterSlug; state.last = id; save();
      root.appendChild(button(state.reading.indexOf(id)>=0?t('read_done'):t('mark_read'),function () {
        if (state.reading.indexOf(id)<0) state.reading.push(id); save(); route();
      },'btn-primary'));
      if (c.topic) {
        var sub = subjects.find(function (s) { return s.slug === c.topic[0]; });
        var top = sub && sub.topics.find(function (o) { return o.slug === c.topic[1]; });
        if (top) root.appendChild(link(t('practice'),'practice/'+top.id));
      }
    });
  }
  function selection(selected) {
    var sub = h('select',{'aria-label':t('subject')}), top = h('select',{'aria-label':t('topic')});
    sub.appendChild(h('option',{value:''},t('choose_subject')));
    subjects.forEach(function (s) { sub.appendChild(h('option',{value:s.id},name(s))); });
    function fill() {
      top.replaceChildren(h('option',{value:''},t('choose_topic')));
      var s = subjects.find(function (s) { return s.id === Number(sub.value); });
      (s ? s.topics : []).forEach(function (o) { if (o.question_count) top.appendChild(h('option',{value:o.id},name(o)+' ('+o.question_count+')')); });
    }
    sub.addEventListener('change',fill);
    if(!selected){var first=topics.find(function(o){return o.question_count;});if(first)selected=first.id;}
    if (selected) { var o = topicBy(selected); if (o) sub.value = o.subject_id; } fill(); if (selected) top.value = selected;
    return {sub:sub,top:top,node:h('div',{class:'offline-form'},h('label',{},t('subject'),sub),h('label',{},t('topic'),top))};
  }
  function questionText(q) { return q['text_'+SS.lang] || q.text_hi || q.text_en || ''; }
  function options(q) { return q['options_'+SS.lang] || q.options_hi || q.options_en || []; }
  function questionCard(q, reveal, onAnswer) {
    var box = h('section',{class:'offline-card'}), opts = options(q), picked = null;
    box.appendChild(h('p',{class:'xs muted'},'#'+q.id+' · '+(q.review_status === 'verified' ? t('verified') : q.source_type === 'ai_generated' ? t('ai_generated') : t('review_pending'))));
    box.appendChild(h('h2',{class:'offline-question'},questionText(q)));
    if (!q['text_'+SS.lang]) box.appendChild(h('p',{class:'xs muted'},t('language_fallback')));
    var choices = h('div',{class:'offline-options'}), feedback = h('div',{'aria-live':'polite'});
    opts.forEach(function (text,index) {
      var choice = button(String.fromCharCode(65+index)+'. '+text,function () {
        if (picked != null && reveal) return; picked = index;
        choices.querySelectorAll('button').forEach(function (b,n) { b.setAttribute('aria-pressed',String(n===index)); });
        if (reveal) {
          choices.querySelectorAll('button').forEach(function (b,n) { b.disabled = true; if(n===q.answer_index) b.dataset.result='correct'; else if(n===index) b.dataset.result='wrong'; });
          feedback.appendChild(h('strong',{},index===q.answer_index?t('correct'):t('incorrect')));
          feedback.appendChild(h('p',{class:'offline-question'},q['solution_'+SS.lang] || q.solution_hi || q.solution_en || t('no_solution')));
        }
        if (onAnswer) onAnswer(index);
      },'btn-secondary offline-option'); choice.setAttribute('aria-pressed','false'); choices.appendChild(choice);
    });
    box.appendChild(choices); box.appendChild(feedback);
    if (window.SSWhiteboard) box.appendChild(window.SSWhiteboard.create(q.id));
    return box;
  }
  function bank(selected) {
    heading(t('questions'),'home'); var pick = selection(selected), difficulty = h('select',{'aria-label':t('difficulty')},h('option',{value:''},t('all_difficulties')));
    ['easy','medium','hard'].forEach(function (d) { difficulty.appendChild(h('option',{value:d},t(d))); });
    var search = h('input',{type:'search',maxlength:120,placeholder:t('search'),'aria-label':t('search')});
    root.appendChild(pick.node); root.appendChild(h('div',{class:'offline-form'},h('label',{},t('difficulty'),difficulty),h('label',{},t('search'),search)));
    var results=h('div',{class:'offline-list'}), page=0, rows=[], token=generation; root.appendChild(results);
    function paint() {
      var term=search.value.toLocaleLowerCase(), filtered=rows.filter(function (q) { return (!difficulty.value || q.difficulty===difficulty.value) && (!term || (questionText(q)+' '+q.id).toLocaleLowerCase().indexOf(term)>=0); });
      if(page*20>=filtered.length) page=0; results.replaceChildren(h('p',{class:'muted'},t('questions')+': '+filtered.length));
      filtered.slice(page*20,page*20+20).forEach(function (q) { results.appendChild(button('#'+q.id+' · '+questionText(q),function () { go('question/'+q.topic_id+'/'+q.id); },'btn-secondary offline-option')); });
      var prev=button(t('previous'),function(){page--;paint();}), next=button(t('next'),function(){page++;paint();}); prev.disabled=page===0; next.disabled=(page+1)*20>=filtered.length;
      results.appendChild(h('div',{class:'offline-row'},prev,h('span',{},String(page+1)),next));
    }
    var loadGeneration=0; function load() { var currentLoad=++loadGeneration; page=0; rows=[]; results.replaceChildren(h('p',{},t('loading'))); if(!pick.top.value){results.replaceChildren(h('p',{},t('choose_topic')));return;} loadTopic(pick.top.value).then(function(r){if(token===generation&&currentLoad===loadGeneration){rows=r;paint();}}).catch(showError); }
    pick.top.addEventListener('change',load); pick.sub.addEventListener('change',load); difficulty.addEventListener('change',function(){page=0;paint();}); search.addEventListener('input',function(){page=0;paint();}); load();
  }
  function oneQuestion(topic,id) { heading(t('questions'),'questions/'+topic); var token=generation; return loadTopic(topic).then(function(rows){if(token!==generation)return;var q=rows.find(function(q){return q.id===Number(id);});if(!q)throw Error('question');root.appendChild(questionCard(q,true,function(index){record(q,index);}));}); }
  function record(q,index,defer) { state.answers[q.id]={topic:q.topic_id,pick:index,correct:index===q.answer_index,at:Date.now()}; if(!defer)save(); }
  function shuffle(rows) { var copy=rows.slice(); for(var i=copy.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),v=copy[i];copy[i]=copy[j];copy[j]=v;}return copy; }
  function practice(selected) {
    heading(t('practice'),'home'); var pick=selection(selected), count=h('select',{'aria-label':t('session_size')}); [10,20,50].forEach(function(n){count.appendChild(h('option',{value:n},n));});
    root.appendChild(pick.node); root.appendChild(h('label',{class:'offline-row'},t('session_size'),count));
    var start=button(t('start'),function(){if(!pick.top.value){SS.toast(t('choose_topic'));return;}start.disabled=true;loadTopic(pick.top.value).then(function(rows){begin(shuffle(rows).slice(0,Number(count.value)),'practice');start.disabled=false;}).catch(function(){start.disabled=false;showError();});},'btn-primary');root.appendChild(start);
  }
  function begin(rows,mode,minutes,rules) {
    if(!rows.length){SS.toast(t('no_content'));return;}
    if(state.active && !window.confirm(t('replace_session')))return;
    session={rows:rows,index:0,picks:{},mode:mode,deadline:minutes?Date.now()+minutes*60000:null,rules:rules||{}}; persistSession();go('session');
  }
  function persistSession(){if(!session)return;state.active={ids:session.rows.map(function(q){return q.id;}),topicIds:Array.from(new Set(session.rows.map(function(q){return q.topic_id;}))),picks:session.picks,index:session.index,mode:session.mode,deadline:session.deadline,rules:session.rules||{}};save();}
  async function resume(){
    var a=state.active;if(!a)return;var token=generation,ids=new Set(a.ids),byId=new Map();
    try{for(var i=0;i<a.topicIds.length;i++){var rows=await loadTopic(a.topicIds[i]);if(token!==generation)return;rows.forEach(function(q){if(ids.has(q.id))byId.set(q.id,q);});}
      session={rows:a.ids.map(function(id){return byId.get(id);}).filter(Boolean),index:a.index,picks:a.picks,mode:a.mode,deadline:a.deadline,rules:a.rules||{}};
      if(!session.rows.length){state.active=null;save();SS.toast(t('no_content'));return;}
      session.index=Math.min(session.index,session.rows.length-1);if(location.hash==='#session')route();else go('session');
    }catch(e){showError();}
  }
  function sessionView(){
    if(!session){if(state.active){resume();return;}go('practice');return;}
    heading(session.mode==='mock'?t('mock'):t('practice'),'home'); var q=session.rows[session.index];var palette=h('nav',{class:'offline-palette','aria-label':t('questions')});session.rows.forEach(function(item,index){var b=button(String(index+1),function(){session.index=index;persistSession();route();},'btn-ghost');if(index===session.index)b.setAttribute('aria-current','step');if(Object.prototype.hasOwnProperty.call(session.picks,item.id))b.classList.add('is-answered');palette.appendChild(b);});root.appendChild(palette);
    root.appendChild(h('p',{},(session.index+1)+' / '+session.rows.length));
    if(session.deadline){var timer=h('p',{role:'timer'});root.appendChild(timer);function tick(){var remain=Math.max(0,Math.ceil((session.deadline-Date.now())/1000));timer.textContent=t('time_left')+' '+Math.floor(remain/60)+':'+String(remain%60).padStart(2,'0');if(!remain)finishSession();}tick();if(!session)return;var interval=setInterval(tick,1000);SS.onLeave(function(){clearInterval(interval);});}
    root.appendChild(questionCard(q,session.mode!=='mock',function(index){session.picks[q.id]=index;if(session.mode!=='mock')record(q,index,true);persistSession();}));
    if(Object.prototype.hasOwnProperty.call(session.picks,q.id)){
      var choices=root.querySelectorAll('.offline-option');choices.forEach(function(b,n){b.setAttribute('aria-pressed',String(n===session.picks[q.id]));if(session.mode!=='mock'){b.disabled=true;if(n===q.answer_index)b.dataset.result='correct';else if(n===session.picks[q.id])b.dataset.result='wrong';}});
      if(session.mode!=='mock')root.appendChild(h('p',{class:'offline-question'},q['solution_'+SS.lang]||q.solution_hi||q.solution_en||t('no_solution')));
    }
    var prev=button(t('previous'),function(){session.index--;persistSession();route();}),next=button(t('next'),function(){session.index++;persistSession();route();});prev.disabled=session.index===0;next.disabled=session.index===session.rows.length-1;
    root.appendChild(h('div',{class:'offline-row'},prev,next,button(t('finish'),function(){if(window.confirm(t('finish_confirm')))finishSession();},'btn-primary')));
  }
  function finishSession(){if(!session||session.finished)return;session.finished=true;var correct=0,score=0,maxScore=0;session.rows.forEach(function(q){var r=(session.rules||{})[q.id]||{marks:1,negative:0};maxScore+=r.marks;if(Object.prototype.hasOwnProperty.call(session.picks,q.id))score+=session.picks[q.id]===q.answer_index?r.marks:-r.negative;});session.rows.forEach(function(q){if(Object.prototype.hasOwnProperty.call(session.picks,q.id)){record(q,session.picks[q.id],true);if(session.picks[q.id]===q.answer_index)correct++;}});var result={at:Date.now(),total:session.rows.length,correct:correct,topics:Array.from(new Set(session.rows.map(function(q){return q.topic_id;}))),mode:session.mode,score:score,maxScore:maxScore};state.history.unshift(result);state.active=null;save();var rows=session.rows,picks=session.picks;session=null;go('result');setTimeout(function(){if(location.hash!=='#result')return;root.replaceChildren();heading(t('result'),'home');root.appendChild(h('p',{class:'offline-score'},Number(score.toFixed(2))+' / '+maxScore));rows.forEach(function(q){root.appendChild(h('section',{class:'offline-card'},h('h2',{class:'offline-question'},questionText(q)),h('p',{},t('your_answer')+': '+(options(q)[picks[q.id]]||t('unanswered'))),h('p',{},t('correct_answer')+': '+options(q)[q.answer_index]),h('p',{class:'offline-question'},q['solution_'+SS.lang]||q.solution_hi||q.solution_en||'')));});},0);}
  function revision(){heading(t('revision'),'home');var wrong=Object.keys(state.answers).filter(function(id){return !state.answers[id].correct;});notice(t('revision_count')+' '+wrong.length);if(!wrong.length)return;root.appendChild(button(t('start'),function(){var ids=new Set(wrong.map(Number)),topicIds=Array.from(new Set(wrong.map(function(id){return state.answers[id].topic;}))),token=generation;Promise.all(topicIds.map(loadTopic)).then(function(groups){if(token===generation)begin(shuffle(groups.flat().filter(function(q){return ids.has(q.id);})).slice(0,50),'practice');}).catch(showError);},'btn-primary'));}
  function mocks(){
    heading(t('mock'),'home');notice(t('mock_note'));
    (catalog.exams||[]).forEach(function(exam){
      var b=button(name(exam)+' · '+exam.duration_min+' '+t('minutes'),async function(){
        var token=generation;b.disabled=true;
        try {
          var picked=[],rules={},complete=true;
          for(var si=0;si<exam.sections.length;si++) {
            var section=exam.sections[si],pool=[],seen=0,eligible=topics.filter(function(top){return top.subject_id===section.subject_id&&top.question_count;});
            for(var ti=0;ti<eligible.length;ti++) {
              var rows=await loadTopic(eligible[ti].id);if(token!==generation)return;
              rows.forEach(function(q){if(exam.level&&q.level!==exam.level)return;seen++;if(pool.length<section.questions)pool.push(q);else{var slot=Math.floor(Math.random()*seen);if(slot<section.questions)pool[slot]=q;}});
            }
            if(pool.length!==section.questions)complete=false;
            pool.forEach(function(q){rules[q.id]={marks:section.marks_per_q,negative:section.negative_per_q};});picked=picked.concat(shuffle(pool));
          }
          b.disabled=false;if(!complete){SS.toast(t('no_content'));return;}begin(picked,'mock',exam.duration_min,rules);
        }catch(e){b.disabled=false;showError();}
      },'btn-secondary offline-option');root.appendChild(b);
    });
  }
  function progress(){heading(t('progress'),'home');var answers=Object.keys(state.answers),right=answers.filter(function(id){return state.answers[id].correct;}).length;root.appendChild(h('div',{class:'offline-card'},h('p',{},t('read_chapters')+': '+state.reading.length),h('p',{},t('answered')+': '+answers.length),h('p',{},t('correct')+': '+right),h('p',{},t('sessions')+': '+state.history.length)));root.appendChild(h('div',{class:'offline-list offline-history'},state.history.map(function(s){return h('div',{class:'offline-card'},h('strong',{},new Date(s.at).toLocaleString(SS.lang==='hi'?'hi-IN':'en-IN')),h('p',{},t(s.mode)+' · '+(s.score==null?s.correct:Number(s.score.toFixed(2)))+' / '+(s.maxScore==null?s.total:s.maxScore)));})));}
  function resetOptions(){var select=h('select',{'aria-label':t('reset_scope')},h('option',{value:'all'},t('reset_all')));subjects.forEach(function(s){select.appendChild(h('option',{value:'subject:'+s.id},t('subject')+': '+name(s)));});books.forEach(function(b){b.chapters.forEach(function(c){select.appendChild(h('option',{value:'chapter:'+b.slug+'/'+c.slug},name(b)+' / '+name(c)));});});return select;}
  function reset(scope){
    if(!window.confirm(t('reset_confirm')))return;
    if(scope==='all'){state=emptyState();state.migratedReading=true;session=null;if(window.SSWhiteboard)window.SSWhiteboard.clearAll();}
    else{
      var topicIds=new Set(),chapterIds=new Set();
      if(scope.indexOf('subject:')===0){var sid=Number(scope.slice(8)),sub=subjects.find(function(s){return s.id===sid;});topics.forEach(function(o){if(o.subject_id===sid)topicIds.add(o.id);});books.forEach(function(b){b.chapters.forEach(function(c){if((sub&&c.topic&&c.topic[0]===sub.slug)||(sub&&b.subject===sub.slug))chapterIds.add(b.slug+'/'+c.slug);});});}
      else{var id=scope.slice(8);chapterIds.add(id);books.forEach(function(b){b.chapters.forEach(function(c){if(b.slug+'/'+c.slug===id&&c.topic){var sub=subjects.find(function(s){return s.slug===c.topic[0];}),top=sub&&sub.topics.find(function(o){return o.slug===c.topic[1];});if(top)topicIds.add(top.id);}});});}
      var deleted=[];Object.keys(state.answers).forEach(function(id){if(topicIds.has(state.answers[id].topic)){deleted.push(id);delete state.answers[id];}});if(window.SSWhiteboard)window.SSWhiteboard.remove(deleted);
      state.reading=state.reading.filter(function(id){return !chapterIds.has(id);});if(chapterIds.has(state.last))state.last=null;
      // Preserve mixed-subject sessions; only erase sessions entirely inside the chosen scope.
      state.history=state.history.filter(function(s){return !s.topics.length||!s.topics.every(function(id){return topicIds.has(id);});});
      if(state.active&&state.active.topicIds.some(function(id){return topicIds.has(id);})){state.active=null;session=null;}
    }save();SS.toast(t('reset_done'));route();
  }
  function exportBackup(){var data={format:'study-station-offline-backup',version:1,created_at:new Date().toISOString(),progress:state,whiteboards:window.SSWhiteboard?window.SSWhiteboard.export():{}};return JSON.stringify(data);}
  async function restoreBackup(raw){if(object(raw))raw=JSON.stringify(raw);if(typeof raw!=='string'||new TextEncoder().encode(raw).length>MAX_BACKUP)throw Error('invalid');var data=JSON.parse(raw);if(data.format!=='study-station-offline-backup'||data.version!==1)throw Error('invalid');var next=validateState(data.progress),boards=window.SSWhiteboard?window.SSWhiteboard.validate(data.whiteboards||{}):{};if(!window.confirm(t('restore_confirm')))return;var before=state;state=next;if(!save()){state=before;throw Error('storage');}try{await pendingSave;}catch(error){state=before;throw error;}if(window.SSWhiteboard)window.SSWhiteboard.merge(boards);session=null;SS.toast(t('restored'));route();}

  async function importPrevious() {
    if(!window.confirm(t('import_server_confirm')))return;
    try {
      var response=await fetch('/api/v1/backup/export',{credentials:'same-origin',cache:'no-store'});
      if(!response.ok)throw Error('network');
      var old=await response.json();
      if(old.schema_version!==1||!Array.isArray(old.attempts)||old.attempts.length>1000||typeof old.source_id!=='string')throw Error('invalid');
      var needed=new Set(),meta=new Map();old.attempts.forEach(function(a){(a.question_ids||[]).forEach(function(id){needed.add(id);});});
      for(var i=0;i<topics.length;i++) {var rows=await loadTopic(topics[i].id);rows.forEach(function(q){if(needed.has(q.id))meta.set(q.id,{topic:q.topic_id,answer:q.answer_index});});}
      old.attempts.forEach(function(a){
        var receipt=old.source_id+':'+a.id;if(state.imported.indexOf(receipt)>=0)return;
        var correct=0,score=0,max=0,ids=[],exam=(catalog.exams||[]).find(function(e){return e.slug===a.exam;});
        var answerMap=new Map((a.answers||[]).map(function(x){return[x.question_id,x];}));
        (a.question_ids||[]).forEach(function(id){var q=meta.get(id);if(!q)return;ids.push(q.topic);var top=topicBy(q.topic),rule=exam&&exam.sections.find(function(section){return top&&section.subject_id===top.subject_id;}),marks=rule?rule.marks_per_q:1,negative=rule?rule.negative_per_q:0;max+=marks;var answer=answerMap.get(id);if(!answer||!Number.isInteger(answer.chosen_index))return;var right=answer.chosen_index===q.answer,at=Date.parse(answer.answered_at);if(!Number.isFinite(at))return;if(right){correct++;score+=marks;}else score-=negative;if(!state.answers[id]||state.answers[id].at<at)state.answers[id]={topic:q.topic,pick:answer.chosen_index,correct:right,at:at};});
        if(a.finished_at&&ids.length)state.history.unshift({at:Date.parse(a.finished_at),total:ids.length,correct:correct,topics:Array.from(new Set(ids)),mode:a.mode==='mock'?'mock':'practice',score:score,maxScore:max});
        state.imported.push(receipt);
      });
      save();await pendingSave;SS.toast(t('import_server_done'));route();
    }catch(e){SS.toast(t('import_server_failed'));}
  }
  function settings(){heading(t('settings'),'home');notice(t('local_notice'));notice(t('server_progress'));root.appendChild(h('a',{href:'/progress',class:'btn btn-secondary'},t('view_server_progress')));root.appendChild(button(t('import_server'),importPrevious));var scope=resetOptions();root.appendChild(h('section',{class:'offline-card offline-stack'},h('h2',{},t('reset')),h('p',{},t('reset_note')),scope,button(t('reset'),function(){reset(scope.value);},'btn-secondary')));
    var status=h('p',{role:'status'}),file=h('input',{type:'file',accept:'application/json,.json',hidden:true});file.addEventListener('change',function(){var f=file.files[0];file.value='';if(!f)return;if(f.size>MAX_BACKUP){status.textContent=t('invalid_backup');return;}f.text().then(restoreBackup).catch(function(){status.textContent=t('invalid_backup');});});
    root.appendChild(h('section',{class:'offline-card offline-stack'},h('h2',{},t('backup')),h('p',{},t('backup_note')),button(t('export'),function(){var raw=exportBackup(),bridge=window.StudyStationNative;if(new TextEncoder().encode(raw).length>MAX_BACKUP){status.textContent=t('invalid_backup');return;}if(bridge&&typeof bridge.requestLocalBackup==='function'){bridge.requestLocalBackup(raw);return;}var url=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=h('a',{href:url,download:'study-station-offline-'+new Date().toISOString().slice(0,10)+'.json'});document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},1000);}),button(t('import'),function(){var bridge=window.StudyStationNative;if(bridge&&typeof bridge.requestLocalRestore==='function')bridge.requestLocalRestore();else file.click();}),file,status));
  }
  function showError(){if(root)root.appendChild(h('p',{class:'offline-alert',role:'alert'},t('load_error')));}
  function route(){generation++;leaving.splice(0).forEach(function(fn){try{fn();}catch(e){}});root.replaceChildren();window.scrollTo(0,0);var parts=location.hash.slice(1).split('/'),page=parts[0]||'home';document.querySelectorAll('.tabbar a').forEach(function(a){a.removeAttribute('aria-current');if(a.getAttribute('href')==='#'+page)a.setAttribute('aria-current','page');});try{var result=page==='home'?home():page==='books'?bookList():page==='book'?chapters(parts[1]):page==='chapter'?chapter(parts[1],parts[2],parts[3]):page==='questions'?bank(parts[1]):page==='question'?oneQuestion(parts[1],parts[2]):page==='practice'?practice(parts[1]):page==='session'?sessionView():page==='revision'?revision():page==='mock'?mocks():page==='progress'?progress():page==='settings'?settings():page==='result'?heading(t('result'),'home'):home();if(result&&result.catch)result.catch(showError);}catch(e){showError();}}
  function init(){root=document.getElementById('offlineStudy');if(!root)return;document.cookie='ss_lang='+SS.lang+'; Path=/; SameSite=Lax';
    document.querySelector('.brand').setAttribute('href','#home');var settingsLink=document.querySelector('.top-actions a[href="/settings"]');if(settingsLink)settingsLink.href='#settings';
    var routes=['home','practice','mock','revision'];document.querySelectorAll('.tabbar a').forEach(function(a,index){if(index<4)a.setAttribute('href','#'+routes[index]);});
    var lang=document.getElementById('langBtn');if(lang)lang.addEventListener('click',function(){var next=SS.lang==='hi'?'en':'hi',url=new URL(location.href);url.searchParams.set('lang',next);location.href=url.pathname+url.search+url.hash;});
    document.querySelectorAll('[data-theme-set]').forEach(function(b){b.addEventListener('click',function(){window.SSTheme.set(b.dataset.themeSet);var picker=b.closest('details');if(picker)picker.removeAttribute('open');document.querySelectorAll('[data-theme-set]').forEach(function(o){o.setAttribute('aria-pressed',String(o===b));});});b.setAttribute('aria-pressed',String(window.SSTheme&&window.SSTheme.current()===b.dataset.themeSet));});
    window.addEventListener('hashchange',route);window.addEventListener('ss-drive-result',function(e){var r=e.detail;if(!r||!r.ok){if(r)SS.toast(t('backup_failed'));return;}if(r.operation==='local-restore'){restoreBackup(r.data).catch(function(){SS.toast(t('invalid_backup'));});}else if(r.operation==='local-backup')SS.toast(t('saved'));});
    Promise.all([local('catalog.json'),local('books/index.json'),local('manifest.json'),openProgress()]).then(function(data){catalog=data[0];books=data[1];manifest=data[2];subjects=catalog.subjects||[];save();topics=subjects.flatMap(function(s){return(s.topics||[]).map(function(o){return Object.assign({subject_id:s.id},o);});});route();}).catch(showError);
  }
  window.SSOffline={init:init,exportBackup:exportBackup,validateState:validateState};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
