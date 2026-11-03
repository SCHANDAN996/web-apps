/* Study Station v2 service worker: offline shell, network-first pages, never caches API data.
   Book pages (/books/…) are the same for everyone, so visited ones are kept for offline reading. */
const V = '__ASSET_V__';                 // stamped by the server (hash of the static files)
const VERSION = 'ss2-' + V;
const BOOKS = 'ss2-books-v1';
const QUESTIONS = 'ss2-questions-v1';
const BOOKS_MAX = 80;           // pages kept for offline reading (oldest dropped first)
const QUESTIONS_MAX = 30, QUESTIONS_TTL = 24 * 60 * 60 * 1000;
let contentEpoch = 0, contentWrites = Promise.resolve();
const SHELL = ['/static/css/app.css', '/static/js/app.js', '/static/js/theme.js', '/static/js/player.js', '/static/js/whiteboard.js', '/static/js/backup.js', '/static/js/reset.js', '/static/brand-mark.webp', '/static/favicon.png', '/static/icon-192.png', '/static/icon-512.png']
  .map((u) => u + '?v=' + V).concat(['/offline']);

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION && k !== BOOKS && k !== QUESTIONS).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function contentTask(task) {
  const result = contentWrites.catch(() => {}).then(task);
  contentWrites = result.catch(() => {});
  return result;
}

function questionPath(url) { return /^\/questions(?:\/[1-9][0-9]*)?$/.test(url.pathname); }
function explicitLanguage(url) { return ['hi', 'en'].includes(url.searchParams.get('lang')); }
function freshQuestion(response) {
  const saved = Number(response && response.headers.get('X-SS-Cached-At'));
  const age = Date.now() - saved;
  return response && response.headers.get('X-SS-Public-Content') === 'questions-v1' &&
    response.headers.get('X-SS-Cached-Asset') === V && saved > 0 && age >= 0 && age < QUESTIONS_TTL;
}

async function trimQuestions(cache) {
  for (const key of await cache.keys()) {
    if (!freshQuestion(await cache.match(key))) await cache.delete(key);
  }
  const keys = await cache.keys();
  await Promise.all(keys.slice(0, Math.max(0, keys.length - QUESTIONS_MAX)).map((key) => cache.delete(key)));
}

self.addEventListener('message', (e) => {
  const type = e.data && e.data.type, port = e.ports && e.ports[0];
  if (!port || !['SS_CONTENT_CACHE_STATUS', 'SS_CLEAR_CONTENT_CACHE'].includes(type)) return;
  try { if (!e.source || new URL(e.source.url).origin !== location.origin) return; } catch (error) { return; }
  if (type === 'SS_CLEAR_CONTENT_CACHE') contentEpoch++;
  const work = contentTask(async () => {
    if (type === 'SS_CLEAR_CONTENT_CACHE') {
      await Promise.all([caches.delete(BOOKS), caches.delete(QUESTIONS)]);
      return { ok: true, books: 0, questions: 0 };
    }
    const books = await caches.open(BOOKS), questions = await caches.open(QUESTIONS);
    await trimQuestions(questions);
    return { ok: true, books: (await books.keys()).length, questions: (await questions.keys()).length };
  });
  e.waitUntil(work.then((data) => port.postMessage(data), () => port.postMessage({ ok: false })));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;
  // Screens changed inside the page (app.js fetches them with X-SS-Nav) are navigations too.
  const nav = req.mode === 'navigate' || req.headers.get('X-SS-Nav') === '1';

  if (nav && questionPath(url) && explicitLanguage(url)) {
    const epoch = contentEpoch;
    e.respondWith(fetch(req).then((res) => {
      const finalUrl = new URL(res.url || req.url);
      const allowed = res.ok && res.headers.get('X-SS-Public-Content') === 'questions-v1' &&
        finalUrl.origin === url.origin && finalUrl.pathname === url.pathname && finalUrl.searchParams.get('lang') === url.searchParams.get('lang');
      const copy = allowed ? res.clone() : null;
      e.waitUntil(contentTask(async () => {
        if (epoch !== contentEpoch) return;
        const cache = await caches.open(QUESTIONS);
        if (!copy) { await cache.delete(req); return; }
        const headers = new Headers(copy.headers);
        headers.set('X-SS-Cached-At', String(Date.now()));
        headers.set('X-SS-Cached-Asset', V);
        const stored = new Response(await copy.arrayBuffer(), { status: copy.status, statusText: copy.statusText, headers });
        if (epoch !== contentEpoch) return;
        await cache.delete(req); await cache.put(req, stored); await trimQuestions(cache);
      }).catch(() => {}));
      return res;
    }).catch(async () => {
      const cache = await caches.open(QUESTIONS), hit = await cache.match(req);
      if (freshQuestion(hit)) return hit;
      if (hit) await cache.delete(req);
      return caches.match('/offline');
    }));
    return;
  }

  if (nav && url.pathname.startsWith('/books')) {
    const epoch = contentEpoch;
    e.respondWith(fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        e.waitUntil(contentTask(async () => {
          if (epoch !== contentEpoch) return;
          const c = await caches.open(BOOKS);
          await c.delete(req); await c.put(req, copy);
          const keys = await c.keys();
          await Promise.all(keys.slice(0, Math.max(0, keys.length - BOOKS_MAX)).map((k) => c.delete(k)));
        }).catch(() => {}));
      }
      return res;
    }).catch(() => caches.open(BOOKS).then((c) => c.match(req)).then((hit) => hit || caches.match('/offline'))));
    return;
  }
  if (nav) {
    // Pages are personal (progress, attempts) — don't store them, just fall back offline.
    e.respondWith(fetch(req).catch(() => caches.match('/offline')));
    return;
  }
  if (url.pathname.startsWith('/static/')) {
    // Versioned assets never change: cache first, network only on a miss (saves data on every page).
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok && url.searchParams.get('v') === V) {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(req, copy));
      }
      return res;
    })));
  }
});
