// Focused browser checks: local drawing persistence and safe restore boundaries.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const root = fileURLToPath(new URL('../../app/', import.meta.url));
const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 360, height: 800 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.route('https://test.invalid/**', route => route.fulfill({ contentType: 'text/html', body: '<main></main>' }));
await page.goto('https://test.invalid/');
await page.addStyleTag({ content: readFileSync(root + '/static/css/app.css', 'utf8') });
await page.evaluate(() => {
  const t = new Proxy({}, { get: (_o, k) => String(k) });
  window.calls = []; window.leaves = [];
  window.SS = { t, h(tag, attrs, ...children) {
    const e = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => k.startsWith('on') ? e.addEventListener(k.slice(2), v) : e.setAttribute(k, v === true ? '' : v));
    children.flat().forEach(c => c != null && e.append(c)); return e;
  }, icon: () => document.createElement('span'), onLeave(fn) { window.leaves.push(fn); }, toast() {}, go() {},
  api: async (method, url, data) => { window.calls.push({ method, url, data }); return { schema_version: 1 }; } };
  window.SSTheme = { set() {} };
});
await page.addScriptTag({ content: readFileSync(root + '/static/js/whiteboard.js', 'utf8') });
await page.evaluate(() => document.querySelector('main').append(window.SSWhiteboard.create(12)));
await page.locator('.rough-toggle').click();
const area = await page.locator('canvas').boundingBox();
await page.mouse.move(area.x + 20, area.y + 20); await page.mouse.down();
await page.mouse.move(area.x + 90, area.y + 70, { steps: 8 }); await page.mouse.up();
assert.equal(await page.evaluate(() => SSWhiteboard.export()['12'].strokes.length), 1);
assert.equal(await page.evaluate(() => JSON.parse(localStorage.ss_whiteboards_v1)['12'].strokes.length), 1);
for (const theme of ['light', 'dark']) {
  await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
  assert.equal(await page.locator('.rough-toggle').evaluate(e => e.getBoundingClientRect().height >= 44), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  if (process.env.QA_SCREENSHOT_DIR) await page.screenshot({ path: process.env.QA_SCREENSHOT_DIR + '/rough-work-' + theme + '.png', fullPage: true });
}
await page.getByText('rough_undo', { exact: true }).click();
assert.equal(await page.evaluate(() => SSWhiteboard.export()['12'].strokes.length), 0);
assert.equal(await page.evaluate(() => { try { SSWhiteboard.validate({ 12: { strokes: [{ tool: 'pen', color: 'black', points: [[2, 0]] }] } }); return false; } catch { return true; } }), true);
await page.evaluate(() => {
  document.querySelector('main').innerHTML = '<section id="backup"><button data-backup-action="local-backup">save</button><button data-backup-action="local-restore">load</button><button data-backup-action="backup" data-drive-action disabled>drive</button><input id="backupFile" type="file"><p id="driveSetupStatus"></p><p id="backupStatus"></p></section>';
  window.StudyStationNative = { driveConfigured: () => false, requestLocalBackup: () => window.dispatchEvent(new CustomEvent('ss-drive-result', { detail: { operation: 'local-backup', ok: true } })), requestLocalRestore: () => window.dispatchEvent(new CustomEvent('ss-drive-result', { detail: { operation: 'local-restore', ok: true, data: { format: 'study-station-backup', version: 1, progress: { schema_version: 1 }, local: {} } } })) };
});
await page.addScriptTag({ content: readFileSync(root + '/static/js/backup.js', 'utf8') });
assert.equal(await page.locator('[data-drive-action]').isDisabled(), true);
await page.getByText('save', { exact: true }).click();
await page.waitForFunction(() => document.querySelector('#backupStatus').textContent === 'backup_saved');
assert.equal(await page.locator('[data-drive-action]').isDisabled(), true);
await page.getByText('load', { exact: true }).click();
await page.locator('dialog').getByText('cancel', { exact: true }).click();
assert.equal(await page.evaluate(() => calls.filter(c => c.method === 'POST').length), 0);
await page.getByText('load', { exact: true }).click();
await page.locator('dialog').getByText('backup_restore', { exact: true }).last().click();
await page.waitForFunction(() => calls.some(c => c.method === 'POST'));
assert.deepEqual(await page.evaluate(() => calls.find(c => c.method === 'POST').data), { confirm: true, backup: { schema_version: 1 } });
assert.equal(await page.evaluate(() => { try { SSBackup.validate({ format: 'study-station-backup', version: 1, progress: { schema_version: 1 }, local: { lastChapter: { url: 'javascript:alert(1)', hi: '', en: '' } } }); return false; } catch { return true; } }), true);
await page.evaluate(() => {
  File.prototype.text = function () { return new Promise(resolve => { window.completeFile = resolve; }); };
});
await page.locator('#backupFile').setInputFiles({ name: 'slow.json', mimeType: 'application/json', buffer: Buffer.from('{}') });
await page.evaluate(() => {
  window.leaves.pop()();
  delete document.querySelector('#backup').dataset.wired;
  SSBackup.init();
  StudyStationNative.requestLocalBackup = () => {};
});
await page.getByText('save', { exact: true }).click();
await page.evaluate(() => window.completeFile(JSON.stringify({ format: 'study-station-backup', version: 1, progress: { schema_version: 1 }, local: {} })));
await page.waitForTimeout(50);
assert.equal(await page.locator('dialog').count(), 0, 'A stale file read must not open a restore dialog on a newer settings page.');
await page.evaluate(() => { window.leaves.pop()(); delete document.querySelector('#backup').dataset.wired; SSBackup.init(); });
await page.evaluate(() => {
  window.nativeCalls = 0;
  StudyStationNative.requestLocalBackup = () => { window.nativeCalls++; };
  SS.api = () => new Promise(resolve => { window.completeExport = resolve; });
});
await page.getByText('save', { exact: true }).click();
await page.evaluate(() => { window.leaves.pop()(); window.completeExport({ schema_version: 1 }); });
await page.waitForTimeout(50);
assert.equal(await page.locator('[data-backup-action="local-backup"]').isDisabled(), false);
assert.equal(await page.evaluate(() => window.nativeCalls), 0);
assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
assert.deepEqual(errors, []);
console.log('Whiteboard and backup browser checks passed.');
await browser.close();
