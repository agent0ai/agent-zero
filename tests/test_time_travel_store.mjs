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

test('storage shows small histories accurately and describes active expiry limits', () => {
  const store = load(() => {});
  store.payload = { storage: { object_bytes: 4096, commits: 4, retention_enabled: true,
    max_snapshots: 500, max_age_days: 30, max_file_mb: 8 } };
  assert.match(store.storageLabel(), /4 KiB/);
  assert.match(store.storageLabel(), /500 recent snapshots/);
  assert.match(store.storageLabel(), /30 days/);
  assert.match(store.storageLabel(), /Files above 8 MiB excluded/);
  store.payload.storage.retention_enabled = false;
  assert.match(store.storageLabel(), /Snapshot expiry off/);
});

test('checkpoint revert is refused before sending a request', async () => {
  const store = load(() => { throw new Error('must not request checkpoint revert'); });
  store.payload = structuredClone(page);
  store.payload.commits[0].metadata = { retention_checkpoint: true };
  store.selectedHash = 'saved';
  await store.openPreview('revert');
  assert.equal(store.previewOpen, false);
});
