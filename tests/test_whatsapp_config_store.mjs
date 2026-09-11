import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

test('one-click pairing enables WhatsApp and polling stops on cancel, error, connection or cleanup', async () => {
  const requests = [];
  const timers = new Map();
  let nextTimer = 0;
  const source = readFileSync(new URL('../plugins/_whatsapp_integration/webui/whatsapp-config-store.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export const store', 'const store');
  const store = vm.runInNewContext(`${source}\nstore`, {
    createStore: (_name, value) => value,
    API: { callJsonApi: () => new Promise((resolve, reject) => requests.push({ resolve, reject })) },
    setTimeout: fn => { timers.set(++nextTimer, fn); return nextTimer; },
    clearTimeout: id => timers.delete(id),
  });
  store.config = { enabled: false };
  const initial = store.showQr();
  assert.equal(store.config.enabled, true);
  assert.equal(store.qrVisible, true);
  assert.equal(requests.length, 1);
  store.hideQr();
  requests.shift().resolve({ status: 'waiting_scan', qr: 'stale' });
  await initial;
  assert.equal(store.qrDataUrl, null);
  assert.equal(timers.size, 0);

  const old = store.showQr();
  const retry = store.showQr();
  requests.shift().resolve({ status: 'connected' });
  await old;
  assert.equal(store.qrStatus, 'loading');
  requests.shift().resolve({ status: 'waiting_scan', qr: 'current' });
  await retry;
  assert.equal(store.qrDataUrl, 'current');
  assert.equal(timers.size, 1);
  const [id, tick] = [...timers][0];
  timers.delete(id);
  const poll = tick();
  requests.shift().resolve({ status: 'connected' });
  await poll;
  assert.equal(timers.size, 0);
  assert.equal(store.qrStatus, 'connected');

  const failed = store.showQr();
  requests.shift().reject(new Error('Unavailable'));
  await failed;
  assert.equal(store.qrStatus, 'error');
  assert.equal(timers.size, 0);

  const closing = store.showQr();
  store.cleanup();
  requests.shift().resolve({ status: 'waiting_scan', qr: 'closed' });
  await closing;
  assert.equal(store.qrVisible, false);
  assert.equal(store.qrDataUrl, null);
  assert.equal(timers.size, 0);
});
