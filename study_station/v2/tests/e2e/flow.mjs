// End-to-end check in a real (mobile) browser. Used by the QA agent and before deploys.
//   BASE_URL=http://localhost:8000 node tests/e2e/flow.mjs
// Needs: npm i -D playwright (or a global install). Screenshots → tests/e2e/shots/
import { mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright'); }
const { chromium, devices } = pw;

const B = (process.env.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const OUT = new URL('./shots/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const results = [];
const step = async (name, fn) => {
  try { await fn(); results.push({ step: name, ok: true }); }
  catch (e) { results.push({ step: name, ok: false, error: String(e).slice(0, 300) }); }
};

const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices['Pixel 7'] });
const p = await ctx.newPage();
const errors = [];
p.on('pageerror', e => errors.push(e.message));
p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
const shot = async n => { await p.waitForTimeout(500); await p.screenshot({ path: OUT + n + '.png' }); };

await step('onboarding', async () => {
  await p.goto(B + '/');
  await p.click('label.chip:has-text("10")');
  await p.click('label.chip[data-level="10th"] >> nth=0');
  await p.click('#onboard button[type=submit]');
  await p.waitForURL(B + '/');
  await shot('home');
});

await step('practice 10 questions', async () => {
  await p.goto(B + '/practice');
  await p.click('.list-item >> nth=0');
  await p.click('#practiceForm button[type=submit]');
  await p.waitForURL(/\/attempt\/\d+/);
  for (let i = 0; i < 10; i++) {
    await p.waitForSelector('.option:not([disabled])');
    await p.click('.option >> nth=' + (i % 4));
    await p.click('.action-bar .btn-primary');
    await p.waitForSelector('.feedback');
    if (i === 0) await shot('practice-feedback');
    await p.click('.action-bar .btn-primary');
  }
  await p.waitForURL(/\/result\/\d+/);
  await shot('practice-result');
});

await step('mock test with palette and submit', async () => {
  await p.goto(B + '/mock');
  await p.click('.card-link >> nth=0');
  await p.click('[data-mock]');
  await p.waitForURL(/\/attempt\/\d+/);
  await p.waitForSelector('.option');
  for (let i = 0; i < 5; i++) { await p.click('.option >> nth=1'); await p.click('.action-bar .btn-primary'); await p.waitForTimeout(100); }
  await p.click('button[aria-label="Question palette"]');
  await p.waitForSelector('dialog .pal');
  await shot('mock-palette');
  await p.click('dialog .dlg-foot .btn-primary');
  await p.click('dialog button[value=yes]');
  await p.waitForURL(/\/result\/\d+/);
  await shot('mock-result');
});

for (const [name, path] of [['revise', '/revise'], ['progress', '/progress'], ['jobs', '/jobs?qualification=all'],
                            ['current affairs', '/current-affairs'], ['settings', '/settings']]) {
  await step('page ' + name, async () => {
    const r = await p.goto(B + path);
    if (!r || r.status() !== 200) throw new Error('HTTP ' + (r && r.status()));
    await shot(name.replace(' ', '-'));
  });
}

await step('language switch', async () => {
  await p.goto(B + '/');
  await p.click('#langBtn');
  await p.waitForTimeout(600);
  const h = await p.textContent('h1');
  if (!/Hello|नमस्ते/.test(h)) throw new Error('unexpected heading ' + h);
});

await step('books: chapter, flashcard flip, mind map', async () => {
  await p.goto(B + '/books');
  await shot('books');
  await p.click('main .card-link >> nth=0');
  await p.waitForURL(/\/books\/[^/]+$/);
  await p.click('.chapter-list a.list-item >> nth=0');
  await p.waitForSelector('.book-body');
  await shot('book-chapter');
  const fc = p.locator('.book-tabs .chip', { hasText: /फ़्लैशकार्ड|Flashcards/ });
  if (await fc.count()) {
    await fc.first().click();
    await p.waitForSelector('.fc');
    await p.click('.fc >> nth=0');
    if (await p.getAttribute('.fc >> nth=0', 'aria-expanded') !== 'true') throw new Error('flashcard did not flip');
    await shot('book-flashcards');
  }
  const mm = p.locator('.book-tabs .chip', { hasText: /माइंड मैप|Mind map/ });
  if (await mm.count()) { await mm.first().click(); await p.waitForSelector('.mm-tree'); await shot('book-mindmap'); }
});

await step('no horizontal scroll on phone', async () => {
  for (const path of ['/', '/practice', '/jobs', '/current-affairs', '/books']) {
    await p.goto(B + path);
    const over = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (over > 1) throw new Error(path + ' overflows by ' + over + 'px');
  }
});

await browser.close();
const failed = results.filter(r => !r.ok);
console.log(JSON.stringify({ base: B, results, js_errors: errors }, null, 1));
process.exit(failed.length || errors.length ? 1 : 0);
