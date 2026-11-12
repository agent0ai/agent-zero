import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function load(api) {
  const source = readFileSync(new URL('../plugins/_time_travel/webui/time-travel-store.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export const store', 'const store');
  return vm.runInNewContext(`${source}\nstore`, {
    createStore: (_, value) => value, callJsonApi: api,
    getContext: () => 'ctx', URLSearchParams, setTimeout, clearTimeout,
    formatDateTime: value => value,
  });
}

const page = { ok: true, current_hash: 'saved', workspace: { id: 'one', available: true }, present: null,
  commits: [{ hash: 'saved', is_current: true, files: [] }], has_more: false };

test('opening history selects saved history and does not inspect workspace files', async () => {
  const calls = [];
  const store = load(async (path) => { calls.push(path); return structuredClone(page); });
  store.selectedWorkspaceId = 'one';
  await store.refresh({ skipWorkspaceLoad: true });
  assert.equal(store.selectedHash, 'saved');
  assert.equal(store.timelineRows()[0].message, 'Check current changes');
  assert.deepEqual(calls, ['/plugins/_time_travel/history_list']);
});

test('current changes are checked explicitly and late responses cannot cross workspaces', async () => {
  let resolve;
  const store = load(path => path.endsWith('history_present')
    ? new Promise(done => { resolve = done; }) : Promise.resolve(structuredClone(page)));
  store.selectedWorkspaceId = 'one';
  await store.refresh({ skipWorkspaceLoad: true });
  store.selectRow(store.timelineRows()[0]);
  assert.equal(store.presentLoading, true);
  await store.selectWorkspace('two');
  resolve({ ok: true, present: { dirty: true, files: [{ path: 'wrong-workspace' }] } });
  await new Promise(setImmediate);
  assert.equal(store.payload.present, null);
  assert.equal(store.presentLoading, false);
});

test('clearing a selection invalidates an in-flight diff', async () => {
  let resolve;
  const store = load(() => new Promise(done => { resolve = done; }));
  store.payload = structuredClone(page);
  store.payload.commits[0].files = [{ path: 'file.txt' }];
  store.selectRow(store.timelineRows()[1]);
  store.payload.commits[0].files = [];
  await store.loadSelectedDiff();
  resolve({ ok: true, patch: 'stale' });
  await new Promise(setImmediate);
  assert.equal(store.selectedDiff, null);
  assert.equal(store.diffLoading, false);
});
