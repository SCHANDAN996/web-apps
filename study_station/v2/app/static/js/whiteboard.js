/* Per-question rough work. Coordinates are normalized so drawings survive phone rotation. */
(function () {
  'use strict';
  var KEY = 'ss_whiteboards_v1', MAX_BOARDS = 80, MAX_POINTS = 12000, MAX_STROKES = 200;
  var opened = {}, cache = null, disposeCurrent = null, leaveRegistered = false;
  function valid(raw) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Error('invalid_backup');
    var out = {}, total = 0, ids = Object.keys(raw);
    if (ids.length > MAX_BOARDS) throw new Error('invalid_backup');
    ids.forEach(function (id) {
      if (!/^[1-9][0-9]{0,9}$/.test(id)) throw new Error('invalid_backup');
      var board = raw[id];
      if (!board || !Array.isArray(board.strokes) || board.strokes.length > MAX_STROKES) throw new Error('invalid_backup');
      var strokes = board.strokes.map(function (s) {
        if (!s || ['pen', 'erase'].indexOf(s.tool) === -1 || ['black', 'blue', 'green'].indexOf(s.color) === -1 ||
            !Array.isArray(s.points) || !s.points.length) throw new Error('invalid_backup');
        var points = s.points.map(function (p) {
          if (!Array.isArray(p) || p.length !== 2 || !p.every(function (n) { return typeof n === 'number' && Number.isFinite(n) && n >= 0 && n <= 1; })) throw new Error('invalid_backup');
          return [p[0], p[1]];
        });
        total += points.length;
        if (total > MAX_POINTS) throw new Error('invalid_backup');
        return { tool: s.tool, color: s.color, points: points };
      });
      out[id] = { strokes: strokes, updated: typeof board.updated === 'number' && Number.isFinite(board.updated) ? board.updated : 0 };
    });
    return out;
  }
  function load() {
    if (cache) return cache;
    try { cache = valid(JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { cache = {}; }
    return cache;
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(cache)); return true; } catch (e) { return false; }
  }
  function trim() {
    var ids = Object.keys(cache).sort(function (a, b) { return cache[a].updated - cache[b].updated; });
    var points = function () { return Object.keys(cache).reduce(function (sum, id) { return sum + cache[id].strokes.reduce(function (n, s) { return n + s.points.length; }, 0); }, 0); };
    while (ids.length > MAX_BOARDS || points() > MAX_POINTS) delete cache[ids.shift()];
  }
  window.SSWhiteboard = {
    validate: valid,
    export: function () { return JSON.parse(JSON.stringify(load())); },
    merge: function (raw) {
      var incoming = valid(raw); load();
      Object.keys(incoming).forEach(function (id) { if (!cache[id] || incoming[id].updated > cache[id].updated) cache[id] = incoming[id]; });
      trim(); if (!save()) throw new Error('storage_full');
    },
    clearAll: function () { cache = {}; opened = {}; try { localStorage.removeItem(KEY); } catch (e) {} },
    remove: function (ids) {
      load();
      ids.forEach(function (id) { delete cache[String(id)]; delete opened[String(id)]; });
      if (!save()) throw new Error('storage_full');
    },
    create: function (qid) {
      if (disposeCurrent) disposeCurrent();
      var SS = window.SS, h = SS.h, t = SS.t, id = String(qid);
      load();
      var board = cache[id] || { strokes: [], updated: 0 }, tool = 'pen', color = 'black', drawing = null, pointer = null;
      var host = h('section', { class: 'rough-work' });
      var toggle = h('button', { class: 'btn btn-ghost btn-sm rough-toggle', type: 'button', 'aria-expanded': String(!!opened[id]), 'aria-controls': 'rough-' + id }, SS.icon('pen', 'icon-sm'), t.rough_work);
      var panel = h('div', { id: 'rough-' + id, class: 'rough-panel', hidden: !opened[id] });
      var canvas = h('canvas', { class: 'rough-canvas', 'aria-label': t.rough_canvas, role: 'img' });
      var status = h('p', { class: 'xs muted rough-status', role: 'status' }, t.rough_hint);
      var toolbar = h('div', { class: 'rough-tools', role: 'group', 'aria-label': t.rough_tools });
      var ctx = canvas.getContext('2d');
      var tokens = getComputedStyle(document.documentElement);
      var colors = { black: tokens.getPropertyValue('--paper-text').trim(), blue: tokens.getPropertyValue('--rough-blue').trim(), green: tokens.getPropertyValue('--rough-green').trim() };
      function paintStroke(s) {
        ctx.globalCompositeOperation = s.tool === 'erase' ? 'destination-out' : 'source-over';
        ctx.strokeStyle = ctx.fillStyle = colors[s.color];
        ctx.lineWidth = canvas.width * (s.tool === 'erase' ? .045 : .006);
        ctx.lineCap = ctx.lineJoin = 'round';
        ctx.beginPath();
        s.points.forEach(function (p, i) { if (!i) ctx.moveTo(p[0] * canvas.width, p[1] * canvas.height); else ctx.lineTo(p[0] * canvas.width, p[1] * canvas.height); });
        ctx.stroke();
        if (s.points.length === 1) { ctx.beginPath(); ctx.arc(s.points[0][0] * canvas.width, s.points[0][1] * canvas.height, ctx.lineWidth / 2, 0, Math.PI * 2); ctx.fill(); }
      }
      function redraw() {
        var rect = canvas.getBoundingClientRect(), ratio = Math.min(window.devicePixelRatio || 1, 2);
        if (!rect.width) return;
        canvas.width = Math.round(rect.width * ratio); canvas.height = Math.round(rect.height * ratio);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        board.strokes.forEach(paintStroke); if (drawing) paintStroke(drawing);
      }
      function persist() {
        while (board.strokes.reduce(function (n, s) { return n + s.points.length; }, 0) > 6000) board.strokes.shift();
        board.updated = Date.now(); cache[id] = board; trim();
        status.textContent = save() ? t.rough_saved : t.rough_storage;
      }
      function updateTools() {
        toolbar.querySelectorAll('[data-rough-tool]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-rough-tool') === tool)); });
      }
      ['pen', 'erase'].forEach(function (v) {
        toolbar.appendChild(h('button', { class: 'btn btn-secondary btn-sm', type: 'button', 'data-rough-tool': v, 'aria-pressed': String(v === tool), onclick: function () { tool = v; updateTools(); } }, t['rough_' + v]));
      });
      toolbar.appendChild(h('button', { class: 'btn btn-ghost btn-sm', type: 'button', onclick: function () { board.strokes.pop(); persist(); redraw(); } }, t.rough_undo));
      toolbar.appendChild(h('button', { class: 'btn btn-ghost btn-sm', type: 'button', onclick: function () { if (board.strokes.length && window.confirm(t.rough_clear_confirm)) { board.strokes = []; persist(); redraw(); } } }, t.rough_clear));
      var palette = h('div', { class: 'rough-colors', role: 'group', 'aria-label': t.rough_colors });
      Object.keys(colors).forEach(function (v) {
        palette.appendChild(h('button', { class: 'rough-color rough-color-' + v, type: 'button', 'aria-label': t['rough_' + v], 'aria-pressed': String(v === color), onclick: function () {
          color = v; tool = 'pen'; updateTools(); palette.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.classList.contains('rough-color-' + v))); });
        } }, h('span', { 'aria-hidden': 'true' })));
      });
      panel.append(toolbar, palette, canvas, status); host.append(toggle, panel);
      toggle.addEventListener('click', function () { panel.hidden = !panel.hidden; opened[id] = !panel.hidden; toggle.setAttribute('aria-expanded', String(!panel.hidden)); if (!panel.hidden) requestAnimationFrame(redraw); });
      function point(e) { var r = canvas.getBoundingClientRect(); return [Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)), Math.max(0, Math.min(1, (e.clientY - r.top) / r.height))]; }
      canvas.addEventListener('pointerdown', function (e) {
        if (pointer !== null || (e.pointerType === 'mouse' && e.button !== 0)) return;
        e.preventDefault(); pointer = e.pointerId; canvas.setPointerCapture(pointer);
        drawing = { tool: tool, color: color, points: [point(e)] }; redraw();
      });
      canvas.addEventListener('pointermove', function (e) {
        if (pointer !== e.pointerId || !drawing || drawing.points.length >= 1500) return;
        drawing.points.push(point(e)); redraw();
      });
      function finish(e) {
        if (e.pointerId !== pointer || !drawing) return;
        board.strokes.push(drawing); if (board.strokes.length > MAX_STROKES) board.strokes.shift();
        drawing = null; pointer = null; persist(); redraw();
      }
      canvas.addEventListener('pointerup', finish); canvas.addEventListener('pointercancel', finish);
      var resize = typeof ResizeObserver === 'function' ? new ResizeObserver(redraw) : null;
      disposeCurrent = function () {
        if (drawing) { board.strokes.push(drawing); if (board.strokes.length > MAX_STROKES) board.strokes.shift(); drawing = null; pointer = null; persist(); }
        if (resize) resize.disconnect();
      };
      if (resize) resize.observe(canvas);
      if (!leaveRegistered) {
        leaveRegistered = true;
        SS.onLeave(function () {
          if (disposeCurrent) disposeCurrent();
          disposeCurrent = null; leaveRegistered = false;
        });
      }
      if (opened[id]) requestAnimationFrame(redraw);
      return host;
    }
  };
})();
