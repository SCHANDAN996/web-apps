/* APK-local study engine. Content requests never use the study API or learner cookie. */
(function () {
  'use strict';
  var KEY = 'ss_offline_progress_v1', MAX_BACKUP = 4 * 1024 * 1024;
  var boot = JSON.parse(document.getElementById('ss-boot').textContent), SS = window.SS = {};
  SS.lang = boot.lang === 'en' ? 'en' : 'hi'; SS.t = boot.t || {};
  var assetVersion = new URL(document.querySelector('script[src*="offline-study.js"]').src).searchParams.get('v');
  var root, catalog, books, manifest, subjects = [], topics = [], questions = new Map(), generation = 0, leaving = [], session = null, lastResult = null;
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
    root.appendChild(h('h2',{class:'offline-section-title'},SS.t.classroom_home_title));
    var featured=h('div',{class:'home-card-grid home-collaboration-grid'});
    [['workspace','workspace','workspace'],['groups','group','/classroom?view=groups'],['classes','classroom','/classroom?view=classes'],['shared','linked','/classroom?view=shared']].forEach(function(item){featured.appendChild(h('a',{class:'home-image-card',href:item[2].charAt(0)==='/'?item[2]:'#'+item[2]},h('img',{src:'/static/illustrations/'+item[1]+'.svg?v='+assetVersion,width:96,height:72,alt:''}),h('strong',{class:'home-card-title'},SS.t['classroom_home_'+item[0]]),h('span',{class:'muted'},SS.t['classroom_home_'+item[0]+'_desc'])));});root.appendChild(featured);
    var action=state.active?button(t('resume'),resume,'btn-primary'):link(state.last?t('continue_reading'):t('open_book'),state.last?'chapter/'+state.last:'books','btn btn-primary');
    root.appendChild(h('section',{class:'offline-hero'},h('div',{class:'offline-hero-copy'},h('span',{class:'offline-badge'},SS.icon('check'),t('offline_badge')),h('h2',{},state.last?t('continue_reading'):t('hero_title')),action),h('img',{class:'offline-hero-art',src:'/static/illustrations/read.svg?v='+assetVersion,width:96,height:72,alt:''})));
    root.appendChild(h('h2',{class:'offline-section-title'},t('study_tools')));
    root.appendChild(h('div',{class:'home-card-grid'},[
      card(t('books'),t('books_hint'),'books','read'),card(t('practice'),t('practice_hint'),'practice','practice'),
      card(t('revision'),t('revision_hint'),'revision','revise'),card(t('mock'),t('mock_hint'),'mock','mock')
    ]));
    root.appendChild(h('div',{class:'offline-summary offline-home-stats'},h('span',{},h('b',{},state.reading.length),t('read_chapters')),h('span',{},h('b',{},answered),t('answered')),h('span',{},h('b',{},wrong),t('revision'))));
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
      var id = book.slug+'/'+c.slug; var done=state.reading.indexOf(id)>=0;return h('a',{href:'#chapter/'+id,class:'offline-card offline-chapter-link'},h('span',{class:'offline-chapter-number','aria-hidden':'true'},String(c.number).padStart(2,'0')),h('span',{class:'offline-chapter-copy'},h('strong',{},name(c)),h('span',{class:'muted'},done?t('read_done'):t('open_chapter'))),SS.icon(done?'check':'chev'));
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
      var toolbar=h('div',{class:'offline-reader-tools',role:'group','aria-label':t('text_size')}),size=Number(localStorage.getItem('ss_offline_reader_size')||17);if(size<15||size>24)size=17;
      function applySize(){reader.style.fontSize=size+'px';try{localStorage.setItem('ss_offline_reader_size',String(size));}catch(ignored){}}
      toolbar.append(h('span',{class:'muted'},t('text_size')),button('A−',function(){size=Math.max(15,size-1);applySize();},'btn-ghost'),button('A+',function(){size=Math.min(24,size+1);applySize();},'btn-ghost'));root.appendChild(toolbar);applySize();
      function inline(node,value){value.split(/(\*\*[^*]+\*\*)/g).forEach(function(part){node.appendChild(part.startsWith('**')&&part.endsWith('**')?h('strong',{},part.slice(2,-2)):document.createTextNode(part));});}
      var code=false,pre=null;text.split(/\r?\n/).forEach(function(line){if(/^```/.test(line)){code=!code;if(code){pre=h('pre',{});reader.appendChild(pre);}return;}if(code){pre.appendChild(document.createTextNode(line+'\n'));return;}if(!line.trim())return;var title=/^#{1,4}\s+(.+)/.exec(line),bullet=/^[-*•]\s+(.+)/.exec(line),node=h(title?'h2':'p',bullet?{class:'offline-reader-bullet'}:{});inline(node,title?title[1]:bullet?'• '+bullet[1]:line);reader.appendChild(node);});root.appendChild(reader);
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
  function enhanceChoice(select,key) {if(!window.SSChoiceList)return;var control=window.SSChoiceList.enhance(select,{label:t(key),key:key,allowEmpty:key==='difficulty'});SS.onLeave(control.destroy);return control;}
  function selection(selected, plainCount) {
    var sub = h('select',{'aria-label':t('subject')}), top = h('select',{'aria-label':t('topic')});
    sub.appendChild(h('option',{value:''},t('choose_subject')));
    subjects.forEach(function (s) { sub.appendChild(h('option',{value:s.id},name(s))); });
    function fill() {
      top.replaceChildren(h('option',{value:''},t('choose_topic')));
      var s = subjects.find(function (s) { return s.id === Number(sub.value); });
      (s ? s.topics : []).forEach(function (o) { if (o.question_count) top.appendChild(h('option',{value:o.id},name(o)+(plainCount?'':' ('+o.question_count+')'))); });
    }
    sub.addEventListener('change',fill);
    if(!selected){var first=topics.find(function(o){return o.question_count;});if(first)selected=first.id;}
    if (selected) { var o = topicBy(selected); if (o) sub.value = o.subject_id; } fill(); if (selected) top.value = selected;
    var node=h('div',{class:'offline-form'},h('label',{},plainCount?h('span',{},t('subject')):t('subject'),sub),h('label',{},plainCount?h('span',{},t('topic')):t('topic'),top));
    enhanceChoice(sub,'subject');enhanceChoice(top,'topic');
    return {sub:sub,top:top,node:node};
  }
  function questionText(q) { return q['text_'+SS.lang] || q.text_hi || q.text_en || ''; }
  function options(q) { return q['options_'+SS.lang] || q.options_hi || q.options_en || []; }
  function answerText(q, index) { return Number.isInteger(index) && options(q)[index] != null ? String.fromCharCode(65+index)+'. '+options(q)[index] : t('unanswered'); }
  function inlineStudyText(node,text) {
    var re=/\*\*([^*]+)\*\*/g,match,last=0;
    while((match=re.exec(text))){node.appendChild(document.createTextNode(text.slice(last,match.index)));node.appendChild(h('strong',{},match[1]));last=re.lastIndex;}
    node.appendChild(document.createTextNode(text.slice(last)));return node;
  }
  function solutionBlock(q) {
    var block=h('div',{class:'offline-solution'},h('h3',{},t('solution_title')));
    var text=String(q['solution_'+SS.lang] || q.solution_hi || q.solution_en || t('no_solution')),list=null;
    text.split(/\n/).forEach(function(line){
      line=line.trim();if(!line){list=null;return;}
      var bullet=/^[-*•]\s+(.+)$/.exec(line),ordered=/^\d+[.)]\s+(.+)$/.exec(line),title=/^#{1,4}\s+(.+)$/.exec(line),kind=bullet?'ul':ordered?'ol':null;
      if(kind){if(!list||list.tagName.toLowerCase()!==kind){list=h(kind,{});block.appendChild(list);}list.appendChild(inlineStudyText(h('li',{}),(bullet||ordered)[1]));}
      else {list=null;block.appendChild(inlineStudyText(h(title?'h4':'p',{class:'offline-question'}),title?title[1]:line));}
    });
    return block;
  }
  function answerFeedback(q, pick) {
    return h('div',{class:'offline-answer-feedback'},
      h('strong',{class:'offline-answer-status', 'data-status':pick===q.answer_index?'correct':'incorrect'},pick===q.answer_index?t('correct'):t('incorrect')),
      h('dl',{class:'offline-answer-pair'},h('div',{},h('dt',{},t('your_answer')),h('dd',{},answerText(q,pick))),h('div',{},h('dt',{},t('correct_answer')),h('dd',{},answerText(q,q.answer_index)))),solutionBlock(q));
  }
  function questionCard(q, reveal, onAnswer) {
    var box = h('section',{class:'offline-card'}), opts = options(q), picked = null;
    box.appendChild(h('p',{class:'xs muted','data-question-meta':''},'#'+q.id+(q.review_status === 'verified' ? ' · '+t('verified') : '')));
    box.appendChild(h('h2',{class:'offline-question'},questionText(q)));
    if (!q['text_'+SS.lang]) box.appendChild(h('p',{class:'xs muted'},t('language_fallback')));
    var choices = h('div',{class:'offline-options'}), feedback = h('div',{class:'offline-feedback','aria-live':'polite'});
    opts.forEach(function (text,index) {
      var choice = button(String.fromCharCode(65+index)+'. '+text,function () {
        if (picked != null && reveal) return; picked = index;
        choices.querySelectorAll('button').forEach(function (b,n) { b.setAttribute('aria-pressed',String(n===index)); });
        if (reveal) {
          choices.querySelectorAll('button').forEach(function (b,n) { b.disabled = true; if(n===q.answer_index) b.dataset.result='correct'; else if(n===index) b.dataset.result='wrong'; });
          feedback.replaceChildren(answerFeedback(q,index));
        }
        if (onAnswer) onAnswer(index);
      },'btn-secondary offline-option');choice.replaceChildren(h('span',{class:'offline-option-letter','aria-hidden':'true'},String.fromCharCode(65+index)),h('span',{},text));choice.setAttribute('aria-label',String.fromCharCode(65+index)+'. '+text); choice.setAttribute('aria-pressed','false'); choices.appendChild(choice);
    });
    box.appendChild(choices); box.appendChild(feedback);
    if (window.SSQuestionActions) box.appendChild(window.SSQuestionActions.render(q,{lang:SS.lang,topicId:q.topic_id}));
    if (window.SSWhiteboard) box.appendChild(window.SSWhiteboard.create(q.id,questionText(q)));
    return box;
  }
  function bank(selected) {
    heading(t('questions'),'home'); if(window.SSQuestionActions)root.appendChild(link(t('saved_questions'),'saved','btn btn-secondary')); var pick = selection(selected), difficulty = h('select',{'aria-label':t('difficulty')},h('option',{value:''},t('all_difficulties')));
    ['easy','medium','hard'].forEach(function (d) { difficulty.appendChild(h('option',{value:d},t(d))); });
    var search = h('input',{type:'search',maxlength:120,placeholder:t('search'),'aria-label':t('search')});
    root.appendChild(pick.node); root.appendChild(h('div',{class:'offline-form'},h('label',{},t('difficulty'),difficulty),h('label',{},t('search'),search)));enhanceChoice(difficulty,'difficulty');
    var results=h('div',{class:'offline-list'}), page=0, rows=[], token=generation; root.appendChild(results);
    function paint() {
      var term=search.value.trim().toLocaleLowerCase().replace(/^(?:ss-|#)(\d+)$/,'$1'), filtered=rows.filter(function (q) { return (!difficulty.value || q.difficulty===difficulty.value) && (!term || (questionText(q)+' '+q.id).toLocaleLowerCase().indexOf(term)>=0); });
      if(page*20>=filtered.length) page=0; results.replaceChildren(h('p',{class:'muted'},t('questions')+': '+filtered.length));
      filtered.slice(page*20,page*20+20).forEach(function (q) { results.appendChild(button('#'+q.id+' · '+questionText(q),function () { go('question/'+q.topic_id+'/'+q.id); },'btn-secondary offline-option')); });
      var prev=button(t('previous'),function(){page--;paint();}), next=button(t('next'),function(){page++;paint();}); prev.disabled=page===0; next.disabled=(page+1)*20>=filtered.length;
      results.appendChild(h('div',{class:'offline-row'},prev,h('span',{},String(page+1)),next));
    }
    var loadGeneration=0; function load() { var currentLoad=++loadGeneration; page=0; rows=[]; results.replaceChildren(h('p',{},t('loading'))); if(!pick.top.value){results.replaceChildren(h('p',{},t('choose_topic')));return;} loadTopic(pick.top.value).then(function(r){if(token===generation&&currentLoad===loadGeneration){rows=r;paint();}}).catch(showError); }
    pick.top.addEventListener('change',load); pick.sub.addEventListener('change',load); difficulty.addEventListener('change',function(){page=0;paint();}); search.addEventListener('input',function(){page=0;paint();}); load();
  }
  async function savedQuestions() {
    heading(t('saved_questions'),'questions');
    if(!window.SSQuestionActions){notice(t('saved_empty'));return;}
    var token=generation, records=await window.SSQuestionActions.list();if(token!==generation)return;
    if(!records.length){notice(t('saved_empty'));return;}
    var list=h('div',{class:'offline-list'}), page=0, loading=0;root.appendChild(list);
    async function paint() {
      var request=++loading;list.replaceChildren(h('p',{class:'muted'},t('loading')));
      var cards=[];
      // Resolve one page of saved IDs from their topics; never scan the library.
      for(var i=page*20;i<Math.min(records.length,(page+1)*20);i++) {
        var record=records[i], rows;
        try{rows=await loadTopic(record.topicId);}catch(e){continue;}
        if(token!==generation||request!==loading)return;
        var q=rows.find(function(item){return item.id===Number(record.id);});if(!q)continue;
        cards.push(h('section',{class:'offline-card offline-saved-card'},link(questionText(q),'question/'+q.topic_id+'/'+q.id,'offline-saved-question'),h('p',{class:'xs muted'},topicBy(q.topic_id)?name(topicBy(q.topic_id)):'#'+q.id),window.SSQuestionActions.render(q,{lang:SS.lang,topicId:q.topic_id})));
      }
      if(token!==generation||request!==loading)return;list.replaceChildren();
      cards.forEach(function(card){list.appendChild(card);});if(!cards.length)list.appendChild(h('p',{class:'muted'},t('saved_unavailable')));
      var prev=button(t('previous'),function(){page--;paint();}),next=button(t('next'),function(){page++;paint();});prev.disabled=page===0;next.disabled=(page+1)*20>=records.length;
      list.appendChild(h('div',{class:'offline-row'},prev,h('span',{},(page+1)+' / '+Math.ceil(records.length/20)),next));
    }
    await paint();
  }

  async function sharedQuestion(id) {
    heading(t('questions'),'questions');var token=generation;
    if(!/^[1-9][0-9]{0,14}$/.test(id||'')){notice(t('shared_invalid'));return;}
    function missing(){if(token!==generation)return;notice(t('shared_missing'));root.appendChild(h('p',{class:'offline-alert'},'SS-'+id));root.appendChild(link(t('questions'),'questions','btn btn-secondary'));}
    try{
      var index=await local('question-index.json');if(token!==generation)return;
      if(!object(index)||!Object.prototype.hasOwnProperty.call(index,id)||!Number.isSafeInteger(index[id])||!topicBy(index[id])){missing();return;}
      var rows=await loadTopic(index[id]);if(token!==generation)return;
      var q=rows.find(function(item){return String(item.id)===id;});if(!q){missing();return;}
      root.appendChild(questionCard(q,true,function(pick){record(q,pick);}));
    }catch(error){missing();}
  }
  function oneQuestion(topic,id) { heading(t('questions'),'questions/'+topic); var token=generation; return loadTopic(topic).then(function(rows){if(token!==generation)return;var q=rows.find(function(q){return q.id===Number(id);});if(!q)throw Error('question');root.appendChild(questionCard(q,true,function(index){record(q,index);}));}); }
  function record(q,index,defer) { state.answers[q.id]={topic:q.topic_id,pick:index,correct:index===q.answer_index,at:Date.now()}; if(!defer)save(); }
  function shuffle(rows) { var copy=rows.slice(); for(var i=copy.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),v=copy[i];copy[i]=copy[j];copy[j]=v;}return copy; }
  function practice(selected) {
    heading(t('practice'),'home');
    root.appendChild(h('p',{class:'practice-setup-intro'},t('practice_intro')));
    if(state.active){
      var activeTopic=topicBy(state.active.topicIds[0]),answered=Object.keys(state.active.picks||{}).length;
      root.appendChild(h('section',{class:'practice-resume'},h('div',{},h('strong',{},t('resume')),h('p',{},(activeTopic?name(activeTopic):t(state.active.mode))+' · '+answered+' / '+state.active.ids.length)),button(t('practice_resume_action'),resume,'btn-secondary')));
    }
    var pick=selection(selected,true),selectedCount=10,loadedRows=null,loading=false,starting=false,request=0;
    var available=h('p',{class:'practice-available',role:'status','aria-live':'polite'}),summary=h('p',{class:'practice-summary','aria-live':'polite'}),error=h('div',{class:'practice-load-error',role:'status'});
    var quantities=h('div',{class:'practice-counts',role:'group','aria-label':t('session_size')});
    [10,20,50].forEach(function(n){var choice=button(String(n),function(){selectedCount=n;paint();},'btn-secondary');choice.dataset.practiceCount=n;quantities.appendChild(choice);});
    var start=button(t('start'),async function(){
      if(starting||loading||!loadedRows||!loadedRows.length)return;
      starting=true;paint();
      try{await begin(shuffle(loadedRows).slice(0,selectedCount),'practice');}catch(e){error.replaceChildren(h('p',{},t('practice_load_error')));}finally{starting=false;paint();}
    },'btn-primary');start.dataset.practiceStart='';
    var all=link(t('practice_all'),'questions/'+(pick.top.value||''),'btn btn-ghost');
    pick.node.lastElementChild.insertBefore(available,pick.top);
    var card=h('section',{class:'practice-setup-card'},pick.node,h('div',{class:'practice-session-row'},h('div',{class:'practice-quantity'},h('h2',{},t('session_size')),quantities),h('div',{class:'practice-start-area'},summary,start)),error,h('nav',{class:'practice-secondary','aria-label':t('questions')},all,window.SSQuestionActions?link(t('saved_questions'),'saved','btn btn-ghost'):null));root.appendChild(card);
    function paint(){
      quantities.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(Number(b.dataset.practiceCount)===selectedCount));b.disabled=starting;});
      start.disabled=loading||starting||!loadedRows||!loadedRows.length;start.textContent=starting?t('loading'):t('start');
      var topic=topicBy(pick.top.value),count=loadedRows?loadedRows.length:topic?topic.question_count:0;
      available.textContent=loading?t('loading'):!topic?t('choose_topic'):t('practice_available')+': '+count;
      summary.textContent=t('practice_summary')+': '+Math.min(selectedCount,count);
      all.href='#questions/'+(pick.top.value||'');card.setAttribute('aria-busy',String(loading||starting));
    }
    async function load(){
      var current=++request,token=generation;loadedRows=null;error.replaceChildren();
      if(!pick.top.value){loading=false;paint();return;}
      loading=true;paint();
      try{var rows=await loadTopic(pick.top.value);if(token!==generation||current!==request)return;loadedRows=rows;if(!rows.length)error.appendChild(h('p',{},t('no_content')));}
      catch(e){if(token!==generation||current!==request)return;error.appendChild(h('p',{},t('practice_load_error')));var retry=button(t('practice_retry'),load,'btn-secondary');retry.dataset.practiceRetry='';error.appendChild(retry);}
      finally{if(token===generation&&current===request){loading=false;paint();}}
    }
    pick.top.addEventListener('change',load);pick.sub.addEventListener('change',load);load();
  }
  async function begin(rows,mode,minutes,rules) {
    if(!rows.length){SS.toast(t('no_content'));return;}
    if(state.active && !(await SSDialog.confirm({title:t('replace_title'),message:t('replace_session'),confirmLabel:t('replace_action')})))return;
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
    heading(session.mode==='mock'?t('mock'):t('practice'),'home'); var q=session.rows[session.index];var palette=h('nav',{class:'offline-palette','aria-label':t('questions')});session.rows.forEach(function(item,index){var b=button(String(index+1),function(){session.index=index;persistSession();route();},'btn-ghost');b.setAttribute('aria-label',t('question_number')+' '+(index+1));if(index===session.index)b.setAttribute('aria-current','step');if(Object.prototype.hasOwnProperty.call(session.picks,item.id))b.classList.add('is-answered');palette.appendChild(b);});root.appendChild(palette);
    var paletteGeneration=generation;requestAnimationFrame(function(){if(paletteGeneration!==generation||!palette.isConnected)return;var active=palette.querySelector('[aria-current=step]');if(!active)return;var box=palette.getBoundingClientRect(),item=active.getBoundingClientRect();palette.scrollLeft+=item.left-box.left-(palette.clientWidth-item.width)/2;});
    root.appendChild(h('p',{class:'offline-session-position'},t('question_number')+' '+(session.index+1)+' / '+session.rows.length));
    if(session.deadline){var timer=h('p',{role:'timer'});root.appendChild(timer);function tick(){var remain=Math.max(0,Math.ceil((session.deadline-Date.now())/1000));timer.textContent=t('time_left')+' '+Math.floor(remain/60)+':'+String(remain%60).padStart(2,'0');if(!remain)finishSession();}tick();if(!session)return;var interval=setInterval(tick,1000);SS.onLeave(function(){clearInterval(interval);});}
    root.appendChild(questionCard(q,session.mode!=='mock',function(index){session.picks[q.id]=index;if(session.mode!=='mock')record(q,index,true);persistSession();}));
    if(Object.prototype.hasOwnProperty.call(session.picks,q.id)){
      var choices=root.querySelectorAll('.offline-option');choices.forEach(function(b,n){b.setAttribute('aria-pressed',String(n===session.picks[q.id]));if(session.mode!=='mock'){b.disabled=true;if(n===q.answer_index)b.dataset.result='correct';else if(n===session.picks[q.id])b.dataset.result='wrong';}});
      if(session.mode!=='mock')root.querySelector('.offline-feedback').replaceChildren(answerFeedback(q,session.picks[q.id]));
    }
    var prev=button(t('previous'),function(){session.index--;persistSession();route();}),next=button(t('next'),function(){session.index++;persistSession();route();});prev.disabled=session.index===0;next.disabled=session.index===session.rows.length-1;
    root.appendChild(h('div',{class:'offline-session-actions'},prev,next,button(t('finish'),async function(){if(await SSDialog.confirm({title:t('finish_title'),message:t('finish_confirm'),confirmLabel:t('finish_action')}))finishSession();},'btn-primary')));
  }
  function finishSession(){if(!session||session.finished)return;session.finished=true;var correct=0,score=0,maxScore=0;session.rows.forEach(function(q){var r=(session.rules||{})[q.id]||{marks:1,negative:0};maxScore+=r.marks;if(Object.prototype.hasOwnProperty.call(session.picks,q.id))score+=session.picks[q.id]===q.answer_index?r.marks:-r.negative;});session.rows.forEach(function(q){if(Object.prototype.hasOwnProperty.call(session.picks,q.id)){record(q,session.picks[q.id],true);if(session.picks[q.id]===q.answer_index)correct++;}});var result={at:Date.now(),total:session.rows.length,correct:correct,topics:Array.from(new Set(session.rows.map(function(q){return q.topic_id;}))),mode:session.mode,score:score,maxScore:maxScore};state.history.unshift(result);state.active=null;save();lastResult={rows:session.rows,picks:session.picks,result:result};session=null;go('result');}
  function resultView() { if(lastResult){renderResult(lastResult.rows,lastResult.picks,lastResult.result);return;}heading(t('result'),'home');notice(t('result_expired'));root.appendChild(link(t('practice'),'practice','btn btn-primary')); }
  function renderResult(rows,picks,result) {
    root.replaceChildren();heading(t('result'),'home');
    var attempted=rows.filter(function(q){return Object.prototype.hasOwnProperty.call(picks,q.id);}).length;
    var metrics=h('dl',{class:'offline-result-metrics'});
    [[t('result_total'),rows.length],[t('correct'),result.correct],[t('incorrect'),attempted-result.correct],[t('unanswered'),rows.length-attempted]].forEach(function(item){metrics.appendChild(h('div',{},h('dt',{},item[0]),h('dd',{},item[1])));});
    root.appendChild(h('section',{class:'offline-card offline-result-summary','aria-label':t('result_summary')},h('p',{class:'offline-result-eyebrow'},t(result.mode)),h('h2',{},t('result_summary')),h('div',{class:'offline-result-score-row'},h('div',{},h('span',{class:'muted'},t('result_score')),h('p',{class:'offline-score'},Number(result.score.toFixed(2))+' / '+result.maxScore)),h('div',{class:'offline-result-accuracy'},h('strong',{},(attempted?Math.round(result.correct/attempted*100):0)+'%'),h('span',{},t('result_accuracy')))),metrics));
    root.appendChild(h('h2',{class:'offline-section-title'},t('result_review')));
    root.appendChild(h('p',{class:'muted offline-review-hint'},t('result_hint')));
    var list=h('div',{class:'offline-list offline-result-list'});root.appendChild(list);
    rows.forEach(function(q,index){
      var answered=Object.prototype.hasOwnProperty.call(picks,q.id),status=!answered?'unanswered':picks[q.id]===q.answer_index?'correct':'incorrect';
      var card=h('section',{class:'offline-card offline-review-card','data-status':status},h('div',{class:'offline-review-header'},h('span',{class:'offline-review-number'},t('question_number')+' '+(index+1)),h('span',{class:'offline-answer-status','data-status':status},t(status))),h('h3',{class:'offline-question'},questionText(q)));
      if(!q['text_'+SS.lang])card.appendChild(h('p',{class:'xs muted'},t('language_fallback')));
      card.appendChild(h('dl',{class:'offline-answer-pair'},h('div',{'data-answer':status},h('dt',{},t('your_answer')),h('dd',{},answerText(q,picks[q.id]))),h('div',{'data-answer':'correct'},h('dt',{},t('correct_answer')),h('dd',{},answerText(q,q.answer_index)))));
      card.appendChild(solutionBlock(q));if(window.SSQuestionActions)card.appendChild(window.SSQuestionActions.render(q,{lang:SS.lang,topicId:q.topic_id}));list.appendChild(card);
    });
  }
  function revision(){heading(t('revision'),'home');var wrong=Object.keys(state.answers).filter(function(id){return !state.answers[id].correct;});notice(t('revision_count')+' '+wrong.length);if(!wrong.length)return;root.appendChild(button(t('start'),function(){var ids=new Set(wrong.map(Number)),topicIds=Array.from(new Set(wrong.map(function(id){return state.answers[id].topic;}))),token=generation;Promise.all(topicIds.map(loadTopic)).then(function(groups){if(token===generation)begin(shuffle(groups.flat().filter(function(q){return ids.has(q.id);})).slice(0,50),'practice');}).catch(showError);},'btn-primary'));}
  function mocks(){
    heading(t('mock'),'home');
    root.appendChild(h('section',{class:'mock-screen-intro'},h('span',{class:'badge badge-brand'},t('mock_pattern')),h('h2',{},t('mock_choose')),h('p',{},t('mock_choose_hint'))));
    var grid=h('div',{class:'mock-card-grid'});root.appendChild(grid);
    (catalog.exams||[]).forEach(function(exam){
      var total=exam.sections.reduce(function(n,s){return n+s.questions;},0),marks=exam.sections.reduce(function(n,s){return n+s.questions*s.marks_per_q;},0);
      var card=h('article',{class:'mock-exam-card'}),titleId='mock-title-'+exam.id;
      card.setAttribute('aria-labelledby',titleId);
      card.appendChild(h('div',{class:'mock-exam-identity'},h('span',{class:'mock-exam-emblem','aria-hidden':'true'},exam.body),h('div',{},h('span',{class:'mock-exam-stage'},exam.stage_en),h('h2',{id:titleId},name(exam)))));
      var metrics=h('dl',{class:'mock-exam-metrics'});
      [[total,t('questions')],[exam.duration_min,t('minutes')],[Number(marks.toFixed(2)),t('mock_marks')]].forEach(function(pair){metrics.appendChild(h('div',{},h('dt',{},pair[1]),h('dd',{},pair[0])));});card.appendChild(metrics);
      var details=h('details',{class:'mock-exam-details'},h('summary',{},t('mock_sections'))),sectionList=h('ul',{});
      exam.sections.forEach(function(section){var subject=subjects.find(function(s){return s.id===section.subject_id;});sectionList.appendChild(h('li',{},h('strong',{},subject?name(subject):t('subject')),h('span',{},section.questions+' '+t('questions')+' · '+section.marks_per_q+' '+t('mock_marks')+' '+t('mock_each')),h('span',{class:'mock-exam-penalty'},section.negative_per_q?t('mock_negative')+': '+Number(section.negative_per_q.toFixed(3)):t('mock_no_negative'))));});
      details.appendChild(sectionList);var patternNote=exam['pattern_note_'+SS.lang]||exam.pattern_note_hi||exam.pattern_note_en;if(patternNote)details.appendChild(h('p',{class:'mock-exam-note'},patternNote));card.appendChild(details);
      var b=button(t('mock_start'),async function(){
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
      },'btn-primary mock-exam-start');b.setAttribute('aria-label',t('mock_start')+' · '+name(exam));card.appendChild(b);grid.appendChild(card);
    });
    notice(t('mock_note'));
  }
  function progress(){heading(t('progress'),'home');var answers=Object.keys(state.answers),right=answers.filter(function(id){return state.answers[id].correct;}).length;root.appendChild(h('div',{class:'offline-card'},h('p',{},t('read_chapters')+': '+state.reading.length),h('p',{},t('answered')+': '+answers.length),h('p',{},t('correct')+': '+right),h('p',{},t('sessions')+': '+state.history.length)));root.appendChild(h('div',{class:'offline-list offline-history'},state.history.map(function(s){return h('div',{class:'offline-card'},h('strong',{},new Date(s.at).toLocaleString(SS.lang==='hi'?'hi-IN':'en-IN')),h('p',{},t(s.mode)+' · '+(s.score==null?s.correct:Number(s.score.toFixed(2)))+' / '+(s.maxScore==null?s.total:s.maxScore)));})));}
  function resetOptions(){var select=h('select',{'aria-label':t('reset_scope')},h('option',{value:'all'},t('reset_all')));subjects.forEach(function(s){select.appendChild(h('option',{value:'subject:'+s.id},t('subject')+': '+name(s)));});books.forEach(function(b){b.chapters.forEach(function(c){select.appendChild(h('option',{value:'chapter:'+b.slug+'/'+c.slug},name(b)+' / '+name(c)));});});return select;}
  async function reset(scope){
    var picker=root.querySelector('select[aria-label]');var context=picker&&picker.selectedOptions[0]?picker.selectedOptions[0].textContent:'';if(!(await SSDialog.confirm({title:t('reset_title'),message:t('reset_confirm'),confirmLabel:t('reset_action'),danger:true,context:context})))return;
    lastResult=null;if(scope==='all'){state=emptyState();state.migratedReading=true;session=null;if(window.SSWhiteboard)window.SSWhiteboard.clearAll();}
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
  function exportBackup(){var data={format:'study-station-offline-backup',version:1,created_at:new Date().toISOString(),progress:state,whiteboards:window.SSWhiteboard?window.SSWhiteboard.export():{},favorites:window.SSQuestionActions?window.SSQuestionActions.exportSnapshot():[]};return JSON.stringify(data);}
  async function exportWithWorkspaces(){var data=JSON.parse(exportBackup());if(window.SSWorkspaceReady)await window.SSWorkspaceReady;if(window.SSWorkspaceStore)data.workspaces=await SSWorkspaceStore.exportAll();return JSON.stringify(data);}
  async function restoreBackup(raw){if(object(raw))raw=JSON.stringify(raw);if(typeof raw!=='string'||new TextEncoder().encode(raw).length>MAX_BACKUP)throw Error('invalid');var data=JSON.parse(raw);if(data.format!=='study-station-offline-backup'||data.version!==1)throw Error('invalid');var notebooks=window.SSWorkspaceStore?SSWorkspaceStore.validateAll(data.workspaces||[]):[],next=validateState(data.progress),boards=window.SSWhiteboard?window.SSWhiteboard.validate(data.whiteboards||{}):{},favorites=window.SSQuestionActions?window.SSQuestionActions.validate(data.favorites||[]):[];if(!(await SSDialog.confirm({title:t('restore_title'),message:t('restore_confirm'),confirmLabel:t('restore_action')})))return;var before=state;state=next;if(!save()){state=before;throw Error('storage');}try{await pendingSave;}catch(error){state=before;throw error;}if(window.SSQuestionActions)await window.SSQuestionActions.merge(favorites);if(window.SSWhiteboard)window.SSWhiteboard.merge(boards);if(window.SSWorkspaceStore)await SSWorkspaceStore.restoreAll(notebooks);session=null;lastResult=null;SS.toast(t('restored'));route();}

  async function importPrevious() {
    if(!(await SSDialog.confirm({title:t('import_title'),message:t('import_server_confirm'),confirmLabel:t('import_action')})))return;
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
  function settings(){heading(t('settings'),'home');notice(t('local_notice'));notice(t('server_progress'));root.appendChild(h('a',{href:'/progress',class:'btn btn-secondary'},t('view_server_progress')));root.appendChild(button(t('import_server'),importPrevious));var scope=resetOptions();root.appendChild(h('section',{class:'offline-card offline-stack'},h('h2',{},t('reset')),h('p',{},t('reset_note')),h('p',{class:'muted'},t('saved_reset_note')),scope,button(t('reset'),function(){reset(scope.value);},'btn-secondary')));
    enhanceChoice(scope,'reset_scope');
    var status=h('p',{role:'status'}),file=h('input',{type:'file',accept:'application/json,.json',hidden:true});file.addEventListener('change',function(){var f=file.files[0];file.value='';if(!f)return;if(f.size>MAX_BACKUP){status.textContent=t('invalid_backup');return;}f.text().then(restoreBackup).catch(function(){status.textContent=t('invalid_backup');});});
    root.appendChild(h('section',{class:'offline-card offline-stack'},h('h2',{},t('backup')),h('p',{},t('backup_note')),button(t('export'),async function(){try{if(window.SSQuestionActions)await window.SSQuestionActions.ready();}catch(e){status.textContent=t('backup_failed');return;}var raw;try{raw=await exportWithWorkspaces();}catch(e){status.textContent=t('backup_failed');return;}var bridge=window.StudyStationNative;if(new TextEncoder().encode(raw).length>MAX_BACKUP){status.textContent=t('invalid_backup');return;}if(bridge&&typeof bridge.requestLocalBackup==='function'){bridge.requestLocalBackup(raw);return;}var url=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=h('a',{href:url,download:'study-station-offline-'+new Date().toISOString().slice(0,10)+'.json'});document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},1000);}),button(t('import'),function(){var bridge=window.StudyStationNative;if(bridge&&typeof bridge.requestLocalRestore==='function')bridge.requestLocalRestore();else file.click();}),file,status));
  }
  function showError(){if(root)root.appendChild(h('p',{class:'offline-alert',role:'alert'},t('load_error')));}
  function route(){generation++;leaving.splice(0).forEach(function(fn){try{fn();}catch(e){}});root.replaceChildren();window.scrollTo(0,0);var parts=location.hash.slice(1).split('/'),page=parts[0]||'home';document.body.classList.toggle('practice-setup-screen',page==='practice');root.dataset.screen=page;document.querySelectorAll('.tabbar a').forEach(function(a){a.removeAttribute('aria-current');if(a.getAttribute('href')==='#'+page)a.setAttribute('aria-current','page');});try{var result=page==='workspace'?window.SSWorkspace.mount(root):page==='home'?home():page==='books'?bookList():page==='book'?chapters(parts[1]):page==='chapter'?chapter(parts[1],parts[2],parts[3]):page==='questions'?bank(parts[1]):page==='question'?oneQuestion(parts[1],parts[2]):page==='shared'?sharedQuestion(parts.length===2?parts[1]:''):page==='saved'?savedQuestions():page==='practice'?practice(parts[1]):page==='session'?sessionView():page==='revision'?revision():page==='mock'?mocks():page==='progress'?progress():page==='settings'?settings():page==='result'?resultView():home();if(result&&result.catch)result.catch(showError);}catch(e){showError();}}
  function init(){root=document.getElementById('offlineStudy');if(!root)return;if(window.SSQuestionActions)window.SSQuestionActions.ready().catch(function(){});document.cookie='ss_lang='+SS.lang+'; Path=/; SameSite=Lax';
    document.querySelector('.brand').setAttribute('href','#home');var settingsLink=document.querySelector('.top-actions a[href="/settings"]');if(settingsLink)settingsLink.href='#settings';
    var routes=['home','practice','mock','revision'];document.querySelectorAll('.tabbar a').forEach(function(a,index){if(index<4)a.setAttribute('href','#'+routes[index]);});
    var lang=document.getElementById('langBtn');if(lang)lang.addEventListener('click',function(){var next=SS.lang==='hi'?'en':'hi',url=new URL(location.href);url.searchParams.set('lang',next);location.href=url.pathname+url.search+url.hash;});
    document.querySelectorAll('[data-theme-set]').forEach(function(b){b.addEventListener('click',function(){window.SSTheme.set(b.dataset.themeSet);var picker=b.closest('details');if(picker)picker.removeAttribute('open');document.querySelectorAll('[data-theme-set]').forEach(function(o){o.setAttribute('aria-pressed',String(o===b));});});b.setAttribute('aria-pressed',String(window.SSTheme&&window.SSTheme.current()===b.dataset.themeSet));});
    window.addEventListener('hashchange',route);window.addEventListener('ss-drive-result',function(e){var r=e.detail;if(!r||!r.ok){if(r)SS.toast(t('backup_failed'));return;}if(r.operation==='local-restore'){restoreBackup(r.data).catch(function(){SS.toast(t('invalid_backup'));});}else if(r.operation==='local-backup')SS.toast(t('saved'));});
    Promise.all([local('catalog.json'),local('books/index.json'),local('manifest.json'),openProgress()]).then(function(data){catalog=data[0];books=data[1];manifest=data[2];subjects=catalog.subjects||[];save();topics=subjects.flatMap(function(s){return(s.topics||[]).map(function(o){return Object.assign({subject_id:s.id},o);});});route();}).catch(showError);
  }
  window.SSOffline={init:init,exportBackup:exportBackup,exportWithWorkspaces:exportWithWorkspaces,validateState:validateState};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
