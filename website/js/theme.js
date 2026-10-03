/**
 * theme.js — Dark/Light mode toggle with localStorage persistence
 */
(function () {
  const toggle = document.getElementById('themeToggle');
  const html   = document.documentElement;
  const icon   = toggle.querySelector('ion-icon');

  // Restore saved theme or use system preference
  const saved = localStorage.getItem('theme');
  if (saved) {
    html.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    html.setAttribute('data-theme', 'light');
  }
  updateIcon();

  toggle.addEventListener('click', function () {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateIcon();
  });

  function updateIcon() {
    icon.setAttribute('name',
      html.getAttribute('data-theme') === 'dark' ? 'moon-outline' : 'sunny-outline'
    );
  }
})();
