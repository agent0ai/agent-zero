import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function load(path, globals = {}) {
  const source = readFileSync(new URL(`../${path}`, import.meta.url), 'utf8')
    .replace(/^import [\s\S]*? from .*;\n/gm, '')
    .replace('export const store', 'const store');
  return vm.runInNewContext(`${source}\nstore`, {
    createStore: (_, value) => value,
    TOP_CLOUD_PROVIDER_IDS: [], MORE_CLOUD_PROVIDER_IDS: [],
    LOCAL_PROVIDER_IDS: [], ONBOARDING_PROVIDER_OVERRIDES: {},
    ...globals,
  });
}

const onboardingPath = 'plugins/_onboarding/webui/onboarding-store.js';

test('Codex onboarding chooses the recommended pair and preserves explicit model choices', async () => {
  const store = load(onboardingPath, {
    callJsonApi: async () => ({ ok: true, models: ['gpt-5.5', 'gpt-6-luna', 'gpt-6.1-terra'] }),
  });
  store.loading = false;
  store.config = {};
  store.oauthStatus = { provider_map: { codex_oauth: {
    provider_id: 'codex_oauth', connected: true,
    default_model: 'gpt-6.1-terra', default_models: ['gpt-6.1-terra', 'gpt-6-luna'],
  } } };
  store.loadOauthStatus = async () => {};

  await store.selectOAuthProvider('codex_oauth');
  assert.equal(store.config.chat_model.name, 'gpt-6.1-terra');
  await store.primaryAction();
  assert.equal(store.step, 'utility');
  assert.equal(store.config.utility_model.name, 'gpt-6-luna');

  for (const slot of ['chat_model', 'utility_model']) {
    store.selectModel(slot, 'gpt-5.5');
    await store.loadModels(slot);
    assert.equal(store.config[slot].name, 'gpt-5.5');
  }
});

for (const hasPendingChat of [true, false]) {
  test(`Continue closes onboarding without creating a chat (pending chat: ${hasPendingChat})`, async () => {
    const document = new EventTarget();
    const sends = [];
    let newChats = 0, closed = 0, configured = false;
    const modelConfigStore = {
      persistApiKeysForConfig: async () => {}, refreshApiKeyStatus: async () => {},
    };
    const store = load(onboardingPath, {
      document, CustomEvent: Event, modelConfigStore,
      fetchApi: async () => {
        configured = true;
        return { json: async () => ({ ok: true }) };
      },
      window: { closeModal: async () => {
        closed++;
        document.dispatchEvent(new Event('modal-closed'));
      } },
      chatsStore: { newChat: async () => { newChats++; } },
    });
    const gate = load('webui/components/chat/model-gate-store.js', {
      document, modelConfigStore,
      sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
      callJsonApi: async () => ({ model_configured: configured }),
      sendMessage: async options => { sends.push(options); return true; },
    });
    if (hasPendingChat) {
      gate.start({ message: 'My first question', attachments: [], messageId: 'first-message', context: 'original-chat' });
    }
    store.config = {};
    store.loading = false;
    await store.completeSetup();
    await new Promise(setImmediate);
    assert.equal(store.step, 'ready');
    assert.equal(store.primaryButtonLabel(), 'Continue');
    await store.primaryAction();
    await new Promise(setImmediate);
    assert.equal(closed, 1);
    assert.equal(newChats, 0);
    assert.equal(sends.length, hasPendingChat ? 1 : 0);
    if (hasPendingChat) {
      assert.equal(sends[0].context, 'original-chat');
      assert.equal(sends[0].message, 'My first question');
      assert.equal(sends[0].messageId, 'first-message');
      assert.equal(gate.pending, null);
    }
  });
}
