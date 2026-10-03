/**
 * Study Station — Service Worker
 * Offline-first for the app shell; network-first for HTML pages and data.
 * Bump CACHE_VERSION whenever the shell assets change.
 */
const CACHE_VERSION = 'ss-v1';
const SHELL_CACHE = CACHE_VERSION + '-shell';
const RUNTIME_CACHE = CACHE_VERSION + '-runtime';

// Core app shell — cached on install so the site opens offline.
const SHELL_ASSETS = [
  '/index.html',
  '/css/style.css',
  '/css/components.css',
  '/css/animations.css',
  '/js/data.js',
  '/js/jobs_data.js',
  '/js/book-reader.js',
  '/js/app.js',
  '/js/pages.js',
  '/js/theme.js',
  '/js/nav.js',
  '/manifest.webmanifest',
  '/assets/icon.svg'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(SHELL_CACHE).then(function (cache) {
      // addAll fails the whole install if any file 404s — cache individually.
      return Promise.all(
        SHELL_ASSETS.map(function (url) {
          return cache.add(url).catch(function () { /* ignore missing */ });
        })
      );
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k.indexOf(CACHE_VERSION) !== 0; })
            .map(function (k) { return caches.delete(k); })
      );
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Only handle same-origin requests; let CDN/font requests pass through.
  if (url.origin !== self.location.origin) return;

  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').indexOf('text/html') !== -1;

  if (isHTML) {
    // Network-first for pages so jobs/books stay fresh; fall back to cache offline.
    event.respondWith(
      fetch(req).then(function (res) {
        const copy = res.clone();
        caches.open(RUNTIME_CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match('/index.html');
        });
      })
    );
    return;
  }

  // Stale-while-revalidate for static assets (css/js/json/chapter html fetched via XHR).
  event.respondWith(
    caches.match(req).then(function (hit) {
      const fetchPromise = fetch(req).then(function (res) {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(RUNTIME_CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return hit; });
      return hit || fetchPromise;
    })
  );
});
