import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup() {
  const stack = [], opens = [], moves = [];
  const storage = new Map();
  const parent = { moveBefore: node => { node.parentElement = parent; moves.push(parent); } };
  const shell = { parentElement: parent };
  let store;
  const source = readFileSync(new URL('../webui/components/canvas/right-canvas-store.js', import.meta.url), 'utf8')
    .replace(/^import\b[\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  const context = {
    createStore: (_, model) => model, console, setTimeout, clearTimeout,
    SURFACE_MODE_DOCKED: 'canvas', SURFACE_MODE_FLOATING: 'modal',
    normalizeSurfaceId: id => id, normalizeSurfaceMode: mode => mode === 'modal' ? mode : 'canvas',
    migratePersistedSurfaceState: saved => saved,
    getRegisteredSurfaces: () => [],
    preferencesStore: { isUiControlVisible: () => true },
    chatsStore: { selected: 'test' },
    Alpine: { mutateDom: fn => fn() },
    localStorage: { setItem() {}, getItem: () => null },
    sessionStorage: { setItem: (key, value) => storage.set(key, value), getItem: key => storage.get(key), removeItem: key => storage.delete(key) },
    performance: { getEntriesByType: () => [{ type: 'reload' }] },
    document: { documentElement: { clientWidth: 1440 } },
    openModal: (path, beforeClose) => new Promise(resolve => {
      const host = { moveBefore: node => { node.parentElement = host; moves.push(host); } };
      stack.push({ path, beforeClose, resolve, host });
      queueMicrotask(() => store.mountModal(host));
    }),
    closeModal: async path => {
      const i = stack.findIndex(modal => modal.path === path);
      if (i < 0) return;
      const modal = stack[i];
      if (await modal.beforeClose() === false) return false;
      stack.splice(i, 1);
      modal.resolve();
      return true;
    },
  };
  store = vm.runInNewContext(`${source}\nstore`, context);
  store.surfaces = ['files', 'browser', 'editor', 'desktop'].map(id => ({ id, open: payload => opens.push([id, payload]) }));
  store.applyLayoutState = () => {};
  store.mountShell(shell);
  return { store, stack, opens, moves, parent, shell, context, storage };
}

test('closed defaults ignore per-tab history; open tabs keep the current mode', async () => {
  const { store, stack } = setup();
  for (const id of ['files', 'browser', 'editor']) {
    store.recordSurfaceMode(id, 'modal');
    await store.openLatest(id);
    assert.equal(store.isOpen, true);
    assert.equal(stack.length, 0);
    await store.open('desktop');
    assert.equal(store.isDetached, false, 'Desktop stays attached while canvas is open');
    await store.close();
  }
  store.recordSurfaceMode('desktop', 'canvas');
  await store.open('desktop');
  assert.equal(store.isDetached, true);
  assert.equal(store.isOpen, false);
  for (const id of ['files', 'browser', 'editor', 'desktop']) {
    await store.openLatest(id);
    assert.equal(store.isDetached, true);
    assert.equal(stack.length, 1);
  }
  await store.close();
  assert.equal(stack.length, 0);
  assert.equal(store.isDetached, false);
  await store.open('files');
  assert.equal(store.isOpen, true);
});

test('detach/attach moves one shell, keeps every panel, and closes all tabs once', async () => {
  const { store, stack, shell, parent, opens, moves } = setup();
  await store.open('files');
  await Promise.all([store.undockActiveSurface(), store.undockActiveSurface()]);
  assert.equal(stack.length, 1, 'concurrent detaches share one modal');
  assert.equal(shell.parentElement, stack[0].host);
  for (const id of ['browser', 'editor', 'desktop', 'files', 'browser']) await store.open(id);
  assert.deepEqual(opens.map(([id]) => id), ['files', 'browser', 'editor', 'desktop']);
  const visibility = [];
  store.applyLayoutState = () => visibility.push(store.isSurfaceRendered('desktop'));
  await store.dockSurface();
  assert.equal(stack.length, 0);
  assert.equal(shell.parentElement, parent);
  assert.equal(store.isOpen, true);
  assert.equal(store.activeSurfaceId, 'browser');
  assert.equal(store.mountedSurfaceIds().length, 4);
  assert.equal(opens.length, 4, 'handoff does not reopen any panel');
  assert.ok(visibility.every(Boolean), 'reattach never signals a closed desktop host');
  await store.undockActiveSurface();
  await store.close();
  assert.equal(stack.length, 0);
  assert.equal(shell.parentElement, parent);
  assert.equal(store.isOpen, false);
  assert.equal(moves.length, 4);
});

test('tab requests during detach share the pending modal and keep the last selection', async () => {
  const { store, stack } = setup();
  await Promise.all([store.open('desktop'), store.open('files'), store.open('editor')]);
  assert.equal(stack.length, 1);
  assert.equal(store.isDetached, true);
  assert.equal(store.activeSurfaceId, 'editor');
});

test('reopening a closed workspace still runs its surface open hook', async () => {
  const { store, opens } = setup();
  await store.open('desktop');
  await store.dockSurface();
  assert.equal(opens.length, 1);
  await store.close();
  await store.open('desktop');
  assert.equal(opens.length, 2, 'Desktop can renew login after a real close');
});

test('explicit navigation reaches a retained panel and unavailable surfaces do not change mode', async () => {
  const { store, opens, stack } = setup();
  await store.open('editor', { path: '/draft.md' });
  await store.undockActiveSurface();
  await store.openLatest('editor', { path: '/other.md' });
  assert.deepEqual(opens.map(([, payload]) => payload.path), ['/draft.md', '/other.md']);
  assert.equal(await store.open('missing'), false);
  store.getSurface('files').canOpen = () => false;
  assert.equal(await store.open('files'), false);
  assert.equal(store.activeSurfaceId, 'editor');
  assert.equal(stack.length, 1);
});

test('mobile and welcome use the same modal; resize preserves mounted panels', async () => {
  const { store, context, stack } = setup();
  await store.open('files');
  context.document.documentElement.clientWidth = 390;
  store.updateLayoutMode();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(stack.length, 1);
  assert.equal(store.isSurfaceVisible('files'), true);
  assert.equal(await store.dockSurface(), false);
  await store.open('editor');
  assert.equal(stack.length, 1);
  await store.close();
  context.document.documentElement.clientWidth = 1440;
  store.updateLayoutMode();
  context.chatsStore.selected = null;
  await store.open('files');
  assert.equal(store.isDetached, true);
});

test('session reload restores one workspace with its mode and active tab', async () => {
  for (const detached of [false, true]) {
    const { store, storage, stack } = setup();
    await store.open('editor');
    if (detached) await store.undockActiveSurface();
    const saved = storage.get('a0.rightCanvas.session');
    await store.close();
    storage.set('a0.rightCanvas.session', saved);
    store.setWidth = () => {};
    store.restore();
    await store.restoreOpenSurface();
    assert.equal(store.activeSurfaceId, 'editor');
    assert.equal(store.isDetached, detached);
    assert.equal(store.isOpen, !detached);
    assert.equal(stack.length, detached ? 1 : 0);
  }
});
