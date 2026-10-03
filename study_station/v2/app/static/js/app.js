/* Study Station v2 — shared helpers and page wiring (no build step). */
(function () {
  'use strict';
  var SS = window.SS || (window.SS = {});

  SS.api = function (method, url, body) {
    if (method !== 'GET' && !body) body = {};   // API only accepts JSON bodies (CSRF guard)
    return fetch(url, {
      method: method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin'
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) { var e = new Error(data.detail || res.statusText); e.status = res.status; throw e; }
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

  SS.startPractice = function (topicId, difficulty, btn) {
    busy(btn, true);
    return SS.api('POST', '/api/v1/practice', { topic_id: Number(topicId), count: 10, difficulty: difficulty || null })
      .then(function (a) { location.href = '/attempt/' + a.id; })
      .catch(function (e) { busy(btn, false); SS.toast(e.message); });
  };

  SS.startMock = function (slug, btn) {
    busy(btn, true);
    return SS.api('POST', '/api/v1/mock', { exam: slug })
      .then(function (a) { location.href = '/attempt/' + a.id; })
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
          var msg = /daily_limit/.test(e.message) ? SS.t.ai_limit : /key_doubt/.test(e.message) ? SS.t.ai_key_doubt : SS.t.ai_unavailable;
          box.replaceChildren(h('p', { class: 'small muted' }, msg));
        });
    });
    box.appendChild(btn);
    return box;
  };

  // ---------------------------------------------------------------- report dialog
  SS.report = function (questionId) {
    var reasons = SS.lang === 'hi'
      ? [['wrong_answer', 'सही उत्तर गलत है'], ['wrong_solution', 'हल गलत है'], ['typo', 'टाइपिंग/छपाई की गलती'], ['translation', 'अनुवाद ठीक नहीं'], ['unclear', 'सवाल साफ़ नहीं'], ['other', 'कुछ और']]
      : [['wrong_answer', 'Answer key is wrong'], ['wrong_solution', 'Solution is wrong'], ['typo', 'Typo'], ['translation', 'Bad translation'], ['unclear', 'Question unclear'], ['other', 'Something else']];
    var h = SS.h;
    var note = h('textarea', { rows: 3, maxlength: 500, style: 'width:100%;margin-top:12px;padding:8px;border-radius:8px;border:1px solid var(--border);background:var(--surface)', 'aria-label': 'Note' });
    var dlg = h('dialog', { 'aria-label': SS.t.report },
      h('form', { method: 'dialog' },
        h('div', { class: 'dlg-body' }, h('h2', null, SS.t.report),
          h('div', { class: 'chips' }, reasons.map(function (r, i) {
            return h('label', { class: 'chip' }, h('input', { type: 'radio', name: 'reason', value: r[0], checked: i === 0 }), r[1]);
          })), note),
        h('div', { class: 'dlg-foot' },
          h('button', { class: 'btn btn-secondary btn-sm', value: 'cancel' }, '✕'),
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
    var b = e.target.closest('[data-practice]');
    if (b) { e.preventDefault(); SS.startPractice(b.getAttribute('data-practice'), null, b); return; }
    b = e.target.closest('[data-mock]');
    if (b) { e.preventDefault(); SS.startMock(b.getAttribute('data-mock'), b); return; }
    b = e.target.closest('[data-explain]');
    if (b) {
      e.preventDefault();
      var el = SS.explainButton(b.getAttribute('data-explain'));
      if (el) { b.replaceWith(el); el.querySelector('button').click(); }
      return;
    }
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
  });

  var langBtn = document.getElementById('langBtn');
  if (langBtn) langBtn.addEventListener('click', function () {
    var next = langBtn.getAttribute('data-next');
    SS.api('POST', '/api/v1/me', { lang: next }).then(function () { location.reload(); })
      .catch(function (e) { SS.toast(e.message); });
  });

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
      practiceForm.querySelector('[type=submit]'));
  });

  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  }
})();
