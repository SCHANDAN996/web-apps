/* Portable progress + phone-local reading/rough work. Google tokens stay in Android. */
(function () {
  'use strict';
  var MAX_BYTES = 4 * 1024 * 1024, pending = null, generation = 0;
  var PREFS = { ss_theme: ['system', 'light', 'dark', 'paper'], ss_reader_theme: ['plain', 'paper', 'night'], ss_subject: ['quant', 'reasoning', 'english', 'ga', 'science'] };
  function read(key, fallback) { try { return JSON.parse(localStorage.getItem(key) || 'null') || fallback; } catch (e) { return fallback; } }
  function object(o) { return o && typeof o === 'object' && !Array.isArray(o); }
  function chapterUrl(u) { return typeof u === 'string' && /^\/books\/[a-z0-9-]+\/[a-z0-9-]+(?:\?[^#]*)?$/.test(u) && u.length <= 500; }
  function validate(data) {
    if (!object(data) || new TextEncoder().encode(JSON.stringify(data)).length > MAX_BYTES) throw new Error('invalid_backup');
    if (data.schema_version === 1) data = { format: 'study-station-backup', version: 1, progress: data, local: {} };
    if (data.format !== 'study-station-backup' || data.version !== 1 || !object(data.progress) || data.progress.schema_version !== 1 || !object(data.local)) throw new Error('invalid_backup');
    var local = data.local, reading = local.reading || [], prefs = local.preferences || {}, last = local.lastChapter || null;
    if (!Array.isArray(reading) || reading.length > 500 || !reading.every(chapterUrl) || !object(prefs)) throw new Error('invalid_backup');
    var cleanPrefs = {};
    Object.keys(prefs).forEach(function (key) {
      var value = prefs[key];
      if (key === 'ss_reader_scale') { if (typeof value !== 'number' || !Number.isFinite(value) || value < .85 || value > 1.5) throw new Error('invalid_backup'); }
      else if (!PREFS[key] || PREFS[key].indexOf(value) === -1) throw new Error('invalid_backup');
      cleanPrefs[key] = value;
    });
    if (last && (!object(last) || !chapterUrl(last.url) || ['hi', 'en'].some(function (lang) { return typeof last[lang] !== 'string' || last[lang].length > 300; }))) throw new Error('invalid_backup');
    return { format: data.format, version: 1, progress: data.progress, local: {
      workspaces: window.SSWorkspaceStore?SSWorkspaceStore.validateAll(local.workspaces||[]):[], whiteboards: window.SSWhiteboard.validate(local.whiteboards || {}), reading: reading,
      preferences: cleanPrefs, lastChapter: last ? { url: last.url, hi: last.hi, en: last.en } : null
    } };
  }
  function localState() {
    var prefs = {};
    try {
      Object.keys(PREFS).forEach(function (key) { var v = localStorage.getItem(key); if (PREFS[key].indexOf(v) !== -1) prefs[key] = v; });
      var scale = Number(localStorage.getItem('ss_reader_scale'));
      if (scale >= .85 && scale <= 1.5) prefs.ss_reader_scale = scale;
    } catch (e) {}
    return { whiteboards: window.SSWhiteboard.export(), reading: read('ss_read_chapters', []), lastChapter: read('ss_last_chapter', null), preferences: prefs };
  }
  function message(text) { var el = document.getElementById('backupStatus'); if (el) el.textContent = text; }
  function errorMessage(code) {
    var t = window.SS.t;
    return code === 'cancelled' ? t.backup_cancelled : code === 'no_backup' ? t.backup_none :
      code === 'not_configured' ? t.backup_drive_setup : code === 'invalid_backup' || code === 'too_large' ? t.backup_invalid :
      code === 'storage_full' ? t.backup_local_partial : t.backup_failed;
  }
  function nativeBridge() { return window.StudyStationNative; }
  function driveConfigured() { try { return !!(nativeBridge() && nativeBridge().driveConfigured()); } catch (e) { return false; } }
  function setBusy(on) { document.querySelectorAll('[data-backup-action]').forEach(function (b) { b.disabled = on; b.setAttribute('aria-busy', String(on)); }); }
  function finish() { pending = null; setBusy(false); window.SSBackup.refresh(); }
  function exportAll() {
    return window.SS.api('GET', '/api/v1/backup/export').then(async function (progress) {
      if(window.SSWorkspaceReady)await window.SSWorkspaceReady;
      var data = { format: 'study-station-backup', version: 1, created_at: new Date().toISOString(), progress: progress, local: localState() };
      if(window.SSWorkspaceStore)data.local.workspaces=await SSWorkspaceStore.exportAll();
      validate(data); return data;
    });
  }
  function confirmRestore(raw) {
    if (!pending || !document.getElementById('backup')) return;
    var pageGeneration = generation;
    var data;
    try { data = validate(typeof raw === 'string' ? JSON.parse(raw) : raw); }
    catch (e) { finish(); message(errorMessage('invalid_backup')); return; }
    var SS = window.SS, h = SS.h, t = SS.t;
    var cancel = h('button', { class: 'btn btn-secondary', type: 'button', autofocus: true }, t.cancel);
    var apply = h('button', { class: 'btn btn-primary', type: 'button' }, t.backup_restore);
    var dlg = h('dialog', { 'aria-labelledby': 'backupRestoreTitle', 'aria-describedby': 'backupRestoreWarning', 'data-backup-dialog': '' },
      h('div', { class: 'dlg-body' }, h('h2', { id: 'backupRestoreTitle' }, t.backup_restore), h('p', { id: 'backupRestoreWarning' }, t.backup_restore_confirm)),
      h('div', { class: 'dlg-foot' }, cancel, apply));
    var accepted = false, restoring = false;
    dlg.addEventListener('cancel', function (e) { if (restoring) e.preventDefault(); });
    cancel.addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('close', function () { dlg.remove(); if (!accepted && generation === pageGeneration) { finish(); message(t.backup_cancelled); } });
    apply.addEventListener('click', function () {
      restoring = true; apply.disabled = cancel.disabled = true;
      SS.api('POST', '/api/v1/backup/restore', { confirm: true, backup: data.progress }).then(async function () {
        accepted = true;
        var notice = t.backup_restored;
        try {
          window.SSWhiteboard.merge(data.local.whiteboards);
          if(window.SSWorkspaceStore)await SSWorkspaceStore.restoreAll(data.local.workspaces);
          var existing = read('ss_read_chapters', []);
          if (!Array.isArray(existing)) existing = [];
          var merged = Array.from(new Set(existing.filter(chapterUrl).concat(data.local.reading))).slice(-500);
          localStorage.setItem('ss_read_chapters', JSON.stringify(merged));
          if (data.local.lastChapter) localStorage.setItem('ss_last_chapter', JSON.stringify(data.local.lastChapter));
          Object.keys(data.local.preferences).forEach(function (key) {
            var value = data.local.preferences[key];
            if (key === 'ss_theme') window.SSTheme.set(value);
            else localStorage.setItem(key, String(value));
          });
          message(t.backup_restored);
        } catch (e) { notice = t.backup_local_partial; message(notice); }
        dlg.close(); if (generation === pageGeneration) finish();
        // Settings may include another restored language/qualification. Fetch that screen again.
        if (generation === pageGeneration) Promise.resolve(SS.go('/settings', true)).then(function () { SS.toast(notice); });
      }).catch(function (e) { if (generation !== pageGeneration) return; restoring = false; apply.disabled = cancel.disabled = false; message(e.message || t.backup_failed); });
    });
    document.body.appendChild(dlg); dlg.showModal();
  }
  function request(action) {
    if (pending) return;
    var SS = window.SS, bridge = nativeBridge(), pageGeneration = generation; pending = action; setBusy(true); message(SS.t.backup_busy);
    if (action === 'local-restore') {
      if (bridge && typeof bridge.requestLocalRestore === 'function') { try { bridge.requestLocalRestore(); } catch (e) { finish(); message(SS.t.backup_failed); } return; }
      var input = document.getElementById('backupFile'); input.click(); finish(); return;
    }
    if (action === 'restore') {
      if (!driveConfigured()) { finish(); message(SS.t.backup_drive_setup); return; }
      try { bridge.requestDriveRestore(); } catch (e) { finish(); message(SS.t.backup_failed); }
      return;
    }
    exportAll().then(function (data) {
      if (generation !== pageGeneration) return;
      var json = JSON.stringify(data);
      if (action === 'backup') {
        if (!driveConfigured()) throw new Error('not_configured');
        bridge.requestDriveBackup(json); return;
      }
      if (bridge && typeof bridge.requestLocalBackup === 'function') { bridge.requestLocalBackup(json); return; }
      if (/StudyStationApp\//.test(navigator.userAgent)) throw new Error('not_configured');
      var url = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
      var a = document.createElement('a'); a.href = url; a.download = 'study-station-backup-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
      finish(); message(SS.t.backup_downloaded);
    }).catch(function (e) { if (generation !== pageGeneration) return; finish(); message(e.code ? e.message : errorMessage(e.message)); });
  }
  window.SSBackup = {
    validate: validate, export: exportAll,
    init: function () {
      var section = document.getElementById('backup'); if (!section || section.dataset.wired) return;
      section.dataset.wired = '1';
      window.SS.onLeave(function () { generation++; finish(); document.querySelectorAll('[data-backup-dialog]').forEach(function (dlg) { dlg.close(); }); });
      section.querySelectorAll('[data-backup-action]').forEach(function (b) { b.addEventListener('click', function () { request(b.getAttribute('data-backup-action')); }); });
      var input = document.getElementById('backupFile');
      input.addEventListener('change', function () {
        var file = input.files[0]; input.value = ''; if (!file) return;
        if (file.size > MAX_BYTES) { message(window.SS.t.backup_invalid); return; }
        pending = 'local-restore'; setBusy(true);
        var fileGeneration = generation;
        file.text().then(function (raw) { if (generation === fileGeneration) confirmRestore(raw); }).catch(function () { if (generation === fileGeneration) { finish(); message(window.SS.t.backup_invalid); } });
      });
      this.refresh();
    },
    refresh: function () {
      var section = document.getElementById('backup'); if (!section) return;
      var configured = driveConfigured();
      section.querySelectorAll('[data-drive-action]').forEach(function (b) { b.disabled = !configured || !!pending; });
      document.getElementById('driveSetupStatus').textContent = configured ? window.SS.t.backup_drive_ready : window.SS.t.backup_drive_setup;
    }
  };
  window.addEventListener('ss-native-ready', function () { window.SSBackup.refresh(); });
  window.addEventListener('ss-drive-result', function (e) {
    var result = e.detail;
    if (!pending || !object(result) || result.operation !== pending) return;
    if (!result.ok) { finish(); message(errorMessage(result.error)); return; }
    if (pending === 'restore' || pending === 'local-restore') confirmRestore(result.data);
    else { finish(); message(window.SS.t.backup_saved); }
  });
  window.SSBackup.init();
})();
