import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const storage = (values) => ({
  getItem: (key) => values.get(key) ?? null,
  setItem: (key, value) => values.set(key, value),
  removeItem: (key) => values.delete(key),
});

function loadStore(path, context) {
  const source = readFileSync(new URL(path, import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export { store };', '');
  return vm.runInNewContext(`${source}\nstore`, context);
}

test('welcome sections hide independently, survive refresh and reload, and restore with notices', async () => {
  const local = new Map([['dismissed_discovery_cards', '["channels"]']]);
  const session = new Map();
  const loadWelcome = () => {
    const store = loadStore('../webui/components/welcome/welcome-store.js', {
      mountLayout() {},
      createStore: (_name, value) => value,
      getStore: () => undefined,
      localStorage: storage(local),
      sessionStorage: storage(session),
      document: { addEventListener() {} },
    });
    store.buildFrontendContext = () => ({});
    store.runBackendBannerChecks = async () => [{ id: 'system-resources' }];
    store.init();
    return store;
  };

  const store = loadWelcome();
  assert.equal(store.hiddenSections.length, 0);
  store.dismissSection('intro');
  store.dismissSection('intro');
  assert.deepEqual(Array.from(store.hiddenSections), ['intro']);
  assert.equal(local.get('welcome_hidden_intro'), 'true');
  assert.equal(local.has('welcome_hidden_quick-actions'), false);
  store.dismissSection('quick-actions');
  store.init();
  await store.refreshBanners(true);
  assert.deepEqual(Array.from(store.hiddenSections), ['intro', 'quick-actions']);
  assert.equal(store.systemResourceBanner.id, 'system-resources');

  const reloaded = loadWelcome();
  assert.deepEqual(Array.from(reloaded.hiddenSections), ['intro', 'quick-actions']);
  reloaded.dismissBanner('system-resources');
  await reloaded.undismissAll();
  assert.equal(reloaded.hiddenSections.length, 0);
  assert.equal(local.has('welcome_hidden_intro'), false);
  assert.equal(local.has('welcome_hidden_quick-actions'), false);
  assert.equal(session.has('dismissed_banners'), false);
  assert.equal(local.get('dismissed_discovery_cards'), '["channels"]');
  assert.equal(loadWelcome().hiddenSections.length, 0);
  assert.equal(reloaded.systemResourceBanner.id, 'system-resources');
});

test('one restore action brings back sections, notices, accounts and channels', async () => {
  const local = new Map([['unrelated-preference', 'keep']]);
  const session = new Map();
  const stores = new Map();
  const banners = [
    { id: 'system-resources' },
    { id: 'notice', type: 'info' },
    { id: 'discovery-oauth-accounts', type: 'hero', placement: 'after-features' },
    { id: 'channels', type: 'feature' },
  ];
  const context = {
    mountLayout() {},
    createStore: (name, value) => { stores.set(name, value); return value; },
    getStore: (name) => stores.get(name),
    localStorage: storage(local),
    sessionStorage: storage(session),
    document: { addEventListener() {}, body: { dataset: {} } },
    API: { callJsonApi: async () => ({ banners }) },
  };
  const welcome = loadStore('../webui/components/welcome/welcome-store.js', context);
  const discovery = loadStore('../plugins/_discovery/webui/discovery-store.js', { ...context });
  welcome.buildFrontendContext = () => ({});
  welcome.init();
  await Promise.all([welcome.refreshBanners(true), discovery.refreshCards()]);
  welcome.dismissSection('intro');
  welcome.dismissSection('quick-actions');
  welcome.dismissBanner('system-resources');
  welcome.dismissBanner('notice', true);
  discovery.dismissCard('discovery-oauth-accounts');
  discovery.dismissFeatureCards();
  await Promise.all([welcome.refreshBanners(true), discovery.refreshCards()]);
  assert.equal(welcome.systemResourceBanner, null);
  assert.equal(welcome.sortedBanners.length, 0);
  assert.equal(discovery.cards.length, 0);
  assert.equal(discovery.hasDismissedCards, true);

  await welcome.undismissAll();
  assert.equal(welcome.hiddenSections.length, 0);
  assert.equal(welcome.hasDismissedBanners, false);
  assert.equal(welcome.systemResourceBanner.id, 'system-resources');
  assert.equal(welcome.sortedBanners[0].id, 'notice');
  assert.equal(discovery.hasDismissedCards, false);
  assert.equal(discovery.oauthAccountCards.length, 1);
  assert.equal(discovery.featureCards.length, 1);
  assert.deepEqual([...local], [['unrelated-preference', 'keep']]);
  assert.equal(session.size, 0);

  discovery.dismissFeatureCards();
  await welcome.undismissAll();
  assert.equal(discovery.featureCards.length, 1);
  assert.equal(discovery.hasDismissedCards, false);
});
