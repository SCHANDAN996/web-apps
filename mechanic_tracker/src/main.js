/**
 * Main entry — SPA router, auth guard, notification init
 */
import './style.css';
import { renderNav, hideNav } from './components/nav.js';
import { renderAuth } from './pages/auth.js';
import { renderDashboard } from './pages/dashboard.js';
import { renderAddPart } from './pages/add-part.js';
import { renderTracker } from './pages/tracker.js';
import { renderSettings } from './pages/settings.js';
import { initNotifications } from './lib/notifications.js';
import { getParts } from './lib/store.js';

let currentUser = null;

// ──── Router ────
function getRoute() {
  const hash = window.location.hash.replace('#', '') || '/';
  return hash;
}

async function navigate() {
  const container = document.getElementById('page-container');
  const route = getRoute();

  if (!currentUser) {
    hideNav();
    renderAuth(container, (user) => {
      currentUser = user;
      window.location.hash = '#/';
      navigate();
      // Start deadline notifications
      initNotifications(() => getParts('All'));
    });
    return;
  }

  // Reset animation
  container.style.animation = 'none';
  container.offsetHeight; // trigger reflow
  container.style.animation = '';

  renderNav(route);

  switch (route) {
    case '/':
      await renderDashboard(container);
      break;
    case '/add':
      await renderAddPart(container);
      break;
    case '/tracker':
      await renderTracker(container);
      break;
    case '/settings':
      await renderSettings(container);
      break;
    default:
      window.location.hash = '#/';
      return;
  }
}

// ──── Init ────
window.addEventListener('hashchange', navigate);
window.addEventListener('load', () => {
  navigate();
  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
});
