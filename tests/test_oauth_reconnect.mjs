import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const requests = [];
const timers = new Map();
const dismissed = [];
const copied = [];
const feedback = [];
let clipboardDenied = false;
const source = readFileSync(new URL('../plugins/_oauth/webui/oauth-config-store.js', import.meta.url), 'utf8')
  .replace(/^import [\s\S]*? from .*;\n/gm, '').replace('export const store', 'const store');
const store = vm.runInNewContext(`${source}\nstore`, {
  createStore: (_name, value) => value,
  callJsonApi: async (url, payload) => {
    requests.push({ url, payload });
    assert.ok(url.endsWith('/start_login'));
    return { ok: true, flow: 'device_code', attempt_id: 'test', user_code: 'TEST', verification_url: 'https://example.com', interval: 5 };
  },
  window: {
    open() {},
    setTimeout: fn => { timers.set(1, fn); return 1; },
    clearTimeout: id => timers.delete(id),
  },
  toastFrontendInfo() {},
  toastFrontendSuccess: message => feedback.push(message),
  toastFrontendError: message => feedback.push(message),
  copyToClipboard: async code => {
    if (clipboardDenied) throw new Error('Permission denied');
    copied.push(code);
  },
  notificationStore: { dismissToast: id => dismissed.push(id) },
});
const provider = 'codex_oauth';
store.status = { provider_map: { [provider]: { provider_id: provider, connected: true, reconnect_required: true } } };
store.modelConfig = { chat_model: { provider, name: 'chosen-model' } };
assert.equal(store.providerPrimaryLabel(provider), 'Reconnect');
assert.equal(store.providerReadinessLabel(provider), 'Sign in again to continue');
assert.equal(store.providerDetailOpen(provider), false);
await store.connectProvider(provider);
assert.equal(store.providerPrimaryLabel(provider), 'Waiting');
assert.equal(store.providerDetailOpen(provider), true);
assert.equal(store.providerDevice(provider).user_code, 'TEST');
await store.copyDeviceCode(provider);
assert.deepEqual(copied, ['TEST']);
assert.equal(feedback.pop(), 'Sign-in code copied.');
clipboardDenied = true;
await store.copyDeviceCode(provider);
assert.equal(feedback.pop(), 'Could not copy the code. Select it and copy manually.');
assert.equal(timers.size, 1);
await store.connectProvider(provider);
assert.equal(requests.length, 1);
store.cancelConnect(provider);
assert.equal(timers.size, 0);
assert.equal(store.providerDevice(provider), null);
await store.copyDeviceCode(provider);
assert.equal(copied.length, 1);
assert.equal(feedback.length, 0);
assert.equal(store.providerConnected(provider), true);
assert.equal(store.modelConfig.chat_model.name, 'chosen-model');
assert.equal(store.providerPrimaryLabel(provider), 'Reconnect');
await store.handleProviderConnected(provider, { statusLoaded: true });
assert.deepEqual(dismissed, ['toast-oauth-codex-reconnect']);
