/* Study Station v2 — question player: practice, CBT mock, revision. */
(function () {
  'use strict';
  var SS = window.SS, h = SS.h, t = SS.t;
  var root = document.getElementById('player');
  if (!root) return;
  var mode = root.getAttribute('data-mode');
  var attemptId = root.getAttribute('data-attempt');
  var KEYS = 'ABCD';

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function fail(e) { clear(root); root.appendChild(h('div', { class: 'empty' }, e.message || String(e))); }

  // Per-question language: learner's language, but either can be shown when both exist.
  var qLang = {};
  var lastShown = null;   // question id last rendered — only animate on change
  function langOf(q) {
    var want = qLang[q.id] || SS.lang;
    return q.text[want] != null ? want : (want === 'hi' ? 'en' : 'hi');
  }

  function questionView(q, opts) {
    var lang = langOf(q);
    var both = q.text.hi != null && q.text.en != null;
    var meta = h('div', { class: 'q-meta' },
      h('b', null, 'Q' + q.n),
      h('span', { class: 'xs muted' }, SS.pick(q.topic)),
      q.difficulty ? h('span', { class: 'badge' }, t[q.difficulty] || q.difficulty) : null,
      h('span', { class: 'badge ' + (q.verified ? 'badge-ok' : '') }, q.verified ? t.verified_label : t.ai_label),
      both ? h('button', {
        class: 'chip', style: 'margin-left:auto', 'aria-label': 'Switch question language',
        onclick: function () { qLang[q.id] = lang === 'hi' ? 'en' : 'hi'; opts.rerender(); }
      }, SS.icon('globe', 'icon-sm'), lang === 'hi' ? 'English' : 'हिंदी') : null);

    var list = h('div', { class: 'options', role: 'group', 'aria-label': 'Options' });
    q.options[lang].forEach(function (text, i) {
      var cls = 'option';
      var tag = null;
      if (opts.revealed) {
        if (i === opts.revealed.answer_index) { cls += ' is-correct'; tag = t.right_answer; }
        else if (i === opts.chosen) { cls += ' is-wrong'; tag = t.your_answer; }
        if (opts.justRevealed && (i === opts.chosen || i === opts.revealed.answer_index)) cls += ' just';
      }
      list.appendChild(h('button', {
        class: cls, type: 'button', 'aria-pressed': !opts.revealed && opts.chosen === i ? 'true' : 'false',
        disabled: !!opts.revealed,
        onclick: function () { opts.onChoose(i); }
      }, h('span', { class: 'key' }, KEYS[i]), h('span', { class: 'val' }, text), tag ? h('span', { class: 'tag' }, tag) : null));
    });

    var extra = [];
    if (opts.revealed) {
      var ok = opts.chosen === opts.revealed.answer_index;
      extra.push(h('div', { class: 'feedback ' + (ok ? 'ok' : 'bad'), role: 'status' },
        SS.icon(ok ? 'check' : 'x'), ok ? t.correct : t.wrong));
      var sol = opts.revealed.solution[lang] || SS.pick(opts.revealed.solution);
      if (sol) extra.push(h('div', { class: 'solution' }, h('b', null, t.solution + ': '), sol));
      extra.push(h('button', { class: 'btn btn-ghost btn-sm', style: 'margin-top:8px', onclick: function () { SS.report(q.id); } },
        SS.icon('flag', 'icon-sm'), t.report));
    }
    var fresh = lastShown !== q.id; lastShown = q.id;
    return h('article', { class: fresh ? 'enter' : null, 'aria-live': 'polite' }, meta, h('p', { class: 'q-text' }, q.text[lang]), list, extra);
  }

  function actionBar() {
    var bar = h('div', { class: 'action-bar' }, h('div', { class: 'wrap' }));
    return { el: bar, inner: bar.firstChild };
  }

  // ================================================================ PRACTICE
  function practice(data) {
    var qs = data.questions, i = 0, chosen = null, shownAt = Date.now(), justRevealed = false;
    // Resume at the first unanswered question.
    for (var k = 0; k < qs.length; k++) { if (qs[k].state.answer_index === undefined) { i = k; break; } i = k; }
    var head = h('div', { class: 'player-head' });
    var body = h('div', { style: 'padding-top:16px' });
    var bar = actionBar();
    clear(root); root.append(head, body, bar.el);

    function render() {
      var q = qs[i], st = q.state;
      var revealed = st.answer_index !== undefined ? { answer_index: st.answer_index, solution: st.solution } : null;
      clear(head);
      var done = qs.filter(function (x) { return x.state.answer_index !== undefined; }).length;
      head.append(h('div', { class: 'row-between' }, h('b', null, data.title), h('span', { class: 'small muted' }, (i + 1) + ' / ' + qs.length)),
        h('div', { class: 'progress-line' }, h('i', { style: 'width:' + (100 * done / qs.length) + '%' })));
      clear(body);
      body.append(questionView(q, {
        chosen: revealed ? st.chosen : chosen, revealed: revealed, justRevealed: justRevealed,
        onChoose: function (n) { chosen = n; render(); bar.inner.querySelector('.btn-primary').focus(); },
        rerender: render
      }));
      justRevealed = false;
      clear(bar.inner);
      if (!revealed) {
        bar.inner.append(h('button', { class: 'btn btn-primary', disabled: chosen === null, onclick: check }, t.check));
      } else if (i < qs.length - 1) {
        bar.inner.append(h('button', { class: 'btn btn-primary', onclick: function () { i++; chosen = null; shownAt = Date.now(); render(); scrollTo(0, 0); } }, t.next));
      } else {
        bar.inner.append(h('button', { class: 'btn btn-primary', onclick: finish }, t.finish));
      }
    }

    function check(e) {
      var q = qs[i], btn = e.currentTarget;
      btn.disabled = true;
      SS.api('POST', '/api/v1/attempts/' + data.id + '/answer', { question_id: q.id, chosen_index: chosen, time_ms: Date.now() - shownAt })
        .then(function (r) {
          q.state = { chosen: chosen, answer_index: r.answer_index, solution: r.solution, correct: r.correct };
          justRevealed = true;
          if (navigator.vibrate && !r.correct) navigator.vibrate(60);
          render();
        })
        .catch(function (err) { btn.disabled = false; SS.toast(err.message); });
    }

    function finish(e) {
      e.currentTarget.disabled = true;
      SS.api('POST', '/api/v1/attempts/' + data.id + '/finish').then(function () { location.href = '/result/' + data.id; })
        .catch(function (err) { SS.toast(err.message); e.currentTarget.disabled = false; });
    }
    render();
  }

  // ================================================================ CBT MOCK
  function mock(data) {
    var qs = data.questions, i = 0, visited = {}, pending = {}, shownAt = Date.now(), finishing = false;
    qs.forEach(function (q) { if (q.state.chosen !== null || q.state.marked) visited[q.id] = true; });
    visited[qs[0].id] = true;
    var deadline = Date.now() + (data.remaining_sec || 0) * 1000;

    var head = h('div', { class: 'player-head' });
    var body = h('div', { style: 'padding-top:16px' });
    var bar = actionBar();
    clear(root); root.append(head, body, bar.el);

    function status(q) {
      var answered = q.state.chosen !== null && q.state.chosen !== undefined;
      if (q.state.marked) return answered ? 'marked answered' : 'marked';
      if (answered) return 'answered';
      return visited[q.id] ? 'unanswered' : '';
    }

    // Save the current question; failed saves are retried before submit.
    function save(q) {
      var spent = Date.now() - shownAt;
      shownAt = Date.now();
      pending[q.id] = { question_id: q.id, chosen_index: q.state.chosen, marked: !!q.state.marked, time_ms: spent };
      return flush();
    }
    function flush() {
      var jobs = Object.keys(pending).map(function (id) {
        var payload = pending[id];
        return SS.api('POST', '/api/v1/attempts/' + data.id + '/answer', payload)
          .then(function () { if (pending[id] === payload) delete pending[id]; })
          .catch(function (e) { if (e.status === 409) delete pending[id]; else payload.time_ms = 0; throw e; });
      });
      return Promise.all(jobs).catch(function (e) { SS.toast(e.message); });
    }

    function go(n) {
      if (n < 0 || n >= qs.length) return;
      save(qs[i]);
      i = n; visited[qs[i].id] = true;
      render(); scrollTo(0, 0);
    }

    var timerEl = h('span', { class: 'timer', role: 'timer', 'aria-live': 'off' });
    var warned = false;
    function tick() {
      var left = Math.max(0, Math.round((deadline - Date.now()) / 1000));
      var m = Math.floor(left / 60), s = left % 60;
      clear(timerEl);
      timerEl.append(SS.icon('timer', 'icon-sm'), (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s);
      timerEl.classList.toggle('low', left <= 300);
      if (left <= 300 && !warned) { warned = true; SS.toast(SS.lang === 'hi' ? '5 मिनट बचे हैं' : '5 minutes left'); }
      if (left === 0) submit(true);
    }
    var timer = setInterval(tick, 1000);

    function sectionTabs() {
      if (data.sections.length < 2) return null;
      return h('div', { class: 'sec-tabs', role: 'tablist' }, data.sections.map(function (s) {
        var active = i >= s.start && i < s.start + s.count;
        return h('button', { class: 'chip', role: 'tab', 'aria-selected': active ? 'true' : 'false', 'aria-pressed': active ? 'true' : 'false',
          onclick: function () { go(s.start); } }, SS.pick(s.name));
      }));
    }

    function currentSection() {
      return data.sections.filter(function (s) { return i >= s.start && i < s.start + s.count; })[0];
    }

    function render() {
      var q = qs[i];
      clear(head);
      var sec = currentSection();
      head.append(
        h('div', { class: 'row-between' }, h('b', { style: 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap' }, data.title), timerEl,
          h('button', { class: 'btn btn-secondary btn-sm', onclick: openPalette, 'aria-label': 'Question palette' }, SS.icon('grid', 'icon-sm'), (i + 1) + '/' + qs.length)),
        sectionTabs(),
        sec ? h('p', { class: 'xs muted', style: 'margin:6px 0 0' }, '+' + sec.marks + ' / −' + (Math.round(sec.negative * 100) / 100)) : null);
      clear(body);
      body.append(questionView(q, {
        chosen: q.state.chosen, revealed: null,
        onChoose: function (n) { q.state.chosen = n; render(); },
        rerender: render
      }));
      clear(bar.inner);
      bar.inner.append(
        h('button', { class: 'btn btn-secondary btn-sm', onclick: function () { q.state.marked = !q.state.marked; go(Math.min(i + 1, qs.length - 1)); if (i === qs.length - 1) render(); } },
          SS.icon('flag', 'icon-sm'), t.mark_review),
        h('button', { class: 'btn btn-secondary btn-sm', disabled: q.state.chosen === null, onclick: function () { q.state.chosen = null; render(); } }, t.clear),
        i < qs.length - 1
          ? h('button', { class: 'btn btn-primary btn-sm', onclick: function () { go(i + 1); } }, t.save_next)
          : h('button', { class: 'btn btn-primary btn-sm', onclick: function () { save(q); confirmSubmit(); } }, t.submit));
    }

    function counts() {
      var c = { answered: 0, marked: 0, unanswered: 0, notvisited: 0 };
      qs.forEach(function (q) {
        var s = status(q);
        if (s.indexOf('marked') === 0) c.marked++;
        if (s.indexOf('answered') !== -1 && s.indexOf('unanswered') === -1) c.answered++;
        else if (s === 'unanswered' || s === 'marked') c.unanswered++;
        if (!s) c.notvisited++;
      });
      return c;
    }

    function openPalette() {
      var c = counts();
      var dlg = h('dialog', { 'aria-label': 'Question palette' },
        h('div', { class: 'dlg-body' },
          h('div', { class: 'legend', style: 'margin-bottom:16px' },
            h('span', null, h('i', { style: 'background:var(--ok);border-color:var(--ok)' }), (SS.lang === 'hi' ? 'उत्तर दिया ' : 'Answered ') + c.answered),
            h('span', null, h('i', { style: 'background:var(--bad-soft);border-color:var(--bad)' }), (SS.lang === 'hi' ? 'उत्तर नहीं ' : 'Not answered ') + c.unanswered),
            h('span', null, h('i', { style: 'background:#7C3AED;border-color:#7C3AED;border-radius:50%' }), (SS.lang === 'hi' ? 'रिव्यू ' : 'Marked ') + c.marked),
            h('span', null, h('i'), (SS.lang === 'hi' ? 'नहीं देखे ' : 'Not visited ') + c.notvisited)),
          data.sections.map(function (s) {
            return h('section', { style: 'margin-bottom:16px' }, h('h3', null, SS.pick(s.name)),
              h('div', { class: 'palette' }, qs.slice(s.start, s.start + s.count).map(function (q, k) {
                var n = s.start + k;
                return h('button', { class: 'pal ' + status(q) + (n === i ? ' current' : ''), 'aria-label': 'Q' + (n + 1) + ' ' + status(q),
                  onclick: function () { dlg.close(); go(n); } }, String(n + 1));
              })));
          })),
        h('div', { class: 'dlg-foot' },
          h('button', { class: 'btn btn-secondary btn-sm', onclick: function () { dlg.close(); } }, '✕'),
          h('button', { class: 'btn btn-primary btn-sm', onclick: function () { dlg.close(); save(qs[i]); confirmSubmit(); } }, t.submit)));
      dlg.addEventListener('close', function () { dlg.remove(); });
      document.body.appendChild(dlg); dlg.showModal();
    }

    function confirmSubmit() {
      var c = counts();
      var msg = SS.lang === 'hi'
        ? 'उत्तर दिए: ' + c.answered + ' · बिना उत्तर: ' + (qs.length - c.answered) + '\nटेस्ट जमा करने के बाद बदलाव नहीं होगा।'
        : 'Answered: ' + c.answered + ' · Unanswered: ' + (qs.length - c.answered) + '\nYou cannot change answers after submitting.';
      var dlg = h('dialog', null, h('form', { method: 'dialog' },
        h('div', { class: 'dlg-body' }, h('h2', null, t.submit + '?'), h('p', { style: 'white-space:pre-line' }, msg)),
        h('div', { class: 'dlg-foot' }, h('button', { class: 'btn btn-secondary btn-sm', value: 'no' }, '✕'),
          h('button', { class: 'btn btn-primary btn-sm', value: 'yes' }, t.submit))));
      dlg.addEventListener('close', function () { var v = dlg.returnValue; dlg.remove(); if (v === 'yes') submit(false); });
      document.body.appendChild(dlg); dlg.showModal();
    }

    function submit(auto) {
      if (finishing) return;
      finishing = true; clearInterval(timer);
      if (auto) SS.toast(SS.lang === 'hi' ? 'समय ख़त्म — टेस्ट जमा हो रहा है' : 'Time up — submitting');
      save(qs[i]).then(function () {
        return SS.api('POST', '/api/v1/attempts/' + data.id + '/finish');
      }).then(function () { window.removeEventListener('beforeunload', guard); location.href = '/result/' + data.id; })
        .catch(function (e) { finishing = false; SS.toast(e.message); });
    }

    function guard(e) { if (!finishing) { e.preventDefault(); e.returnValue = ''; } }
    window.addEventListener('beforeunload', guard);
    document.addEventListener('visibilitychange', function () { if (document.hidden) save(qs[i]); });
    tick(); render();
  }

  // ================================================================ REVISE
  function revise(cards) {
    if (!cards.length) { clear(root); root.appendChild(h('div', { class: 'empty' }, t.revise_empty)); return; }
    var i = 0, chosen = null, revealed = null, justRevealed = false;
    var body = h('div'), bar = actionBar();
    clear(root); root.append(body, bar.el);
    function render() {
      var q = cards[i];
      clear(body);
      body.append(h('div', { class: 'progress-line', style: 'margin-bottom:16px' }, h('i', { style: 'width:' + (100 * i / cards.length) + '%' })),
        questionView(q, { chosen: chosen, revealed: revealed, justRevealed: justRevealed,
          onChoose: function (n) { chosen = n; render(); }, rerender: render }));
      justRevealed = false;
      clear(bar.inner);
      if (!revealed) bar.inner.append(h('button', { class: 'btn btn-primary', disabled: chosen === null, onclick: check }, t.check));
      else if (i < cards.length - 1) bar.inner.append(h('button', { class: 'btn btn-primary', onclick: function () { i++; chosen = null; revealed = null; render(); scrollTo(0, 0); } }, t.next));
      else bar.inner.append(h('a', { class: 'btn btn-primary', href: '/' }, t.finish));
    }
    function check(e) {
      e.currentTarget.disabled = true;
      SS.api('POST', '/api/v1/revise/' + cards[i].id, { chosen_index: chosen })
        .then(function (r) { revealed = r; justRevealed = true; render(); })
        .catch(function (err) { SS.toast(err.message); render(); });
    }
    render();
  }

  if (mode === 'revise') SS.api('GET', '/api/v1/revise').then(function (d) { revise(d.cards); }).catch(fail);
  else SS.api('GET', '/api/v1/attempts/' + attemptId).then(function (d) {
    if (d.finished) { location.href = '/result/' + d.id; return; }
    (d.mode === 'mock' ? mock : practice)(d);
  }).catch(fail);
})();
