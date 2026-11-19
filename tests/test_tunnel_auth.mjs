import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function setup(auth = false, fail = false) {
  const calls = [], errors = [], confirmations = [];
  const source = readFileSync(new URL('../plugins/_tunnel/webui/tunnel-store.js', import.meta.url), 'utf8')
    .replace(/^import .*;$/gm, '').replace('export { store };', '');
  const context = {
    createStore: (_, model) => model,
    Sleep: { Skip: async () => {} },
    console: { error() {}, warn() {} },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    document: { getElementById: () => null },
    setInterval: () => 1, clearInterval() {},
    confirm: message => { confirmations.push(message); return true; },
    window: { toastFrontendError: message => errors.push(message), toastFrontendInfo() {} },
    fetchApi: async (url, options) => {
      const body = JSON.parse(options.body);
      calls.push(body);
      if (fail) throw new Error('Unavailable');
      return { json: async () => body.action === 'get'
        ? { auth_configured: auth, provider: 'cloudflared', success: false }
        : { success: true, tunnel_url: 'https://example.test' } };
    },
  };
  const store = vm.runInNewContext(`${source}\nstore`, context);
  return { store, calls, errors, confirmations };
}

for (const fail of [false, true]) {
  test(`Start and New URL fail closed when ${fail ? 'auth check fails' : 'sign-in is missing'}`, async () => {
    const { store, calls, errors, confirmations } = setup(false, fail);
    await store.generateLink();
    await store.refreshLink();
    assert.equal(calls.filter(call => call.action !== 'get').length, 0);
    assert.equal(confirmations.length, 0);
    assert.equal(errors.length, 2);
    assert.equal(store.isLoading, false);
  });
}

test('authenticated startup keeps the selected provider', async () => {
  const { store, calls, errors } = setup(true);
  store.provider = 'tailscale';
  await store.generateLink();
  assert.equal(calls.find(call => call.action === 'create').provider, 'tailscale');
  assert.equal(errors.length, 0);
  assert.equal(store.linkGenerated, true);
  assert.equal(store.isLoading, false);
});


test('refresh returns to idle if sign-in disappears before replacement starts', async () => {
  const { store, calls } = setup(true);
  let checks = 0;
  store.requireAuth = async () => ++checks === 1;
  await store.refreshLink();
  assert.equal(calls.filter(call => call.action === 'create').length, 0);
  assert.equal(store.isLoading, false);
});
