import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import test from 'node:test';

const source = readFileSync(new URL('../app/static/js/theme.js', import.meta.url), 'utf8');
function boot(saved, blocked = false) {
  const stored = new Map(saved ? [['ss_theme', saved]] : []);
  const attrs = new Map();
  const metas = [{}, {}].map(() => ({ attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; } }));
  const window = {};
  const document = { documentElement: { setAttribute(k, v) { attrs.set(k, v); }, removeAttribute(k) { attrs.delete(k); }, classList: { add() {} } }, querySelectorAll() { return metas; } };
  const localStorage = { getItem(k) { if (blocked) throw Error(); return stored.get(k); }, setItem(k, v) { if (blocked) throw Error(); stored.set(k, v); }, removeItem(k) { if (blocked) throw Error(); stored.delete(k); } };
  vm.runInNewContext(source, { window, document, localStorage, navigator: { userAgent: '' } });
  return { theme: window.SSTheme, stored, attrs, metas };
}
test('paper restores before paint and updates browser bars', () => {
  const state = boot('paper');
  assert.equal(state.attrs.get('data-theme'), 'paper');
  assert.ok(state.metas.every(m => m.attrs.content === '#FBF6EC' && !m.attrs.media));
});
test('theme changes persist and system restores media-specific bars', () => {
  const state = boot('light');
  state.theme.set('dark');
  assert.equal(state.stored.get('ss_theme'), 'dark');
  assert.equal(state.attrs.get('data-theme'), 'dark');
  state.theme.set('system');
  assert.equal(state.attrs.has('data-theme'), false);
  assert.equal(state.stored.has('ss_theme'), false);
  assert.equal(state.metas[0].attrs.media, '(prefers-color-scheme: light)');
  assert.equal(state.metas[1].attrs.media, '(prefers-color-scheme: dark)');
});
test('blocked storage still permits a theme change for this session', () => {
  const state = boot(null, true);
  state.theme.set('paper');
  assert.equal(state.theme.current(), 'paper');
  assert.equal(state.attrs.get('data-theme'), 'paper');
});
