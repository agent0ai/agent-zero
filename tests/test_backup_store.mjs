import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

function setup({ statuses = ['running', 'completed'], download, json } = {}) {
  const calls = [], clicks = [], toasts = [];
  let store;
  const source = readFileSync(new URL('../webui/components/settings/backup/backup-store.js', import.meta.url), 'utf8')
    .replace(/^import\b[\s\S]*?;\r?\n/gm, '')
    .replace('export { store };', '');
  const metadata = { include_patterns: ['**'], exclude_patterns: [], backup_name: 'my-backup' };
  const context = vm.createContext({
    console, Intl, AbortController,
    setTimeout: callback => setTimeout(callback, 0), clearTimeout,
    createStore: (_, model) => { store = model; return model; },
    getUserHour12: () => false, getUserTimezone: () => 'UTC',
    callJsonApi: async (url, data) => {
      calls.push(data);
      if (json) return json(data);
      return data.action === 'start'
        ? { success: true, status: 'running', job_id: 'job-1' }
        : { success: true, status: statuses.shift(), error: 'Compression failed' };
    },
    fetchApi: async (url, options) => {
      calls.push(JSON.parse(options.body));
      return download || new Response('zip contents', { headers: { 'Content-Type': 'application/zip' } });
    },
    window: {
      URL: { createObjectURL: () => 'blob:backup', revokeObjectURL() {} },
      toastFrontendInfo: (...args) => toasts.push(args),
      toastFrontendError: (...args) => toasts.push(args),
    },
    document: {
      getElementById: () => null,
      createElement: () => ({ click() { clicks.push(this.download); } }),
    },
  });
  vm.runInContext(source, context);
  store.backupEditor = { getValue: () => JSON.stringify(metadata), destroy() {} };
  return { store, calls, clicks, toasts };
}

test('polls a running backup and downloads only the completed archive', async () => {
  const { store, calls, clicks, toasts } = setup();
  await store.createBackup();
  assert.deepEqual(calls.map(call => call.action), ['start', 'status', 'status', 'download']);
  assert.deepEqual(clicks, ['my-backup.zip']);
  assert.equal(store.loading, false);
  assert.equal(store.backupJob, null);
  assert.equal(store.error, '');
  assert.ok(toasts.some(toast => toast[0] === 'Downloading...'));
});

test('a failed job shows its error and permits a fresh backup', async () => {
  const { store, calls, clicks } = setup({ statuses: ['failed'] });
  await store.createBackup();
  assert.deepEqual(calls.map(call => call.action), ['start', 'status']);
  assert.deepEqual(clicks, []);
  assert.match(store.error, /Compression failed/);
  assert.equal(store.backupJob, null);
  assert.equal(store.loading, false);
});

test('a JSON error response is displayed instead of downloaded as a ZIP', async () => {
  const { store, clicks } = setup({
    statuses: ['completed'],
    download: Response.json({ success: false, error: 'Archive unavailable' }),
  });
  await store.createBackup();
  assert.deepEqual(clicks, []);
  assert.equal(store.error, 'Archive unavailable');
  assert.equal(store.backupJob.id, 'job-1');
});

test('closing during creation preserves the job for a later resume', async () => {
  let acceptStart;
  const { store, calls, clicks } = setup({
    json: data => data.action === 'start'
      ? new Promise(resolve => { acceptStart = resolve; })
      : { success: true, status: 'completed' },
  });
  const first = store.createBackup();
  await store.createBackup(); // A second click shares the in-flight operation.
  store.onClose();
  acceptStart({ success: true, job_id: 'job-1' });
  await first;
  assert.deepEqual(calls.map(call => call.action), ['start']);
  assert.deepEqual(clicks, []);
  assert.equal(store.backupJob.id, 'job-1');
  await store.createBackup();
  assert.deepEqual(calls.map(call => call.action), ['start', 'status', 'download']);
  assert.deepEqual(clicks, ['my-backup.zip']);
});

test('closing during a status request stops polling and preserves restore state', async () => {
  let acceptStatus;
  const { store, calls, clicks } = setup({
    json: () => new Promise(resolve => { acceptStatus = resolve; }),
  });
  store.backupJob = { id: 'job-1', name: 'existing' };
  const pending = store.createBackup();
  store.onClose();
  store.mode = 'restore';
  store.loading = true;
  acceptStatus({ success: true, status: 'completed' });
  await pending;
  assert.equal(store.loading, true);
  assert.deepEqual(calls.map(call => call.action), ['status']);
  assert.deepEqual(clicks, []);
});

test('expired jobs clear the resume state', async () => {
  const { store, clicks } = setup({
    json: () => { throw new Error(JSON.stringify({ code: 'backup_not_found', error: 'Expired' })); },
  });
  store.backupJob = { id: 'expired', name: 'old' };
  await store.createBackup();
  assert.equal(store.backupJob, null);
  assert.deepEqual(clicks, []);
  assert.equal(store.loading, false);
});

test('a stalled status request can be detached and resumed before its late response', async () => {
  let acceptOldStatus, acceptNewStatus;
  const { store, calls, clicks } = setup({
    json: () => new Promise(resolve => {
      if (!acceptOldStatus) acceptOldStatus = resolve;
      else acceptNewStatus = resolve;
    }),
  });
  store.backupJob = { id: 'job-1', name: 'existing' };
  const oldAttempt = store.createBackup();
  store.onClose();
  await Promise.race([
    oldAttempt,
    new Promise((_, reject) => setTimeout(() => reject(new Error('cancelled polling remained busy')), 200)),
  ]);
  assert.equal(store.backupBusy, false);
  const resumed = store.createBackup();
  assert.equal(store.backupBusy, true);
  acceptOldStatus({ success: false, status: 'failed', error: 'Stale failure' });
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(store.backupBusy, true);
  assert.equal(store.backupJob.id, 'job-1');
  assert.equal(store.error, '');
  acceptNewStatus({ success: true, status: 'completed' });
  await resumed;
  assert.deepEqual(calls.map(call => call.action), ['status', 'status', 'download']);
  assert.deepEqual(clicks, ['existing.zip']);
  assert.equal(store.backupJob, null);
  assert.equal(store.backupBusy, false);
});

test('network errors preserve a known job for retry', async () => {
  const { store, clicks } = setup({ json: () => { throw new Error('Network unavailable'); } });
  store.backupJob = { id: 'job-1', name: 'existing' };
  await store.createBackup();
  assert.equal(store.backupJob.id, 'job-1');
  assert.match(store.error, /Network unavailable/);
  assert.deepEqual(clicks, []);
});
