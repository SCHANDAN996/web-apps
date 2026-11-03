// Destructive only to a new disposable learner on a local seeded QA server.
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const B = process.env.BASE_URL || 'http://127.0.0.1:8011';
if (!/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(B)) throw new Error('Use a local scratch server.');
const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
const context = await browser.newContext({ viewport: { width: 360, height: 800 } });
const p = await context.newPage(), errors = [];
p.on('pageerror', e => errors.push(e.message));
await p.goto(B + '/');
async function post(path, data) { const r = await p.request.post(B + path, { data }); assert.equal(r.ok(), true, path + ' ' + r.status() + ' ' + await r.text()); return r.json(); }
async function progress() { const r = await p.request.get(B + '/api/v1/backup/export'); assert.equal(r.ok(), true); return r.json(); }
await post('/api/v1/me', { lang: 'hi', level: '10th', target_exams: [] });
const catalog = await (await p.request.get(B + '/api/v1/catalog')).json();
const optionsResponse = await p.request.get(B + '/api/v1/me/reset-options'); assert.equal(optionsResponse.ok(), true);
const options = await optionsResponse.json();
function topic(c) { return catalog.subjects.find(s => s.slug === c.subject)?.topics.find(t => t.name.en === c.topic_label_en && t.questions > 0); }
const a = options.chapters.find(c => c.subject === 'quant' && topic(c));
const b = options.chapters.find(c => c.subject !== a.subject && topic(c));
const sibling = options.chapters.find(c => c.subject === a.subject && c.url !== a.url);
assert.ok(a && b && sibling, 'Seeded books with distinct scopes are required.');
async function attempt(t) {
  const value = await post('/api/v1/practice', { topic_id: t.id, count: 1 });
  await post('/api/v1/attempts/' + value.id + '/answer', { question_id: value.questions[0].id, chosen_index: 0, time_ms: 500 });
  await post('/api/v1/attempts/' + value.id + '/finish', {}); return value;
}
const aa = await attempt(topic(a)), bb = await attempt(topic(b));
const mock = await post('/api/v1/mock', { exam: catalog.exams[0].slug });
await post('/api/v1/attempts/' + mock.id + '/finish', {});
await p.goto(B + '/settings');
await p.waitForFunction(() => document.querySelectorAll('#resetBook option').length > 1);
await p.evaluate(({ a, b, sibling, qa, qb }) => {
  localStorage.setItem('ss_read_chapters', JSON.stringify([a.url, b.url, sibling.url]));
  localStorage.setItem('ss_last_chapter', JSON.stringify({ url: b.url, hi: b.title_hi, en: b.title_en }));
  const board = { strokes: [{ tool: 'pen', color: 'black', points: [[0.1, 0.1]] }], updated: Date.now() };
  SSWhiteboard.merge({ [qa]: board, [qb]: board }); SSTheme.set('paper');
}, { a, b, sibling, qa: aa.questions[0].id, qb: bb.questions[0].id });
await p.selectOption('#resetScope', 'chapter'); await p.selectOption('#resetBook', a.book); await p.selectOption('#resetChapter', a.chapter);
const before = await progress();
// Portable backup identifiers deliberately differ from the player's database row IDs.
const preservedPractice = before.attempts.find(x => x.mode === 'practice' && x.question_ids.includes(bb.questions[0].id)).id;
const preservedMock = before.attempts.find(x => x.mode === 'mock').id;
await p.click('#resetProgress');
assert.match(await p.locator('#resetWarning').textContent(), /मॉक/);
await p.locator('dialog .btn-secondary').click();
assert.deepEqual(await progress(), before);
await p.click('#resetProgress');
await p.waitForTimeout(500); // Let the Material dialog entry animation finish before visual QA.
const dialogBounds = await p.locator('dialog').boundingBox();
const confirmBounds = await p.locator('dialog .btn-primary').boundingBox();
assert.ok(dialogBounds.y >= 0 && dialogBounds.y + dialogBounds.height <= 800, 'Confirmation fits the phone viewport.');
assert.ok(confirmBounds.y >= 0 && confirmBounds.y + confirmBounds.height <= 800, 'Confirmation button stays visible.');
if (process.env.QA_SCREENSHOT_DIR) await p.screenshot({ path: process.env.QA_SCREENSHOT_DIR + '/reset-chapter-confirm-hi-viewport.png' });
if (process.env.QA_CONFIRM_ONLY) { await browser.close(); process.exit(0); }
await p.locator('dialog .btn-primary').click();
await p.waitForFunction(() => !document.querySelector('dialog'));
await p.waitForFunction(() => document.querySelector('#resetScope')?.value === 'all' && document.querySelectorAll('#resetBook option').length > 1);
let state = await progress();
assert.deepEqual(state.attempts.map(a => a.id).sort((a,b) => a-b), [preservedPractice, preservedMock].sort((a,b) => a-b));
let local = await p.evaluate(() => ({ read: JSON.parse(localStorage.ss_read_chapters), rough: SSWhiteboard.export(), last: JSON.parse(localStorage.ss_last_chapter), theme: SSTheme.current() }));
assert.equal(local.read.includes(a.url), false); assert.equal(local.read.includes(sibling.url), true); assert.equal(local.read.includes(b.url), true);
assert.equal(local.rough[aa.questions[0].id], undefined); assert.ok(local.rough[bb.questions[0].id]); assert.equal(local.last.url, b.url); assert.equal(local.theme, 'paper');
await p.selectOption('#resetScope', 'subject'); await p.selectOption('#resetSubject', b.subject);
await p.click('#resetProgress'); await p.locator('dialog .btn-primary').click();
await p.waitForFunction(() => !document.querySelector('dialog'));
await p.waitForFunction(() => document.querySelector('#resetScope')?.value === 'all' && document.querySelectorAll('#resetBook option').length > 1);
state = await progress(); assert.deepEqual(state.attempts.map(a => a.id), [preservedMock]);
local = await p.evaluate(() => ({ read: JSON.parse(localStorage.ss_read_chapters), rough: SSWhiteboard.export(), last: localStorage.ss_last_chapter }));
assert.deepEqual(local.read, [sibling.url]); assert.deepEqual(local.rough, {}); assert.equal(local.last, undefined);
await p.selectOption('#resetScope', 'all'); await p.click('#resetProgress'); await p.locator('dialog .btn-primary').click();
await p.waitForURL(B + '/');
state = await progress(); assert.deepEqual(state.attempts, []);
assert.equal(await p.evaluate(() => localStorage.getItem('ss_read_chapters')), null);
assert.equal(await p.evaluate(() => SSTheme.current()), 'paper');
assert.deepEqual(errors, []);
console.log('Chapter cancel/confirm, subject isolation, mock preservation, exact local cleanup and all reset passed.');
await browser.close();
