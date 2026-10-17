/**
 * app.js — SPA core: navigation, toast, and page init
 */

// ====== STATE ======
var currentPage = 'home';
var currentStudyClass = null;
var currentStudySubject = null;
var currentQuizData = null;
var currentQuizIndex = 0;
var quizScore = 0;
var quizAnswered = false;
var quizUserData = [];
var currentJobTab = 'latest';
var currentJobCategory = 'all';
var currentPyqTab = 'ssc';
var quizTimer = null;
var quizSeconds = 0;

// ====== NAVIGATION ======
function navigate(page) {
  document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
  document.getElementById('page-' + page).classList.add('active');

  document.querySelectorAll('.navbar__link').forEach(function(l) { l.classList.remove('active'); });
  document.querySelectorAll('.navbar__link[data-page="' + page + '"]').forEach(function(l) { l.classList.add('active'); });

  document.querySelectorAll('.mobile-nav__link').forEach(function(l) { l.classList.remove('active'); });
  document.querySelectorAll('.mobile-nav__link[data-page="' + page + '"]').forEach(function(l) { l.classList.add('active'); });

  document.querySelectorAll('.bottom-nav__link').forEach(function(l) { l.classList.remove('active'); });
  document.querySelectorAll('.bottom-nav__link[data-page="' + page + '"]').forEach(function(l) { l.classList.add('active'); });

  currentPage = page;
  if (history.replaceState) history.replaceState(null, '', page === 'home' ? '#' : '#' + page);
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (page === 'classes') renderClassesGrid();
  if (page === 'study') renderStudyClasses();
  if (page === 'practice') renderPracticeSubjects();
  if (page === 'books') renderBooks();
  if (page === 'jobs') renderJobs();
  if (page === 'pyq') renderPyq();
}

// ====== SAFE HTML HELPERS ======
// Use for any text that came from outside our own code (scraped jobs, AI replies).
function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Allow http(s) and relative links only — blocks javascript:/data: URLs.
function safeUrl(value) {
  var url = String(value == null ? '' : value).trim();
  var probe = url.replace(/[\u0000-\u0020]/g, '').toLowerCase();
  var scheme = probe.match(/^([a-z][a-z0-9+.-]*):/);
  if (scheme && scheme[1] !== 'http' && scheme[1] !== 'https') return '';
  return url;
}

// ====== TOAST ======
function showToast(msg, type) {
  type = type || 'info';
  var c = document.getElementById('toastContainer');
  var t = document.createElement('div');
  t.className = 'toast toast--' + type;
  var icons = { success: 'checkmark-circle-sharp', error: 'close-circle-sharp', info: 'information-circle-sharp' };
  t.innerHTML = '<ion-icon name="' + icons[type] + '"></ion-icon><span class="toast__msg">' + escapeHtml(msg) + '</span><button class="toast__close" onclick="this.parentElement.remove()"><ion-icon name="close-outline"></ion-icon></button>';
  c.appendChild(t);
  setTimeout(function() { t.style.opacity = '0'; t.style.transform = 'translateX(100px)'; t.style.transition = 'all 0.3s ease'; setTimeout(function() { t.remove(); }, 300); }, 4000);
}

// ====== INIT ======
window.addEventListener('load', function() {
  // Hash deep-link support: index.html#practice opens that page directly
  var hash = window.location.hash.replace('#', '');
  var validPages = ['classes', 'study', 'practice', 'books', 'jobs', 'pyq'];
  if (validPages.indexOf(hash) !== -1) navigate(hash);

  setTimeout(function() {
    document.getElementById('loadingScreen').classList.add('hidden');
  }, 1200);

  setTimeout(function() {
    document.querySelectorAll('#page-home .fade-in').forEach(function(el, i) {
      setTimeout(function() { el.classList.add('visible'); }, i * 100);
    });
  }, 1500);

  setTimeout(function() {
    showToast('Welcome to Study Station! 🎉 Explore all pages from the navigation.', 'success');
  }, 2000);
});
