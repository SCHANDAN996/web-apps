/* A local-first, optional introduction. Never gates sign-in or study. */
(function () {
  'use strict';
  var key = 'ss_intro_seen_v1', index = 0, questionCount = null, returnFocus;
  function strings() { try { return JSON.parse(document.getElementById('ss-boot').textContent).t; } catch (_) { return {}; } }
  function seen() { try { return localStorage.getItem(key) === '1'; } catch (_) { return false; } }
  function remember() { try { localStorage.setItem(key, '1'); } catch (_) {} }
  function paint() {
    var dialog = document.getElementById('studyIntro'), t = strings();
    dialog.querySelectorAll('[data-intro-slide]').forEach(function (panel, n) { panel.hidden = n !== index; panel.querySelector('h2').id = n === index ? 'introHeading' : ''; });
    dialog.querySelectorAll('[data-intro-dot]').forEach(function (b, n) { b.setAttribute('aria-pressed', String(n === index)); });
    dialog.querySelector('[data-intro-prev]').disabled = index === 0;
    dialog.querySelector('[data-intro-next]').textContent = index === 2 ? t.intro_start : t.next;
    var count = dialog.querySelector('[data-intro-count]');
    count.hidden = !Number.isSafeInteger(questionCount) || questionCount < 1;
    if (!count.hidden) count.textContent = questionCount.toLocaleString(document.documentElement.lang === 'hi' ? 'hi-IN' : 'en-IN') + ' ' + t.intro_questions;
  }
  function close() { remember(); document.getElementById('studyIntro').close(); }
  function show() {
    var dialog = document.getElementById('studyIntro'); if (!dialog || dialog.open || !dialog.showModal) return;
    returnFocus = document.activeElement; index = 0; paint(); dialog.showModal(); dialog.querySelector('[data-intro-next]').focus();
  }
  function init() {
    var dialog = document.getElementById('studyIntro'); if (!dialog) return;
    if (!dialog.dataset.wired) {
      dialog.dataset.wired = '1';
      dialog.querySelector('[data-intro-lang]').addEventListener('click',function(){var button=document.getElementById('langBtn');if(button)button.click();});
      dialog.querySelector('[data-intro-close]').addEventListener('click', close);
      dialog.querySelector('[data-intro-next]').addEventListener('click', function () { if (index === 2) close(); else { index++; paint(); } });
      dialog.querySelector('[data-intro-prev]').addEventListener('click', function () { index = Math.max(0,index - 1); paint(); });
      dialog.querySelectorAll('[data-intro-dot]').forEach(function (b,n) { b.addEventListener('click',function () { index=n;paint(); }); });
      dialog.addEventListener('cancel',remember);
      dialog.addEventListener('close',function () { if (returnFocus && returnFocus.isConnected) returnFocus.focus(); });
      var slides=dialog.querySelector('.intro-slides'), start;
      slides.addEventListener('touchstart',function (e) { start=e.touches.length===1?{x:e.touches[0].clientX,y:e.touches[0].clientY}:null; },{passive:true});
      slides.addEventListener('touchend',function (e) { if(!start)return;var dx=e.changedTouches[0].clientX-start.x,dy=e.changedTouches[0].clientY-start.y;start=null;if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.5){index=Math.max(0,Math.min(2,index+(dx<0?1:-1)));paint();} },{passive:true});
      slides.addEventListener('keydown',function (e) { if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();index=Math.max(0,Math.min(2,index+(e.key==='ArrowRight'?1:-1)));paint();} });
    }
    if (document.querySelector('[data-intro-auto]') && !seen()) {
      show();
      fetch('/api/v1/intro-summary',{credentials:'same-origin'}).then(function(r){if(!r.ok)throw Error();return r.json();}).then(function(data){questionCount=data.questions;paint();}).catch(function(){});
    }
  }
  document.addEventListener('click',function(e){if(e.target.closest('[data-intro-open]'))show();});
  window.SSIntro={init:init,show:show,seen:seen,setCount:function(n){questionCount=n;if(document.getElementById('studyIntro'))paint();}};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
