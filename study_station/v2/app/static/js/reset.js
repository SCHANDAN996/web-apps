/* Explicit learner-owned resets. Scoped resets preserve mixed-subject mocks. */
(function () {
  'use strict';
  var generation = 0;
  function label(item, key) { return item[key + (window.SS.lang === 'en' ? '_en' : '_hi')] || ''; }
  function localReset(scope, result) {
    if (scope === 'all') {
      if (window.SSWhiteboard) window.SSWhiteboard.clearAll();
      localStorage.removeItem('ss_read_chapters'); localStorage.removeItem('ss_last_chapter');
      return;
    }
    if (window.SSWhiteboard) window.SSWhiteboard.remove(result.whiteboard_question_ids || []);
    var urls = new Set(result.reading_urls || []);
    var reading = JSON.parse(localStorage.getItem('ss_read_chapters') || '[]');
    if (Array.isArray(reading)) localStorage.setItem('ss_read_chapters', JSON.stringify(reading.filter(function (u) { return !urls.has(u); })));
    var last = JSON.parse(localStorage.getItem('ss_last_chapter') || 'null');
    if (last && urls.has(last.url)) localStorage.removeItem('ss_last_chapter');
  }
  window.SSReset = { init: function () {
    var section = document.getElementById('resetStudy');
    if (!section || section.dataset.wired) return;
    section.dataset.wired = '1';
    var SS = window.SS, t = SS.t, h = SS.h, options = null, seq = generation;
    var scope = document.getElementById('resetScope'), subject = document.getElementById('resetSubject');
    var book = document.getElementById('resetBook'), chapter = document.getElementById('resetChapter');
    var action = document.getElementById('resetProgress'), impact = document.getElementById('resetImpact');
    var status = document.getElementById('resetStatus');
    SS.onLeave(function () { generation++; });
    function selectedChapter() { return options && options.chapters.find(function (c) { return c.book === book.value && c.chapter === chapter.value; }); }
    function update() {
      document.getElementById('resetSubjectField').hidden = scope.value !== 'subject';
      document.getElementById('resetBookField').hidden = document.getElementById('resetChapterField').hidden = scope.value !== 'chapter';
      var chosen = selectedChapter();
      impact.textContent = scope.value === 'all' ? t.reset_impact_all : scope.value === 'subject' ? t.reset_impact_subject :
        chosen && chosen.topic_label_hi ? t.reset_impact_chapter_topic.replace('{topic}', label(chosen, 'topic_label')) : t.reset_impact_chapter_reading;
      action.textContent = scope.value === 'all' ? t.reset_progress_action : t.reset_selected_action;
      action.disabled = scope.value !== 'all' && (!options || (scope.value === 'subject' ? !subject.value : !chosen));
    }
    function fillChapters() {
      chapter.replaceChildren(h('option', { value: '' }, t.reset_choose_chapter));
      if (options) options.chapters.filter(function (c) { return c.book === book.value; }).forEach(function (c) { chapter.appendChild(h('option', { value: c.chapter }, label(c, 'title'))); });
      update();
    }
    scope.addEventListener('change', update); subject.addEventListener('change', update);
    book.addEventListener('change', fillChapters); chapter.addEventListener('change', update);
    SS.api('GET', '/api/v1/me/reset-options').then(function (data) {
      if (generation !== seq) return;
      options = data;
      data.subjects.forEach(function (s) { subject.appendChild(h('option', { value: s.slug }, label(s, 'title'))); });
      var seen = new Set();
      data.chapters.forEach(function (c) { if (!seen.has(c.book)) { seen.add(c.book); book.appendChild(h('option', { value: c.book }, label(c, 'book_title'))); } });
      update();
    }).catch(function (e) { if (generation === seq) { status.textContent = e.message || t.reset_options_failed; update(); } });
    action.addEventListener('click', function () {
      if (action.disabled) return;
      var selectedScope = scope.value, chosen = selectedChapter();
      var name = selectedScope === 'all' ? t.reset_scope_all : selectedScope === 'subject' ? subject.selectedOptions[0].textContent : label(chosen, 'book_title') + ' · ' + label(chosen, 'title');
      var warning = impact.textContent;
      var body = { confirm: true, scope: selectedScope };
      if (selectedScope === 'subject') body.subject = subject.value;
      if (selectedScope === 'chapter') { body.book = chosen.book; body.chapter = chosen.chapter; }
      if (selectedScope !== 'all') body.whiteboard_question_ids = window.SSWhiteboard ? Object.keys(window.SSWhiteboard.export()).map(Number) : [];
      var cancel = h('button', { class: 'btn btn-secondary', type: 'button', autofocus: true }, t.cancel);
      var confirm = h('button', { class: 'btn btn-primary', type: 'button' }, selectedScope === 'all' ? t.reset_progress_action : t.reset_selected_action);
      var dlg = h('dialog', { 'aria-labelledby': 'resetTitle', 'aria-describedby': 'resetWarning' },
        h('div', { class: 'dlg-body' }, h('h2', { id: 'resetTitle' }, t.reset_confirm_selected), h('p', { class: 'reset-selection' }, name),
          h('p', { id: 'resetWarning' }, warning), h('p', { class: 'small muted' }, t.reset_common_warning)),
        h('div', { class: 'dlg-foot' }, cancel, confirm));
      var running = false;
      cancel.addEventListener('click', function () { dlg.close(); });
      dlg.addEventListener('cancel', function (e) { if (running) e.preventDefault(); });
      dlg.addEventListener('close', function () { dlg.remove(); if (action.isConnected) action.focus(); });
      confirm.addEventListener('click', function () {
        running = true; confirm.disabled = cancel.disabled = true;
        SS.api('POST', '/api/v1/me/reset-progress', body).then(function (result) {
          var notice = t.reset_done;
          try { localReset(selectedScope, result); } catch (e) { notice = t.reset_local_partial; }
          dlg.close();
          if (generation === seq) Promise.resolve(SS.go(selectedScope === 'all' ? '/' : '/settings', true)).then(function () { SS.toast(notice); });
        }).catch(function (e) { if (generation !== seq) return; running = false; confirm.disabled = cancel.disabled = false; SS.toast(e.message); });
      });
      document.body.appendChild(dlg); dlg.showModal();
    });
    update();
  }, clearLocal: localReset };
  window.SSReset.init();
})();
