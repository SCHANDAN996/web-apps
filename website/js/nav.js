/**
 * nav.js — Mobile navigation (hamburger drawer + language toggle)
 */
(function () {
  // ====== MOBILE DRAWER ======
  var btn     = document.getElementById('mobileMenuBtn');
  var nav     = document.getElementById('mobileNav');
  var overlay = document.getElementById('mobileNavOverlay');
  var close   = document.getElementById('mobileNavClose');

  btn.addEventListener('click', function () {
    nav.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  });

  function closeMobileNav() {
    nav.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  close.addEventListener('click', closeMobileNav);
  overlay.addEventListener('click', closeMobileNav);

  // expose globally so inline onclick handlers can use it
  window.closeMobileNav = closeMobileNav;

  // ====== LANGUAGE TOGGLE ======
  var langBtn  = document.getElementById('langToggle');
  var langSpan = langBtn.querySelector('span');
  var lang     = localStorage.getItem('language') || 'en';

  langSpan.textContent = lang === 'en' ? 'EN' : 'हिं';
  if (lang === 'hi') document.body.classList.add('hindi');

  langBtn.addEventListener('click', function () {
    lang = lang === 'en' ? 'hi' : 'en';
    langSpan.textContent = lang === 'en' ? 'EN' : 'हिं';
    document.body.classList.toggle('hindi', lang === 'hi');
    localStorage.setItem('language', lang);
  });
})();
