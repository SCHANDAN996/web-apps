// Applies the saved theme before the page paints (no flash). Loaded in <head>, not deferred.
(function () {
  try {
    var t = localStorage.getItem('ss_theme');
    if (t === 'light' || t === 'dark') {
      document.documentElement.setAttribute('data-theme', t);
      // status bar follows the in-app theme, not just the phone's
      var c = t === 'dark' ? '#111318' : '#F9F9FF';
      var metas = document.querySelectorAll('meta[name="theme-color"]');
      for (var i = 0; i < metas.length; i++) { metas[i].setAttribute('content', c); metas[i].removeAttribute('media'); }
    }
  } catch (e) { /* private mode: follow the system */ }
})();
