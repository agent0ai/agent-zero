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

test('a requested tag survives the initial Browse reset exactly once', async () => {
  const store = load();
  store.search = 'old query';
  store.initialBrowseFilter = 'tag:welcome';
  store.fetchIndex = async () => true;
  await store.openIndexView();
  assert.equal(store.browseFilter, 'tag:welcome');
  assert.equal(store.search, '');
  await store.openIndexView();
  assert.equal(store.browseFilter, 'all');
});
