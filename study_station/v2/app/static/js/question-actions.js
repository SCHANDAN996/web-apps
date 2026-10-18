(function () {
  'use strict';
  var dbPromise, snapshot = [];
  function t(key) {
    var strings = window.SS && window.SS.t;
    if (!strings) { try { strings = JSON.parse(document.getElementById('ss-boot').textContent).t; } catch (_) {} }
    return strings && strings[key] || key;
  }
  function notice(key) { if (window.SS && SS.toast) SS.toast(t(key)); }
  function database() {
    if (!dbPromise) dbPromise = new Promise(function (resolve, reject) {
      var request = indexedDB.open('ss-question-favorites', 1);
      request.onupgradeneeded = function () { request.result.createObjectStore('questions', {keyPath:'id'}); };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { dbPromise = null; reject(request.error); };
    });
    return dbPromise;
  }
  function idOf(question) {
    var id = String(question && typeof question === 'object' ? question.id : question);
    if (!/^[1-9][0-9]{0,14}$/.test(id)) throw Error('Invalid question ID');
    return id;
  }
  async function read(id) {
    var db = await database();
    return new Promise(function (resolve, reject) {
      var request = db.transaction('questions').objectStore('questions').get(id);
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }
  async function list() {
    var db = await database();
    return new Promise(function (resolve, reject) {
      var request = db.transaction('questions').objectStore('questions').getAll();
      request.onsuccess = function () { snapshot = request.result.sort(function (a,b) { return b.savedAt-a.savedAt; }); resolve(snapshot.map(function (record) { return Object.assign({},record); })); };
      request.onerror = function () { reject(request.error); };
    });
  }
  function validateRecords(records) {
    if (!Array.isArray(records) || records.length > 5000) throw Error('Invalid favorites backup');
    var seen = new Map(), fields = ['id','lang','savedAt','topicId','version'];
    records.forEach(function (record) {
      if (!record || typeof record !== 'object' || Array.isArray(record) || Object.keys(record).some(function (key) { return fields.indexOf(key) < 0; }) || Object.keys(record).length !== fields.length) throw Error('Invalid favorite record');
      var id = idOf(record);
      if (record.version !== 1 || (record.lang !== 'hi' && record.lang !== 'en') || typeof record.topicId !== 'string' || !/^[a-zA-Z0-9_\/-]{1,160}$/.test(record.topicId) || !Number.isSafeInteger(record.savedAt) || record.savedAt < 0 || record.savedAt > Date.now()+86400000) throw Error('Invalid favorite record');
      var clean = {version:1,id:id,topicId:record.topicId,lang:record.lang,savedAt:record.savedAt};
      if (!seen.has(id) || seen.get(id).savedAt < clean.savedAt) seen.set(id,clean);
    });
    return Array.from(seen.values());
  }
  async function restoreRecords(records) {
    var clean = validateRecords(records), db = await database();
    await new Promise(function (resolve,reject) {
      var transaction = db.transaction('questions','readwrite'), store = transaction.objectStore('questions');
      var keys = store.getAllKeys();
      keys.onsuccess = function () {
        var combined = new Set(keys.result);
        clean.forEach(function (record) { combined.add(record.id); });
        if (combined.size > 5000) { transaction.abort(); return; }
        clean.forEach(function (record) {
          var request = store.get(record.id);
          request.onsuccess = function () { if (!request.result || request.result.savedAt < record.savedAt) store.put(record); };
        });
      };
      transaction.oncomplete = resolve;
      transaction.onerror = transaction.onabort = function () { reject(transaction.error || Error('Storage unavailable')); };
    });
    var recordsAfter = await list();
    window.dispatchEvent(new CustomEvent('ss-question-favorites-changed',{detail:{restored:true}}));
    return recordsAfter;
  }
  async function toggle(question, options) {
    options = options || {};
    var id = idOf(question), db = await database();
    var record = validateRecords([{version:1,id:id,topicId:String(options.topicId || question.topic_id || ''),lang:options.lang === 'en' ? 'en' : 'hi',savedAt:Date.now()}])[0];
    return new Promise(function (resolve, reject) {
      var transaction = db.transaction('questions','readwrite'), store = transaction.objectStore('questions');
      var request = store.get(id), saved;
      request.onsuccess = function () {
        saved = !request.result;
        if (!saved) store.delete(id);
        else {
          var count = store.count();
          count.onsuccess = function () { if (count.result >= 5000) transaction.abort(); else store.put(record); };
        }
      };
      transaction.oncomplete = function () {
        list().then(function () {
          window.dispatchEvent(new CustomEvent('ss-question-favorites-changed',{detail:{id:id,saved:saved}}));
          resolve(saved);
        },reject);
      };
      transaction.onerror = transaction.onabort = function () { reject(transaction.error || Error('Storage unavailable')); };
    });
  }
  function payload(question, options) {
    options = options || {};
    var id = idOf(question), lang = options.lang === 'en' ? 'en' : 'hi';
    var text = String(question['text_'+lang] || question.text_hi || question.text_en || '');
    var choices = question['options_'+lang] || question.options_hi || question.options_en || [];
    if (!Array.isArray(choices)) choices = [];
    var url = 'https://studystation.ebookcart.in/q/'+encodeURIComponent(id)+'?lang='+lang;
    return {title:'Study Station · #'+id,text:[text].concat(choices.map(function (choice,index) { return String.fromCharCode(65+index)+'. '+String(choice); })).concat([t('question_install_answer')]).join('\n'),url:url};
  }
  async function share(question, options) {
    var data = payload(question,options);
    try {
      if (window.SSNativeShare && typeof SSNativeShare.shareQuestion === 'function') {
        var language = options && options.lang === 'en' ? 'en' : 'hi';
        var contentLanguage = question['text_'+language] ? language : question.text_hi ? 'hi' : 'en';
        var result = await SSNativeShare.shareQuestion({id:Number(idOf(question)),lang:language,
          question:String(question['text_'+contentLanguage] || ''),
          options:question['options_'+contentLanguage] || []});
        if (result && result.ok) return true;
        notice('question_share_failed'); return false;
      }
      if (navigator.share) { await navigator.share(data); return true; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(data.text+'\n\n'+data.url);
        notice('question_share_copied'); return true;
      }
      notice('question_share_failed'); return false;
    } catch (error) {
      if (error.name !== 'AbortError') notice('question_share_failed');
      return false;
    }
  }
  function render(question, options) {
    var id = idOf(question), row = document.createElement('div'); row.className = 'question-actions';
    var save = document.createElement('button'), send = document.createElement('button');
    save.type = send.type = 'button'; save.className = send.className = 'btn btn-ghost question-action';
    save.dataset.favoriteQuestion = id; send.dataset.shareQuestion = id;
    function paint(saved) { save.setAttribute('aria-pressed',String(saved)); save.textContent = (saved ? '★ ' : '☆ ')+t(saved ? 'question_saved' : 'question_save'); }
    paint(false); send.textContent = '↗ '+t('question_share');
    read(id).then(function (record) { paint(!!record); }).catch(function () {});
    save.addEventListener('click',async function () {
      save.disabled = true;
      try { var saved = await toggle(question,options); paint(saved); notice(saved ? 'question_saved_notice' : 'question_removed_notice'); }
      catch (_) { notice('question_storage_failed'); }
      finally { save.disabled = false; }
    });
    send.addEventListener('click',function () { share(question,options); });
    row.append(save,send); return row;
  }
  window.SSQuestionActions = {render:render,list:list,exportRecords:list,restoreRecords:restoreRecords,merge:restoreRecords,validate:validateRecords,ready:list,exportSnapshot:function () { return snapshot.map(function (record) { return Object.assign({},record); }); },isSaved:async function (id) { return !!(await read(idOf(id))); },toggle:toggle,share:share,payload:payload};
})();
