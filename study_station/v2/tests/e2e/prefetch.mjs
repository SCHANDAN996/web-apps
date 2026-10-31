// Exercise the real router with a controlled clock and transport (no server writes).
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
const p = await browser.newPage({ viewport: { width: 360, height: 800 } }), errors = [];
p.on('pageerror', e => errors.push(e.message));
await p.route('https://prefetch.test/**', route => route.fulfill({ contentType: 'text/html', body: '<html lang="hi"><head><link rel="stylesheet" href="/static/css/app.css?v=abcd"></head><body><main id="main"></main><script id="ss-boot" type="application/json">{"lang":"hi","t":{"offline":"offline"}}</script></body></html>' }));
await p.goto('https://prefetch.test/');
await p.evaluate(() => {
  window.SSTheme = { current: () => 'light' };
  window.now = 1000; Date.now = () => window.now;
  window.counts = {}; window.active = 0; window.maxActive = 0; window.aborted = [];
  window.pending = {}; window.version = 1;
  window.html = path => '<html lang="hi"><head><link rel="stylesheet" href="/static/css/app.css?v=abcd"></head><body><main id="main"><h1>' + path + ':' + window.version + '</h1></main><script id="ss-boot" type="application/json">{"lang":"hi","t":{"offline":"offline"}}</script></body></html>';
  window.fetch = (url, opts = {}) => {
    const path = new URL(url, location.href).pathname;
    window.counts[path] = (window.counts[path] || 0) + 1;
    if (path === '/api/v1/pending') return new Promise(resolve => { window.completeWrite = () => { window.version++; resolve(new Response('{}')); }; });
    if (path.startsWith('/api/')) { window.version++; return Promise.resolve(new Response('{}', { headers: { 'Content-Type': 'application/json' } })); }
    if (path === '/books/fail' && window.counts[path] === 1) return Promise.reject(new Error('network failure'));
    if (path.startsWith('/books/hold-') || path === '/books/slow') {
      window.active++; window.maxActive = Math.max(window.maxActive, window.active);
      return new Promise((resolve, reject) => {
        let done = false;
        const finish = fn => { if (done) return; done = true; window.active--; fn(); };
        window.pending[path] = () => finish(() => resolve(new Response(window.html(path))));
        opts.signal?.addEventListener('abort', () => finish(() => { window.aborted.push(path); reject(new DOMException('Aborted', 'AbortError')); }));
      });
    }
    return Promise.resolve(new Response(window.html(path)));
  };
});
await p.addScriptTag({ content: readFileSync(fileURLToPath(new URL('../../app/static/js/app.js', import.meta.url)), 'utf8') });
async function touch(path) {
  await p.evaluate(path => {
    let link = document.querySelector('a[data-test-path="' + path + '"]');
    if (!link) { link = document.createElement('a'); link.href = path; link.dataset.testPath = path; link.textContent = path; document.querySelector('main').append(link); }
    link.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
  }, path);
  await p.waitForTimeout(10);
}
async function count(path) { return p.evaluate(path => window.counts[path] || 0, path); }
await touch('/books/repeat'); await touch('/books/repeat'); assert.equal(await count('/books/repeat'), 1);
await p.evaluate(() => { window.now += 5001; });
await touch('/books/repeat'); assert.equal(await count('/books/repeat'), 2, 'Expired entries must prefetch again.');
await p.evaluate(() => SS.go('/books/repeat')); assert.equal(await count('/books/repeat'), 2, 'A fresh prefetch is consumed without another fetch.');
await touch('/books/fail'); await touch('/books/fail'); assert.equal(await count('/books/fail'), 2, 'Failed prefetches must be immediately retryable.');
for (let i = 0; i < 9; i++) { await p.evaluate(() => { window.now++; }); await touch('/books/hold-' + i); }
assert.ok(await p.evaluate(() => window.maxActive <= 6), 'Speculative requests must stay bounded.');
assert.ok(await p.evaluate(() => window.aborted.includes('/books/hold-0')), 'Oldest speculative request should be aborted.');
await p.evaluate(() => SS.go('/jobs')); assert.equal(await p.evaluate(() => window.active), 0, 'Navigation cancels prefetches belonging to the previous page.');
await touch('/progress'); await p.evaluate(() => SS.api('POST', '/api/v1/test', {}));
await p.evaluate(() => SS.go('/progress')); assert.equal(await count('/progress'), 2, 'A successful write must not reuse a stale prefetched screen.');
assert.equal(await p.locator('h1').textContent(), '/progress:2');
await p.evaluate(() => { window.write = SS.api('POST', '/api/v1/pending', {}); });
await touch('/books/after-write');
await p.evaluate(async () => { window.completeWrite(); await window.write; });
await p.evaluate(() => SS.go('/books/after-write'));
assert.equal(await count('/books/after-write'), 2, 'Prefetches started during a write must be invalidated when it completes.');
assert.equal(await p.locator('h1').textContent(), '/books/after-write:3');
await touch('/books/hold-hidden'); await p.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pagehide')));
assert.equal(await p.evaluate(() => window.active), 0);
await p.evaluate(() => { window.oldNavigation = SS.go('/books/slow'); });
await p.evaluate(() => SS.go('/practice/fast'));
await p.evaluate(async () => { window.pending['/books/slow'](); await window.oldNavigation; });
assert.equal(await p.locator('h1').textContent(), '/practice/fast:3', 'A late earlier navigation must not replace the current screen.');
assert.deepEqual(errors, []);
console.log('Prefetch expiry, deduplication, retries, bounded cancellation, mutation invalidation and navigation ordering passed.');
await browser.close();
