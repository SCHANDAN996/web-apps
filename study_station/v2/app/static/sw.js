/* Study Station v2 service worker: offline shell, network-first pages, never caches API data.
   Book pages (/books/…) are the same for everyone, so visited ones are kept for offline reading. */
const VERSION = 'ss2-v1';
const BOOKS = 'ss2-books-v1';
const BOOKS_MAX = 80;           // pages kept for offline reading (oldest dropped first)
const SHELL = ['/static/css/app.css', '/static/js/app.js', '/static/js/player.js', '/static/icon.svg', '/offline'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION && k !== BOOKS).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;

  if (req.mode === 'navigate' && url.pathname.startsWith('/books')) {
    e.respondWith(fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(BOOKS).then((c) => c.delete(req).then(() => c.put(req, copy)).then(() => c.keys())
          .then((keys) => Promise.all(keys.slice(0, Math.max(0, keys.length - BOOKS_MAX)).map((k) => c.delete(k)))));
      }
      return res;
    }).catch(() => caches.open(BOOKS).then((c) => c.match(req)).then((hit) => hit || caches.match('/offline'))));
    return;
  }
  if (req.mode === 'navigate') {
    // Pages are personal (progress, attempts) — don't store them, just fall back offline.
    e.respondWith(fetch(req).catch(() => caches.match('/offline')));
    return;
  }
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(caches.match(req).then((hit) => {
      const net = fetch(req).then((res) => {
        if (res.ok) caches.open(VERSION).then((c) => c.put(req, res.clone()));
        return res;
      });
      return hit || net;
    }));
  }
});
