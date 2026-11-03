// Real service-worker cache policy on a disposable local HTTP origin.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const worker = readFileSync(fileURLToPath(new URL('../../app/static/sw.js', import.meta.url)), 'utf8').replaceAll('__ASSET_V__', 'a1');
const visits = new Map(); let held, removed = false;
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/sw.js') { res.setHeader('Content-Type', 'text/javascript'); res.end(worker); return; }
  const key = url.pathname + url.search, count = (visits.get(key) || 0) + 1; visits.set(key, count);
  const send = () => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (removed && url.pathname === '/questions/7') res.statusCode = 404;
    else if (url.pathname.startsWith('/questions') && url.pathname !== '/questions/999') res.setHeader('X-SS-Public-Content', 'questions-v1');
    res.end('<h1>' + (url.pathname === '/offline' ? 'Offline' : key + ':' + count) + '</h1>');
  };
  if (url.searchParams.has('hold')) held = send; else send();
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const B = 'http://127.0.0.1:' + server.address().port;
const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
try {
  const context = await browser.newContext(), p = await context.newPage();
  await p.goto(B + '/');
  await p.evaluate(async () => { await navigator.serviceWorker.register('/sw.js'); await navigator.serviceWorker.ready; });
  await p.waitForFunction(() => !!navigator.serviceWorker.controller);
  async function message(type) {
    return p.evaluate(type => new Promise(resolve => { const channel = new MessageChannel(); channel.port1.onmessage = e => resolve(e.data); navigator.serviceWorker.controller.postMessage({ type }, [channel.port2]); }), type);
  }
  await p.goto(B + '/questions/1?lang=hi'); await message('SS_CONTENT_CACHE_STATUS');
  await p.goto(B + '/questions/1?lang=hi'); assert.equal(await p.locator('h1').textContent(), '/questions/1?lang=hi:2');
  await p.goto(B + '/questions/1?lang=en'); await message('SS_CONTENT_CACHE_STATUS');
  await context.setOffline(true);
  await p.goto(B + '/questions/1?lang=hi'); assert.equal(await p.locator('h1').textContent(), '/questions/1?lang=hi:2');
  await p.goto(B + '/questions/1?lang=en'); assert.equal(await p.locator('h1').textContent(), '/questions/1?lang=en:1');
  await context.setOffline(false);
  await p.goto(B + '/questions/7?lang=hi'); await message('SS_CONTENT_CACHE_STATUS'); removed = true;
  assert.equal((await p.goto(B + '/questions/7?lang=hi')).status(), 404); await message('SS_CONTENT_CACHE_STATUS');
  await context.setOffline(true); await p.goto(B + '/questions/7?lang=hi'); assert.equal(await p.locator('h1').textContent(), 'Offline');
  await context.setOffline(false);
  await p.goto(B + '/questions/999?lang=hi'); // no public-content marker
  await p.goto(B + '/questions/2'); // language not explicit
  for (const path of ['/progress', '/attempt/1', '/jobs']) await p.goto(B + path);
  await p.evaluate(() => fetch('/api/v1/stats'));
  const excluded = await p.evaluate(async () => (await (await caches.open('ss2-questions-v1')).keys()).map(r => new URL(r.url).pathname + new URL(r.url).search));
  assert.equal(excluded.some(u => /999|questions\/2|progress|attempt|jobs/.test(u)), false);
  assert.equal(await p.evaluate(async () => (await Promise.all((await caches.keys()).map(async name => (await (await caches.open(name)).keys()).map(r => r.url)))).flat().some(url => url.includes('/api/'))), false);
  for (let i = 0; i < 32; i++) await p.goto(B + '/questions?page=' + i + '&lang=hi');
  assert.equal((await message('SS_CONTENT_CACHE_STATUS')).questions, 30);
  await p.evaluate(async () => {
    const c = await caches.open('ss2-questions-v1'), req = (await c.keys())[0], response = await c.match(req);
    const headers = new Headers(response.headers); headers.set('X-SS-Cached-Asset', 'old-assets');
    await c.put(req, new Response(await response.arrayBuffer(), { headers })); window.oldAssetUrl = req.url;
  });
  const oldAssetUrl = await p.evaluate(() => window.oldAssetUrl);
  await context.setOffline(true); await p.goto(oldAssetUrl); assert.equal(await p.locator('h1').textContent(), 'Offline');
  await context.setOffline(false);
  await p.evaluate(async () => {
    const c = await caches.open('ss2-questions-v1'), req = (await c.keys()).at(-1), response = await c.match(req);
    const headers = new Headers(response.headers); headers.set('X-SS-Cached-At', String(Date.now() - 86400001));
    await c.put(req, new Response(await response.arrayBuffer(), { headers })); window.expiredUrl = req.url;
  });
  const expired = await p.evaluate(() => window.expiredUrl);
  await context.setOffline(true); await p.goto(expired); assert.equal(await p.locator('h1').textContent(), 'Offline');
  await context.setOffline(false);
  await p.goto(B + '/books/test'); await message('SS_CONTENT_CACHE_STATUS');
  await p.evaluate(() => { localStorage.setItem('ss_theme', 'paper'); localStorage.setItem('ss_read_chapters', '["keep"]'); localStorage.setItem('ss_whiteboards_v1', '{"keep":true}'); });
  await p.evaluate(() => { window.heldFetch = fetch('/questions/20?lang=hi&hold=1', { headers: { 'X-SS-Nav': '1' } }); });
  for (let i = 0; !held && i < 50; i++) await new Promise(resolve => setTimeout(resolve, 10));
  assert.ok(held);
  assert.deepEqual(await message('SS_CLEAR_CONTENT_CACHE'), { ok: true, books: 0, questions: 0 });
  held(); await p.evaluate(() => window.heldFetch.then(r => r.text()));
  const cleared = await message('SS_CONTENT_CACHE_STATUS'); assert.equal(cleared.books, 0); assert.equal(cleared.questions, 0);
  const kept = await p.evaluate(async () => ({ assets: (await (await caches.open('ss2-a1')).keys()).length, theme: localStorage.ss_theme, reading: localStorage.ss_read_chapters, rough: localStorage.ss_whiteboards_v1 }));
  assert.ok(kept.assets > 0); assert.equal(kept.theme, 'paper'); assert.equal(kept.reading, '["keep"]'); assert.equal(kept.rough, '{"keep":true}');
  console.log('Actual SW public-marker/language isolation, network-first/offline,30-page cap,24h expiry and content-only clear/in-flight race passed.');
} finally { await browser.close(); server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
