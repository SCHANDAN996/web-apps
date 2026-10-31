// Applies the saved theme before the page paints (no flash). Loaded in <head>, not deferred.
(function () {
  var current = 'system';
  try { current = localStorage.getItem('ss_theme') || 'system'; } catch (e) {}
  if (['light', 'dark', 'paper'].indexOf(current) === -1) current = 'system';
  function apply(t) {
    if (t === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', t);
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) {
      var dark = i === 1;
      metas[i].setAttribute('content', t === 'paper' ? '#FBF6EC' : (t === 'dark' || (t === 'system' && dark) ? '#111318' : '#F9F9FF'));
      if (t === 'system') metas[i].setAttribute('media', '(prefers-color-scheme: ' + (dark ? 'dark' : 'light') + ')');
      else metas[i].removeAttribute('media');
    }
  }
  window.SSTheme = {
    current: function () { return current; },
    set: function (t) {
      if (['system', 'light', 'dark', 'paper'].indexOf(t) === -1) return;
      current = t;
      try { if (t === 'system') localStorage.removeItem('ss_theme'); else localStorage.setItem('ss_theme', t); } catch (e) {}
      apply(t);
    }
  };
  apply(current);
  // Inside the Android app the system bars are handled natively: the page can use a tighter frame.
  if (navigator.userAgent.indexOf('StudyStationApp/') !== -1) document.documentElement.classList.add('in-app');
})();
