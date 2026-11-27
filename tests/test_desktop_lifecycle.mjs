import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup() {
  const frames = [], requests = [];
  let release;
  function element() {
    return {
      isConnected: true, style: {}, navigations: [],
      setAttribute() {},
      append(node) { node.parentElement = this; },
      moveBefore(node) { this.append(node); },
      set src(value) { this.url = value; this.navigations.push(value); },
      get src() { return this.url; },
    };
  }
  const parking = element();
  const source = readFileSync(new URL('../plugins/_desktop/webui/desktop-store.js', import.meta.url), 'utf8')
    .replace(/^import.*\n/gm, '').replace('export const store', 'const store');
  const store = vm.runInNewContext(`${source}\nstore`, {
    createStore: (_, model) => model,
    callJsonApi: (...args) => {
      requests.push(args);
      return new Promise(resolve => { release = () => resolve({ ok: true, url: '/desktop/tuxee/' }); });
    },
    document: {
      body: element(), getElementById: () => parking,
      createElement: tag => { const node = element(); if (tag === 'iframe') frames.push(node); return node; },
    },
  });
  const panel = () => { const host = element(); return { host, querySelector: () => host }; };
  return { store, frames, requests, panel, release: () => release(), parking };
}

test('fresh open logs in once; hiding a tab or canvas reloads only on reopening', async () => {
  const t = setup(), canvas = t.panel();
  await t.store.onMount(canvas);
  const opening = t.store.onOpen(); t.release(); await opening;
  const frame = t.frames[0];
  assert.equal(frame.src, '/desktop/tuxee/?a0_open=1');
  assert.equal(t.store.loading, true);
  assert.equal(frame.style.visibility, 'hidden');
  frame.onload();
  assert.equal(t.store.loading, false);
  await t.store.onOpen();
  assert.equal(frame.navigations.length, 1); // Manual logout stays visible while open.
  for (let i = 2; i <= 4; i++) {
    t.store.setDesktopHostVisible(false);
    assert.equal(frame.parentElement, t.parking);
    assert.equal(frame.navigations.length, i - 1);
    t.store.setDesktopHostVisible(true);
    await t.store.onOpen();
    assert.equal(frame.parentElement, canvas.host);
    assert.equal(frame.navigations.length, i);
    assert.equal(t.store.loading, true);
    assert.equal(frame.style.visibility, 'hidden');
    frame.onload();
    assert.equal(t.store.loading, false);
    assert.equal(frame.style.visibility, '');
  }
  assert.equal(t.requests.length, 1);
  assert.equal(t.frames.length, 1);
});

test('modal close and reopen reloads, but docking preserves the running document', async () => {
  const t = setup(), modal = t.panel(), canvas = t.panel();
  await t.store.onMount(canvas);
  const opening = t.store.onMount(modal, { mode: 'modal' }); t.release(); await opening;
  const frame = t.frames[0];
  t.store.cleanup(modal); modal.host.isConnected = false;
  const reopened = t.panel();
  await t.store.onMount(reopened, { mode: 'modal' });
  assert.equal(frame.navigations.length, 2);
  t.store.beforeDesktopHostHandoff();
  t.store.cleanup(reopened); reopened.host.isConnected = false;
  t.store.setDesktopHostVisible(false);
  await t.store.onMount(canvas); await t.store.onOpen();
  t.store.afterDesktopHostShown();
  assert.equal(frame.parentElement, canvas.host);
  assert.equal(frame.navigations.length, 2);
  t.store.beforeDesktopHostHandoff(); t.store.cancelDesktopHostHandoff();
  assert.equal(frame.parentElement, canvas.host);
  assert.equal(frame.navigations.length, 2);
});

test('closing during startup parks the result and reopening reloads it without duplicate startup', async () => {
  const t = setup(), canvas = t.panel();
  await t.store.onMount(canvas);
  const first = t.store.onOpen(), second = t.store.onOpen();
  t.store.setDesktopHostVisible(false);
  t.store.cleanup(canvas); canvas.host.isConnected = false;
  t.release(); await Promise.all([first, second]);
  assert.equal(t.frames[0].parentElement, t.parking);
  const next = t.panel(); await t.store.onMount(next); await t.store.onOpen();
  assert.equal(t.frames[0].navigations.length, 2);
  assert.equal(t.requests.length, 1);
});
