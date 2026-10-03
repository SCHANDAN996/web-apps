// Applies the saved theme before the page paints (no flash). Loaded in <head>, not deferred.
(function () {
  try {
    var t = localStorage.getItem('ss_theme');
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  } catch (e) { /* private mode: follow the system */ }
})();
