/* Study Station v2 — shared helpers and page wiring (no build step). */
(function () {
  'use strict';
  var SS = window.SS || (window.SS = {});
  // Boot data comes as JSON (not an inline script) so the CSP can forbid inline JS.
  try {
    var boot = JSON.parse(document.getElementById('ss-boot').textContent);
    SS.lang = boot.lang; SS.t = boot.t; SS.ai = boot.ai;
  } catch (e) { SS.lang = SS.lang || 'hi'; SS.t = SS.t || {}; }

  SS.api = function (method, url, body) {
    if (method !== 'GET') clearWarm();
    if (method !== 'GET' && !body) body = {};   // API only accepts JSON bodies (CSRF guard)
    return fetch(url, {
      method: method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin'
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          var code = typeof data.detail === 'string' ? data.detail : '';
          var e = new Error((SS.t.errors && SS.t.errors[code]) || (SS.t.errors && SS.t.errors._default) || 'Error');
          e.status = res.status; e.code = code; throw e;
        }
        if (method !== 'GET') clearWarm();
        return data;
      });
    }, function () { var e = new Error(SS.t.offline); e.status = 0; throw e; });
  };

  SS.toast = function (msg) {
    var old = document.querySelector('.toast'); if (old) old.remove();
    var el = document.createElement('div');
    el.className = 'toast'; el.setAttribute('role', 'status'); el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 2600);
  };

  // Build DOM safely: h('div', {class: 'x'}, 'text', child) — strings become text nodes.
  SS.h = function (tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
      else if (k === 'html') throw new Error('no raw html');
      else el.setAttribute(k, v === true ? '' : v);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      (Array.isArray(c) ? c : [c]).forEach(function (x) {
        if (x === null || x === undefined || x === false) return;
        el.appendChild(typeof x === 'object' ? x : document.createTextNode(String(x)));
      });
    }
    return el;
  };

  SS.icon = function (name, cls) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg'); svg.setAttribute('class', 'icon ' + (cls || ''));
    svg.setAttribute('aria-hidden', 'true');
    var use = document.createElementNS(ns, 'use'); use.setAttribute('href', '#i-' + name);
    svg.appendChild(use); return svg;
  };

  // Pick the learner's language, fall back to the other one.
  SS.pick = function (obj) {
    if (!obj) return null;
    var other = SS.lang === 'hi' ? 'en' : 'hi';
    return obj[SS.lang] != null ? obj[SS.lang] : obj[other];
  };

  function busy(btn, on) { if (btn) { btn.disabled = on; btn.setAttribute('aria-busy', on ? 'true' : 'false'); } }

  SS.startPractice = function (topicId, difficulty, btn, count) {
    busy(btn, true);
    return SS.api('POST', '/api/v1/practice', { topic_id: Number(topicId), count: Number(count) || 10, difficulty: difficulty || null })
      .then(function (a) { SS.go('/attempt/' + a.id); })
      .catch(function (e) { busy(btn, false); SS.toast(e.message); });
  };

  SS.startMock = function (slug, btn) {
    busy(btn, true);
    return SS.api('POST', '/api/v1/mock', { exam: slug })
      .then(function (a) { SS.go('/attempt/' + a.id); })
      .catch(function (e) { busy(btn, false); SS.toast(e.message); });
  };

  // ---------------------------------------------------------------- AI tutor
  // Returns a button that, when tapped, replaces itself with the AI explanation.
  SS.explainButton = function (questionId, lang) {
    if (!SS.ai) return null;
    var h = SS.h;
    var box = h('div');
    var btn = h('button', { class: 'btn btn-secondary btn-sm', type: 'button', style: 'margin-top:8px' }, '✨ ' + SS.t.ai_explain);
    btn.addEventListener('click', function () {
      btn.disabled = true; btn.textContent = SS.t.ai_busy;
      SS.api('POST', '/api/v1/questions/' + questionId + '/explain', { lang: lang || SS.lang })
        .then(function (r) {
          box.replaceChildren(h('div', { class: 'solution', style: 'border-left-color:var(--accent)' },
            h('p', { class: 'xs muted', style: 'margin:0 0 6px' }, '✨ ' + SS.t.ai_note), r.text));
        })
        .catch(function (e) {
          var msg = e.code === 'daily_limit' ? SS.t.ai_limit : e.code === 'key_doubt' ? SS.t.ai_key_doubt : SS.t.ai_unavailable;
          box.replaceChildren(h('p', { class: 'small muted' }, msg));
        });
    });
    box.appendChild(btn);
    return box;
  };

  // ---------------------------------------------------------------- report dialog
  SS.report = function (questionId) {
    var reasons = SS.lang === 'hi'
      ? [['wrong_answer', 'सही उत्तर ग़लत है'], ['wrong_solution', 'हल ग़लत है'], ['typo', 'टाइपिंग/छपाई की ग़लती'], ['translation', 'अनुवाद ठीक नहीं'], ['unclear', 'सवाल साफ़ नहीं'], ['other', 'कुछ और']]
      : [['wrong_answer', 'Answer key is wrong'], ['wrong_solution', 'Solution is wrong'], ['typo', 'Typo'], ['translation', 'Bad translation'], ['unclear', 'Question unclear'], ['other', 'Something else']];
    var h = SS.h;
    var note = h('textarea', { id: 'reportNote', rows: 3, maxlength: 500, style: 'width:100%;padding:8px;border-radius:8px;border:1px solid var(--border);background:var(--surface-raised);color:var(--text)' });
    var noteLabel = h('label', { for: 'reportNote', class: 'small', style: 'display:block;margin-top:12px;margin-bottom:4px' }, SS.t.report_note || 'Note');
    var dlg = h('dialog', { 'aria-label': SS.t.report },
      h('form', { method: 'dialog' },
        h('div', { class: 'dlg-body' }, h('h2', null, SS.t.report),
          h('div', { class: 'chips' }, reasons.map(function (r, i) {
            return h('label', { class: 'chip' }, h('input', { type: 'radio', name: 'reason', value: r[0], checked: i === 0 }), r[1]);
          })), noteLabel, note),
        h('div', { class: 'dlg-foot' },
          h('button', { class: 'btn btn-secondary btn-sm', value: 'cancel' }, SS.t.cancel),
          h('button', { class: 'btn btn-primary btn-sm', value: 'send' }, SS.t.report))));
    document.body.appendChild(dlg);
    dlg.addEventListener('close', function () {
      if (dlg.returnValue === 'send') {
        var reason = dlg.querySelector('input[name=reason]:checked').value;
        SS.api('POST', '/api/v1/questions/' + questionId + '/report', { reason: reason, note: note.value })
          .then(function () { SS.toast('✓'); }).catch(function (e) { SS.toast(e.message); });
      }
      dlg.remove();
    });
    dlg.showModal();
  };

  // ---------------------------------------------------------------- page wiring
  document.addEventListener('click', function (e) {
    var questionPractice = e.target.closest('[data-question-practice]');
    if (questionPractice) {
      e.preventDefault(); busy(questionPractice, true);
      SS.api('POST', '/api/v1/questions/' + Number(questionPractice.getAttribute('data-question-practice')) + '/practice', {})
        .then(function (a) { SS.go('/attempt/' + a.id); })
        .catch(function (err) { busy(questionPractice, false); SS.toast(err.message); });
      return;
    }
    var b = e.target.closest('[data-practice]');
    if (b) { e.preventDefault(); SS.startPractice(b.getAttribute('data-practice'), null, b); return; }
    b = e.target.closest('[data-mock]');
    if (b) { e.preventDefault(); SS.startMock(b.getAttribute('data-mock'), b); return; }
    b = e.target.closest('[data-retry-wrong]');
    if (b) {
      e.preventDefault(); busy(b, true);
      SS.api('POST', '/api/v1/attempts/' + Number(b.getAttribute('data-retry-wrong')) + '/retry-wrong')
        .then(function (a) { SS.go('/attempt/' + a.id); })
        .catch(function (err) { busy(b, false); SS.toast(err.message); });
      return;
    }
    b = e.target.closest('[data-ca-quiz]');
    if (b) {
      e.preventDefault(); busy(b, true);
      var days = Number(b.getAttribute('data-ca-quiz'));
      SS.api('POST', '/api/v1/practice', { topic_id: Number(b.getAttribute('data-topic')), count: days > 7 ? 25 : 20, since_days: days })
        .then(function (a) { SS.go('/attempt/' + a.id); })
        .catch(function (err) { busy(b, false); SS.toast(err.message); });
      return;
    }
    b = e.target.closest('[data-explain]');
    if (b) {
      e.preventDefault();
      var el = SS.explainButton(b.getAttribute('data-explain'));
      if (el) { b.replaceWith(el); el.querySelector('button').click(); }
      return;
    }
    b = e.target.closest('[data-flip]');
    if (b) { b.setAttribute('aria-expanded', b.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'); return; }
    b = e.target.closest('[data-report]');
    if (b) { e.preventDefault(); SS.report(b.getAttribute('data-report')); return; }
    b = e.target.closest('#reviewFilter [data-f]');
    if (b) {
      var f = b.getAttribute('data-f');
      document.querySelectorAll('#reviewFilter [data-f]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      document.querySelectorAll('.review-item').forEach(function (it) {
        it.hidden = f !== 'all' && it.getAttribute('data-status') !== f;
      });
    }
    var to = !e.defaultPrevented && !e.button && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey && screenLink(e);
    if (to) { e.preventDefault(); SS.go(to); }
  });

  var langBtn = document.getElementById('langBtn');
  if (langBtn) langBtn.addEventListener('click', function () {
    var next = langBtn.getAttribute('data-next');
    SS.api('POST', '/api/v1/me', { lang: next }).then(function () {
      if (/^\/questions(?:\/|$)/.test(location.pathname)) {
        var url = new URL(location.href); url.searchParams.set('lang', next); location.assign(url.href);
      } else location.reload();
    })
      .catch(function (e) { SS.toast(e.message); });
  });

  // ---------------------------------------------------------------- per-screen wiring
  // Runs for the first screen and again after every screen change (see "in-app navigation" below).
  // Anything a screen hooks onto window/document goes through onPage so it is removed on the way out.
  var leave = [];
  SS.onLeave = function (fn) { leave.push(fn); };
  function onPage(target, type, fn, opts) {
    target.addEventListener(type, fn, opts);
    leave.push(function () { target.removeEventListener(type, fn, opts); });
  }

  function paintThemes() {
    var c = window.SSTheme.current();
    document.querySelectorAll('[data-theme-set]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-theme-set') === c));
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-theme-set]');
    var picker = document.getElementById('themePicker');
    if (b) {
      window.SSTheme.set(b.getAttribute('data-theme-set'));
      paintThemes();
      if (picker && picker.open) { picker.open = false; picker.querySelector('summary').focus(); }
    } else if (picker && !picker.contains(e.target)) picker.open = false;
  });
  document.addEventListener('keydown', function (e) {
    var picker = document.getElementById('themePicker');
    if (e.key === 'Escape' && picker && picker.open) { picker.open = false; picker.querySelector('summary').focus(); }
  });

  SS.initPage = function () {
  if (window.SSBackup) window.SSBackup.init();
  var onboard = document.getElementById('onboard');
  if (onboard) {
    onboard.addEventListener('submit', function (e) {
      e.preventDefault();
      var fd = new FormData(onboard);
      var btn = onboard.querySelector('[type=submit]');
      busy(btn, true);
      SS.api('POST', '/api/v1/me', { lang: fd.get('lang'), level: fd.get('level'), target_exams: fd.getAll('exams') })
        .then(function () { location.href = '/'; })
        .catch(function (err) { busy(btn, false); SS.toast(err.message); });
    });
    // Suggest exams that match the chosen qualification.
    onboard.addEventListener('change', function (e) {
      if (e.target.name !== 'level') return;
      var rank = { '10th': 1, '12th': 2, 'graduate': 3 }[e.target.value];
      onboard.querySelectorAll('[data-level]').forEach(function (chip) {
        var r = { '10th': 1, '12th': 2, 'graduate': 3 }[chip.getAttribute('data-level')];
        chip.hidden = r > rank;
        if (r > rank) chip.querySelector('input').checked = false;
      });
    });
    var lv = onboard.querySelector('input[name=level]:checked');
    if (lv) lv.dispatchEvent(new Event('change', { bubbles: true }));
  }

  var syncMake = document.getElementById('syncMake');
  if (syncMake) syncMake.addEventListener('click', function () {
    busy(syncMake, true);
    SS.api('POST', '/api/v1/sync/code').then(function (r) {
      var el = document.getElementById('syncCode');
      el.textContent = r.code; el.hidden = false;
      document.getElementById('syncWarn').hidden = false;
      busy(syncMake, false);
    }).catch(function (e) { busy(syncMake, false); SS.toast(e.message); });
  });
  var syncRestore = document.getElementById('syncRestore');
  if (syncRestore) syncRestore.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = syncRestore.querySelector('[type=submit]');
    busy(btn, true);
    SS.api('POST', '/api/v1/sync/restore', { code: new FormData(syncRestore).get('code') })
      .then(function () { location.href = '/'; })
      .catch(function (err) { busy(btn, false); SS.toast(err.status === 404 ? SS.t.sync_bad : err.message); });
  });

  var practiceForm = document.getElementById('practiceForm');
  if (practiceForm) practiceForm.addEventListener('submit', function (e) {
    e.preventDefault();
    SS.startPractice(practiceForm.getAttribute('data-topic'), new FormData(practiceForm).get('difficulty'),
      practiceForm.querySelector('[type=submit]'), new FormData(practiceForm).get('count'));
  });
  var questionFilters = document.getElementById('questionBankFilters');
  if (questionFilters) questionFilters.addEventListener('submit', function (e) {
    e.preventDefault(); SS.go('/questions?' + new URLSearchParams(new FormData(questionFilters)).toString());
  });
  var cacheCard = document.getElementById('contentCache');
  if (cacheCard) {
    var cacheStatus = document.getElementById('contentCacheStatus'), cacheClear = document.getElementById('contentCacheClear');
    function cacheMessage(type) {
      if (!('serviceWorker' in navigator) || !window.MessageChannel) return Promise.reject(new Error('unavailable'));
      return navigator.serviceWorker.getRegistration().then(function (registration) {
        var worker = navigator.serviceWorker.controller || (registration && registration.active);
        if (!worker) throw new Error('unavailable');
        return new Promise(function (resolve, reject) {
          var channel = new MessageChannel();
          var timer = setTimeout(function () { channel.port1.close(); reject(new Error('timeout')); }, 5000);
          channel.port1.onmessage = function (event) {
            clearTimeout(timer); channel.port1.close();
            if (event.data && event.data.ok) resolve(event.data); else reject(new Error('cache_failed'));
          };
          worker.postMessage({ type: type }, [channel.port2]);
        });
      });
    }
    function cacheRefresh() {
      cacheMessage('SS_CONTENT_CACHE_STATUS').then(function (data) {
        cacheStatus.textContent = SS.t.cache_status.replace('{books}', data.books).replace('{questions}', data.questions);
        cacheClear.disabled = false;
      }).catch(function () { cacheStatus.textContent = SS.t.cache_unavailable; cacheClear.disabled = true; });
    }
    cacheClear.addEventListener('click', function () {
      clearWarm();
      busy(cacheClear, true);
      cacheMessage('SS_CLEAR_CONTENT_CACHE').then(function () { cacheStatus.textContent = SS.t.cache_cleared; busy(cacheClear, false); })
        .catch(function () { cacheStatus.textContent = SS.t.cache_failed; busy(cacheClear, false); });
    });
    if ('serviceWorker' in navigator) onPage(navigator.serviceWorker, 'controllerchange', cacheRefresh);
    cacheRefresh();
  }

  // ---------------------------------------------------------------- practice: subject tabs + topic search
  var secs = document.querySelectorAll('.subject-sec');
  if (secs.length) {
    document.documentElement.classList.add('js');
    var tabs = document.querySelectorAll('[data-subject-tab]');
    var search = document.getElementById('topicSearch');
    var none = document.getElementById('searchEmpty');
    var current = (location.hash || '').slice(1);
    try { current = current || localStorage.getItem('ss_subject') || ''; } catch (e) {}
    if (!document.querySelector('[data-subject="' + current + '"]')) current = secs[0].getAttribute('data-subject');
    var show = function () {
      var q = (search && search.value || '').trim().toLowerCase();
      var anyHit = false;
      secs.forEach(function (sec) {
        var rows = sec.querySelectorAll('[data-topic-name]'), hits = 0;
        rows.forEach(function (li) { var ok = !q || li.getAttribute('data-topic-name').indexOf(q) !== -1; li.classList.toggle('is-hidden', !ok); if (ok) hits++; });
        var visible = q ? hits > 0 : sec.getAttribute('data-subject') === current;
        sec.classList.toggle('is-hidden', !visible);
        if (visible && hits) anyHit = true;
      });
      tabs.forEach(function (t) { t.setAttribute('aria-current', String(!q && t.getAttribute('data-subject-tab') === current)); });
      if (none) none.hidden = !q || anyHit;
    };
    tabs.forEach(function (t) {
      t.addEventListener('click', function (e) {
        e.preventDefault();
        current = t.getAttribute('data-subject-tab');
        try { localStorage.setItem('ss_subject', current); } catch (err) {}
        if (search) search.value = '';
        show();
        history.replaceState(null, '', '#' + current);
      });
    });
    if (search) search.addEventListener('input', show);
    show();
  }

  // ---------------------------------------------------------------- continue reading
  // The chapter page remembers itself; the home plan turns "Read a chapter" into "Continue: <chapter>".
  var lastKey = 'ss_last_chapter';
  var chapterMeta = document.querySelector('[data-chapter-url]');
  var readKey = 'ss_read_chapters';
  var readList = function () { try { return JSON.parse(localStorage.getItem(readKey) || '[]'); } catch (e) { return []; } };
  if (chapterMeta) {
    var curUrl = chapterMeta.getAttribute('data-chapter-url');
    try { localStorage.setItem(lastKey, JSON.stringify({ url: curUrl, hi: chapterMeta.getAttribute('data-title-hi'), en: chapterMeta.getAttribute('data-title-en') })); } catch (e) {}
    // A chapter counts as read once the reader reaches its end.
    var markRead = function () {
      if (innerHeight + scrollY < document.documentElement.scrollHeight - 200) return;
      var list = readList();
      if (list.indexOf(curUrl) === -1) { list.push(curUrl); try { localStorage.setItem(readKey, JSON.stringify(list.slice(-500))); } catch (e) {} }
      window.removeEventListener('scroll', markRead);
    };
    onPage(window, 'scroll', markRead, { passive: true });
    setTimeout(markRead, 0);                       // short chapters never scroll
  }
  var readNow = readList();
  document.querySelectorAll('[data-chapter-link]').forEach(function (a) {
    if (readNow.indexOf(a.getAttribute('data-chapter-link')) !== -1) {
      a.classList.add('is-read');
      var m = a.querySelector('.read-mark'); if (m) m.hidden = false;
    }
  });
  var planRead = document.getElementById('planRead');
  if (planRead) {
    try {
      var last = JSON.parse(localStorage.getItem(lastKey) || 'null');
      if (last && /^\/books\//.test(last.url)) {
        planRead.setAttribute('href', last.url);
        var b = planRead.querySelector('[data-continue-label]');
        b.textContent = b.getAttribute('data-continue-label') + ': ' + (last[SS.lang] || last.hi || last.en || last.title || '');
      }
    } catch (e) {}
  }

  // ---------------------------------------------------------------- book reader settings
  var reader = document.getElementById('reader');
  if (reader) {
    var store = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
    var applyTheme = function (t) {
      reader.classList.toggle('reader-paper', t === 'paper');
      reader.classList.toggle('reader-night', t === 'night');
      document.querySelectorAll('[data-reader-theme]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-reader-theme') === t)); });
    };
    var scale = Number(store('ss_reader_scale')) || 1;
    var applySize = function () { reader.style.setProperty('--reader-scale', String(scale)); };
    applyTheme(store('ss_reader_theme') || 'plain');
    applySize();
    onPage(document, 'click', function (e) {
      var t = e.target.closest('[data-reader-theme]');
      if (t) { var v = t.getAttribute('data-reader-theme'); store('ss_reader_theme', v); applyTheme(v); return; }
      var z = e.target.closest('[data-reader-size]');
      if (z) {
        scale = Math.min(1.5, Math.max(0.85, Math.round((scale + 0.1 * Number(z.getAttribute('data-reader-size'))) * 100) / 100));
        store('ss_reader_scale', String(scale)); applySize();
      }
    });
  }

  // Reading progress bar on chapter pages (transform only, one update per frame).
  var readBar = document.getElementById('readBar');
  if (readBar) {
    var ticking = false;
    var upd = function () {
      var max = document.documentElement.scrollHeight - innerHeight;
      readBar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, scrollY / max) : 1) + ')';
      ticking = false;
    };
    onPage(window, 'scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(upd); } }, { passive: true });
    upd();
  }

  paintThemes();
  if (window.SSReset) window.SSReset.init();
  var jobFilters = document.getElementById('jobFilters');
  if (jobFilters) jobFilters.addEventListener('submit', function (e) {
    e.preventDefault();
    SS.go('/jobs?' + new URLSearchParams(new FormData(jobFilters)).toString());
  });
  var jobSearch = document.getElementById('jobSearch');
  if (jobSearch) {
    var jobCards = document.querySelectorAll('[data-job-search]');
    var filterJobs = function () {
      var q = jobSearch.value.trim().toLocaleLowerCase();
      var visible = 0;
      jobCards.forEach(function (card) {
        card.hidden = card.getAttribute('data-job-search').toLocaleLowerCase().indexOf(q) === -1;
        if (!card.hidden) visible++;
      });
      document.getElementById('jobSearchEmpty').hidden = visible > 0;
      document.getElementById('jobShown').textContent = String(visible);
      document.getElementById('jobSearchClear').hidden = !q;
    };
    jobSearch.addEventListener('input', filterJobs);
    document.getElementById('jobSearchClear').addEventListener('click', function () {
      jobSearch.value = ''; filterJobs(); jobSearch.focus();
    });
    filterJobs();
  }
  };

  // Install prompt (Android Chrome): show our own card instead of the browser mini-bar.
  var installCard = document.getElementById('installCard'), deferredInstall = null;
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredInstall = e;
    try { if (localStorage.getItem('ss_install_dismissed')) return; } catch (err) {}
    if (installCard) installCard.hidden = false;
  });
  var installBtn = document.getElementById('installBtn');
  if (installBtn) installBtn.addEventListener('click', function () {
    if (!deferredInstall) return;
    deferredInstall.prompt();
    deferredInstall.userChoice.then(function (c) {
      if (c.outcome !== 'accepted') { try { localStorage.setItem('ss_install_dismissed', '1'); } catch (err) {} }
      installCard.hidden = true; deferredInstall = null;
    });
  });
  window.addEventListener('appinstalled', function () { if (installCard) installCard.hidden = true; });

  // Connection state as a snackbar.
  window.addEventListener('offline', function () { SS.toast(SS.t.offline_now || 'Offline'); });
  window.addEventListener('online', function () { SS.toast(SS.t.online_again || 'Online'); });

  // ---------------------------------------------------------------- Material 3 feel
  // Ripple on press (transform/opacity only; skipped when the user prefers reduced motion).
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduceMotion) document.addEventListener('pointerdown', function (e) {
    var el = e.target.closest('.btn, .chip, .card-link, .option, .tab, .list-item, .seg-btn');
    if (!el || el.disabled || el.getAttribute('aria-disabled') === 'true') return;
    var r = el.getBoundingClientRect(), size = Math.max(r.width, r.height) * 2.2;
    var dot = document.createElement('span');
    dot.className = 'ripple';
    dot.style.width = dot.style.height = size + 'px';
    dot.style.left = (e.clientX - r.left - size / 2) + 'px';
    dot.style.top = (e.clientY - r.top - size / 2) + 'px';
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(dot);
    dot.addEventListener('animationend', function () { dot.remove(); });
  }, { passive: true });
  // Top app bar takes the container tint once the page scrolls (M3 "on scroll" state).
  var onScroll = function () { document.body.classList.toggle('scrolled', window.scrollY > 4); };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---------------------------------------------------------------- in-app navigation
  // The frame (top bar, tab bar, CSS, JS) stays put; a screen change fetches the page and swaps only
  // <main>. Inside the Android app the frame itself is read from the APK (templates/shell.html →
  // android/…/assets/shell), so the structure is on screen before the network answers.
  var SCREEN = /^\/(?:(?:settings|practice|mock|attempt|result|revise|progress|current-affairs|jobs|books|questions)(?:\/|$)|$)/;
  var navSeq = 0, warm = {}, here = location.pathname + location.search;
  var WARM_TTL = 5000, WARM_LIMIT = 6;

  function dropWarm(url, abort) {
    var entry = warm[url];
    delete warm[url];
    if (abort && entry && entry.ctl) entry.ctl.abort();
  }

  function clearWarm() {
    Object.keys(warm || {}).forEach(function (url) { dropWarm(url, true); });
  }

  function pruneWarm() {
    var now = Date.now();
    Object.keys(warm).forEach(function (url) {
      if (now - warm[url].at >= WARM_TTL) dropWarm(url, true);
    });
  }

  function screenLink(e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download')) return null;
    var u;
    try { u = new URL(a.getAttribute('href'), location.href); } catch (err) { return null; }
    if (u.origin !== location.origin || !SCREEN.test(u.pathname)) return null;
    if (u.pathname + u.search === here && u.hash) return null;          // a jump inside this screen
    return u.href;
  }

  function assetV(doc) {
    var l = doc.querySelector('link[rel="stylesheet"][href*="/static/css/app.css"]');
    var m = l && /[?&]v=([0-9a-f]+)/.exec(l.getAttribute('href'));
    return m ? m[1] : '';
  }

  function markTab(path) {
    document.querySelectorAll('.tabbar .tab').forEach(function (a) {
      var href = a.getAttribute('href');
      if (href === '/' ? path === '/' : path.indexOf(href) === 0) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }

  function fetchPage(url, ctl) {
    ctl = ctl || (window.AbortController ? new AbortController() : null);
    var timer = ctl && setTimeout(function () { ctl.abort(); }, 15000);     // a stalled connection counts as offline
    return fetch(url, { credentials: 'same-origin', headers: { 'X-SS-Nav': '1' }, signal: ctl ? ctl.signal : undefined }).then(function (res) {
      return res.text().then(function (html) { return { url: res.url || url, html: html }; });
    }).then(function (page) { clearTimeout(timer); return page; }, function (error) { clearTimeout(timer); throw error; });
  }

  function setCookie(name, value) {
    document.cookie = name + '=' + value + '; path=/; max-age=86400; samesite=lax' + (location.protocol === 'https:' ? '; secure' : '');
  }

  // The fetched page does not fit this frame (the server has newer CSS/JS, or another language): load it
  // whole. The cookies tell the Android app which frame to use next; the guard stops a reload loop.
  function loadWhole(url, doc) {
    var lang = doc.documentElement.getAttribute('lang');
    try {
      if (sessionStorage.getItem('ss_whole') === url) return false;
      sessionStorage.setItem('ss_whole', url);
    } catch (e) { return false; }
    if (lang === 'hi' || lang === 'en') setCookie('ss_lang', lang);
    if (assetV(doc) !== assetV(document)) setCookie('ss_shell_off', assetV(document));
    location.replace(url);
    return true;
  }

  function show(p, mode) {                       // mode: push | replace | pop
    var doc = new DOMParser().parseFromString(p.html, 'text/html');
    var fresh = doc.getElementById('main');
    var fits = fresh && assetV(doc) === assetV(document) &&
      doc.documentElement.getAttribute('lang') === document.documentElement.getAttribute('lang');
    if (!fits && loadWhole(p.url, doc)) return;
    if (!fresh) { location.replace(p.url); return; }
    try { sessionStorage.removeItem('ss_whole'); } catch (e) {}
    leave.splice(0).forEach(function (fn) { try { fn(); } catch (e) {} });
    document.querySelectorAll('dialog, .toast').forEach(function (el) { el.remove(); });
    if (mode === 'push') history.pushState({ ss: 1 }, '', p.url);
    else if (mode === 'replace') history.replaceState({ ss: 1 }, '', p.url);
    here = location.pathname + location.search;
    clearWarm();
    try { SS.ai = JSON.parse(doc.getElementById('ss-boot').textContent).ai; } catch (e) {}
    document.title = doc.title;
    document.body.className = doc.body.className;
    var main = document.getElementById('main');
    main.className = fresh.className;
    main.replaceChildren.apply(main, [].map.call(fresh.childNodes, function (n) { return document.importNode(n, true); }));
    markTab(location.pathname);
    scrollTo(0, mode === 'pop' && history.state && history.state.y || 0);
    onScroll();
    // Scripts this screen needs and the frame does not have yet (the question player).
    var had = !!SS.startPlayer;
    var need = [].map.call(doc.querySelectorAll('script[src]'), function (s) { return s.getAttribute('src'); })
      .filter(function (src) { return !document.querySelector('script[src="' + src + '"]'); });
    (function next() {
      var src = need.shift();
      if (src) {
        var el = document.createElement('script');
        el.src = src; el.onload = el.onerror = next;
        document.body.appendChild(el);
        return;
      }
      SS.initPage();
      if (had) SS.startPlayer();                  // a freshly loaded player.js starts itself
    })();
  }

  function waiting() { return document.getElementById('shellWait'); }

  function go(url, mode) {
    var seq = ++navSeq;
    if (mode === 'push') { try { history.replaceState({ ss: 1, y: scrollY }, ''); } catch (e) {} }
    markTab(new URL(url).pathname);
    document.body.classList.add('nav-busy');
    pruneWarm();
    var w = warm[url];
    dropWarm(url, false);                    // navigation owns this request now
    clearWarm();                            // other screens belong to the page being left
    return (w ? w.p : fetchPage(url)).then(function (p) {
      if (seq === navSeq) show(p, mode);
    }, function () {
      if (seq !== navSeq) return;
      document.body.classList.remove('nav-busy');
      markTab(location.pathname);
      if (!waiting()) { SS.toast(SS.t.offline); return; }
      // The frame came from the APK and the first screen could not be fetched: say so, offer a retry.
      document.getElementById('main').replaceChildren(SS.h('div', { class: 'empty', id: 'shellWait' },
        SS.icon('wifi-off', 'empty-icon'), SS.h('p', null, SS.t.offline),
        SS.h('button', { class: 'btn btn-primary', type: 'button', onclick: function () { go(url, 'replace'); } }, SS.t.retry)));
    });
  }
  SS.go = function (url, replace) { return go(new URL(url, location.href).href, replace ? 'replace' : 'push'); };

  window.addEventListener('popstate', function () {
    if (location.pathname + location.search !== here) go(location.href, 'pop');
  });
  window.addEventListener('pagehide', clearWarm);
  document.addEventListener('visibilitychange', function () { if (document.hidden) clearWarm(); });
  // Start fetching on touch-down: by the time the tap is complete the screen is usually there.
  document.addEventListener('pointerdown', function (e) {
    var to = screenLink(e);
    pruneWarm();
    if (!to || warm[to]) return;
    var urls = Object.keys(warm);
    if (urls.length >= WARM_LIMIT) {
      urls.sort(function (a, b) { return warm[a].at - warm[b].at; });
      dropWarm(urls[0], true);
    }
    var entry = { at: Date.now(), ctl: window.AbortController ? new AbortController() : null };
    entry.p = fetchPage(to, entry.ctl).catch(function (error) {
      if (warm[to] === entry) dropWarm(to, false);
      throw error;
    });
    entry.p.catch(function () {});
    warm[to] = entry;
  }, { passive: true });

  if (waiting()) go(location.href, 'replace'); else SS.initPage();

  if ('serviceWorker' in navigator && (location.protocol === 'https:' || ['localhost', '127.0.0.1', '[::1]'].indexOf(location.hostname) !== -1)) {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  }
})();
