/* View-only pointer navigation. Saved document coordinates remain normalized. */
(function () {
  'use strict';
  window.SSWorkspaceGestures = {
    attach: function (stage, canvas, callbacks) {
      const cb = callbacks || {}, pointers = new Map(), listeners = [];
      const width = canvas.width || 900, height = canvas.height || 1200, margin = 12;
      let size = { width: 0, height: 0 }, base = 1, zoom = 1, x = margin, y = margin;
      let mode = 'idle', pinch = null, pan = null, frame = 0, destroyed = false;
      const previous = { touchAction: stage.style.touchAction, position: canvas.style.position, width: canvas.style.width, height: canvas.style.height, transform: canvas.style.transform, transformOrigin: canvas.style.transformOrigin, left: canvas.style.left, top: canvas.style.top, maxWidth: canvas.style.maxWidth, margin: canvas.style.margin };
      stage.style.touchAction = 'none';
      Object.assign(canvas.style, { position: 'absolute', left: '0', top: '0', width: width + 'px', height: height + 'px', maxWidth: 'none', margin: '0', transformOrigin: '0 0' });
      function view() { return { zoom, x, y, scale: base * zoom }; }
      function bounds() {
        const w = width * base * zoom, h = height * base * zoom;
        x = w <= size.width - margin * 2 ? (size.width - w) / 2 : Math.max(size.width - margin - w, Math.min(margin, x));
        y = h <= size.height - margin * 2 ? (size.height - h) / 2 : Math.max(size.height - margin - h, Math.min(margin, y));
      }
      function apply() {
        bounds();
        if (frame || destroyed) return;
        frame = requestAnimationFrame(function () { frame = 0; canvas.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + (base * zoom) + ')'; if (cb.onView) cb.onView(view()); });
      }
      function measure(initial) {
        if (!initial && stage.clientWidth === size.width && stage.clientHeight === size.height) return;
        if (!initial && pointers.size) cancel();
        const oldScale = base * zoom, cx = (size.width / 2 - x) / oldScale, cy = (size.height / 2 - y) / oldScale;
        size = { width: stage.clientWidth, height: stage.clientHeight };
        base = Math.max(.001, (size.width - margin * 2) / width);
        if (initial) { x = margin; y = margin; } else { x = size.width / 2 - cx * base * zoom; y = size.height / 2 - cy * base * zoom; }
        apply();
      }
      function local(e) { const r = stage.getBoundingClientRect(); return { x: e.clientX - r.left - stage.clientLeft, y: e.clientY - r.top - stage.clientTop, type: e.pointerType }; }
      function point(p) { const a = (p.x - x) / (base * zoom * width), b = (p.y - y) / (base * zoom * height); return a < 0 || b < 0 || a > 1 || b > 1 ? null : [a, b]; }
      function cancel() { if (mode === 'draw' && cb.onCancel) cb.onCancel(); mode = pointers.size ? 'wait' : 'idle'; pinch = pan = null; }
      function pair() { return Array.from(pointers.values()).slice(0, 2); }
      function startPinch() {
        const p = pair(), mid = { x: (p[0].x + p[1].x) / 2, y: (p[0].y + p[1].y) / 2 };
        pinch = { distance: Math.max(1, Math.hypot(p[1].x - p[0].x, p[1].y - p[0].y)), zoom, anchorX: (mid.x - x) / (base * zoom), anchorY: (mid.y - y) / (base * zoom) };
        mode = 'pinch'; pan = null;
      }
      function down(e) {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        e.preventDefault();
        // A resting touch must not cancel or move an active stylus stroke.
        // A pen arriving during another active pointer waits for a fresh gesture.
        if (pointers.size && (e.pointerType === 'pen' || Array.from(pointers.values()).some(p => p.type === 'pen'))) return;
        pointers.set(e.pointerId, local(e));
        try { stage.setPointerCapture(e.pointerId); } catch (_) {}
        if (pointers.size > 2) { cancel(); return; }
        if (pointers.size === 2) { if (mode === 'draw' && cb.onCancel) cb.onCancel(); if (mode === 'wait') return; startPinch(); return; }
        if (mode === 'wait') return;
        const p = pointers.get(e.pointerId);
        if (cb.getTool && cb.getTool() === 'hand') { mode = 'pan'; pan = { start: p, x, y }; }
        else { const q = point(p); if (!q) { mode = 'outside'; return; } mode = 'draw'; if (cb.onStart) cb.onStart(q, e); }
      }
      function move(e) {
        if (!pointers.has(e.pointerId)) return;
        e.preventDefault(); const p = local(e); pointers.set(e.pointerId, p);
        if (mode === 'draw') { const q = point(p); if (!q) { if (cb.onEnd) cb.onEnd(); mode = 'wait'; } else if (cb.onMove) cb.onMove(q, e); }
        else if (mode === 'pan') { x = pan.x + p.x - pan.start.x; y = pan.y + p.y - pan.start.y; apply(); }
        else if (mode === 'pinch' && pointers.size === 2) {
          const ps = pair(), mid = { x: (ps[0].x + ps[1].x) / 2, y: (ps[0].y + ps[1].y) / 2 };
          zoom = Math.max(.1, Math.min(4, pinch.zoom * Math.hypot(ps[1].x - ps[0].x, ps[1].y - ps[0].y) / pinch.distance));
          x = mid.x - pinch.anchorX * base * zoom; y = mid.y - pinch.anchorY * base * zoom; apply();
        }
      }
      function up(e) {
        if (!pointers.has(e.pointerId)) return;
        pointers.delete(e.pointerId);
        if (mode === 'draw' && cb.onEnd) cb.onEnd();
        if (mode === 'pinch') { pinch = null; mode = pointers.size ? 'wait' : 'idle'; }
        else mode = pointers.size ? 'wait' : 'idle';
        pan = null;
      }
      function abort(e) { if (!pointers.has(e.pointerId)) return; pointers.delete(e.pointerId); cancel(); }
      function background() { cancel(); pointers.clear(); mode = 'idle'; }
      function on(target, type, fn) { target.addEventListener(type, fn, { passive: false }); listeners.push(() => target.removeEventListener(type, fn)); }
      on(stage, 'pointerdown', down); on(stage, 'pointermove', move); on(stage, 'pointerup', up); on(stage, 'pointercancel', abort); on(stage, 'lostpointercapture', abort); on(window, 'blur', background);
      const visibility = function () { if (document.hidden) background(); }; on(document, 'visibilitychange', visibility);
      const observer = typeof ResizeObserver === 'function' ? new ResizeObserver(() => measure(false)) : null;
      if (observer) observer.observe(stage); else on(window, 'resize', () => measure(false));
      measure(true);
      function setZoom(value) { if (!Number.isFinite(value)) return; const old = base * zoom, cx = (size.width / 2 - x) / old, cy = (size.height / 2 - y) / old; cancel(); zoom = Math.max(.1, Math.min(4, value)); x = size.width / 2 - cx * base * zoom; y = size.height / 2 - cy * base * zoom; apply(); }
      return {
        getView: view, setZoom, zoomBy: factor => setZoom(zoom * factor),
        panBy: function (dx, dy) { if (!Number.isFinite(dx) || !Number.isFinite(dy)) return; cancel(); x += dx; y += dy; apply(); },
        reset: function () { cancel(); zoom = 1; x = margin; y = margin; apply(); },
        fit: function () { cancel(); zoom = Math.max(.1, Math.min(4, Math.min((size.width - margin * 2) / width, (size.height - margin * 2) / height) / base)); x = margin; y = margin; apply(); },
        destroy: function () { destroyed = true; background(); listeners.forEach(fn => fn()); if (observer) observer.disconnect(); if (frame) cancelAnimationFrame(frame); stage.style.touchAction = previous.touchAction; ['position','width','height','transform','transformOrigin','left','top','maxWidth','margin'].forEach(k => canvas.style[k] = previous[k]); }
      };
    }
  };
})();
