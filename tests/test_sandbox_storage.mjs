import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function model(callJsonApi, errors = [], actions = {}) {
  const source = readFileSync(new URL('../plugins/_sandboxing/webui/sandboxing-store.js', import.meta.url), 'utf8')
    .replace(/^import [\s\S]*?;\n/gm, '').replace('export const store', 'const store');
  return vm.runInNewContext(source + '\nmodel;', {
    createStore: (_, value) => value, callJsonApi,
    toastFrontendError: message => errors.push(message), toastFrontendSuccess() {}, ...actions,
  });
}

test('creation form follows the configured sandbox name and honors an explicit type', async () => {
  const defaults = { name: 'home', sandbox_type: 'temporary', default_sandbox_type: 'permanent' };
  const requests = [];
  const store = model(async (_, input) => {
    if (input.action === 'create') requests.push(input);
    return { ok: true, defaults };
  });
  await store.refresh();
  store.form.name = 'research';
  assert.equal(store.creationType, 'temporary');
  store.form.name = 'home';
  assert.equal(store.creationType, 'permanent');
  store.creationType = 'temporary';
  await store.createSandbox();
  assert.equal(requests[0].sandbox_type, 'temporary');
  store.form.name = 'home';
  assert.equal(store.creationType, 'permanent');
});

test('explicit size calculation leaves polling and actions free and survives refresh', async () => {
  let finish;
  const calls = [];
  const sandbox = { name: 'browser', created_at: 'first' };
  const store = model(async (_, input) => {
    calls.push(input.action);
    if (input.action === 'disk_usage') return new Promise(resolve => { finish = resolve; });
    return { ok: true, sandboxes: [{ ...sandbox, size_bytes: null }] };
  });
  await store.refresh();
  assert.deepEqual(calls, ['list']);
  assert.equal(store.formatSize(null), 'Not calculated');
  assert.equal(store.formatSize(0), '0 B');
  const pending = store.measureStorage(sandbox);
  await store.measureStorage(sandbox);
  assert.equal(store.storageFor(sandbox).loading, true);
  assert.equal(store.busy, false);
  assert.equal(store.isBusy(sandbox.name), false);
  await store.perform('stop', sandbox);
  assert.deepEqual(calls, ['list', 'disk_usage', 'stop', 'list']);
  finish({ ok: true, size_bytes: 1024 });
  await pending;
  await store.refresh();
  assert.equal(store.storageFor(store.sandboxes[0]).size_bytes, 1024);
  assert.equal(store.storageFor(sandbox).loading, false);
});

test('a late size response never replaces a recreated sandbox measurement', async () => {
  const replies = [];
  const store = model(() => new Promise(resolve => replies.push(resolve)));
  const old = { name: 'browser', created_at: 'first' };
  const current = { name: 'browser', created_at: 'second' };
  const first = store.measureStorage(old);
  assert.equal(store.storageFor(current), null);
  const second = store.measureStorage(current);
  replies[0]({ ok: true, size_bytes: 111 });
  await first;
  assert.equal(store.storageFor(current).loading, true);
  assert.equal(store.storageFor(current).size_bytes, undefined);
  replies[1]({ ok: true, size_bytes: 222 });
  await second;
  assert.equal(store.storageFor(current).size_bytes, 222);
});

test('failed measurement releases its button and reports through notifications', async () => {
  const errors = [];
  const store = model(async () => ({ ok: false, error: 'Missing sandbox' }), errors);
  const sandbox = { name: 'browser', created_at: 'first' };
  await store.measureStorage(sandbox);
  assert.equal(store.storageFor(sandbox).loading, false);
  assert.deepEqual(errors, ['Missing sandbox']);
});

test('browse files closes Sandboxes before opening the Files surface at its connection', async () => {
  const calls = [];
  const store = model(null, [], {
    closeModal: async path => { calls.push(path); },
    openSurface: async (surface, { path }) => { calls.push(surface, path); },
  });
  const path = '/@connections/sandbox/0123456789abcdef0123456789abcdef';
  await store.browseFiles({ browse_path: path });
  assert.deepEqual(calls, ['/plugins/_sandboxing/webui/main.html', 'files', path]);
});
