import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function load() {
  const source = readFileSync(new URL('../plugins/_plugin_installer/webui/pluginInstallStore.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export { store };', '');
  return vm.runInNewContext(`${source}\nstore`, { createStore: (_, value) => value });
}

test('Welcome matches secondary tags, counts each plugin once, and stays discoverable when empty', () => {
  const store = load();
  Object.defineProperty(store, 'pluginsList', { value: [
    { key: 'terminal', tags: ['tools', 'welcome', 'welcome'] }, { key: 'chats', tags: ['welcome'] }, { key: 'files', tags: ['files'] },
  ] });
  assert.equal(store.filteredPlugins.length, 3);
  store.setBrowseFilter('tag:welcome');
  assert.equal(store.filteredPlugins.length, 2);
  assert.equal(store.browseFilters.find(filter => filter.key === 'tag:welcome').count, 2);
  const empty = load();
  assert.equal(empty.browseFilters.find(filter => filter.key === 'tag:welcome').count, 0);
});

test('Provider stays visible below the popular tags and only matches its exact tag', () => {
  const store = load();
  const popularTags = ['tools', 'models', 'search', 'files', 'data'];
  Object.defineProperty(store, 'pluginsList', { value: [
    { key: 'eligible', tags: [...popularTags, 'provider', 'provider'] },
    { key: 'excluded', description: 'Another model provider', tags: popularTags },
    { key: 'related', tags: [...popularTags, 'provider-tools'] },
  ] });
  store.setBrowseFilter('tag:provider');
  assert.equal(store.filteredPlugins.length, 1);
  assert.equal(store.filteredPlugins[0].key, 'eligible');
  assert.equal(store.browseFilters.filter(filter => filter.key === 'tag:provider').length, 1);
  assert.equal(store.browseFilters.find(filter => filter.key === 'tag:provider').count, 1);
  const empty = load();
  assert.equal(empty.browseFilters.find(filter => filter.key === 'tag:provider').count, 0);
});

test('Channels stays discoverable before the tag exists and matches secondary tags exactly once', () => {
  const store = load();
  assert.equal(store.browseFilters.find(filter => filter.key === 'tag:channels').count, 0);
  Object.defineProperty(store, 'pluginsList', { value: [
    { key: 'eligible', tags: ['tools', 'models', 'search', 'files', 'data', 'channels', 'channels'] },
    { key: 'excluded', description: 'Channels integration', tags: ['channel-tools'] },
  ] });
  store.setBrowseFilter('tag:channels');
  assert.equal(store.filteredPlugins.length, 1);
  assert.equal(store.filteredPlugins[0].key, 'eligible');
  assert.equal(store.browseFilters.filter(filter => filter.key === 'tag:channels').length, 1);
  assert.equal(store.browseFilters.find(filter => filter.key === 'tag:channels').count, 1);
});

for (const tag of ['welcome', 'provider', 'channels']) {
  test(`the requested ${tag} tag survives the initial Browse reset exactly once`, async () => {
    const store = load();
    store.search = 'old query';
    store.page = 3;
    store.initialBrowseFilter = `tag:${tag}`;
    store.fetchIndex = async () => true;
    await store.openIndexView();
    assert.equal(store.browseFilter, `tag:${tag}`);
    assert.equal(store.search, '');
    assert.equal(store.page, 1);
    await store.openIndexView();
    assert.equal(store.browseFilter, 'all');
  });
}
