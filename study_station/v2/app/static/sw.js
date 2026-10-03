/* Study Station v2 service worker: offline shell, network-first pages, never caches API data. */
const VERSION = 'ss2-v1';
const SHELL = ['/static/css/app.css', '/static/js/app.js', '/static/js/player.js', '/static/icon.svg', '/offline'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;

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
