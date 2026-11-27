import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function load() {
  const source = readFileSync(new URL('../plugins/_plugin_installer/webui/pluginInstallStore.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export { store };', '');
  return vm.runInNewContext(`${source}\nstore`, { createStore: (_, value) => value, URL });
}

test('Official stays immediately after All and can be selected when empty', () => {
  const store = load();
  assert.equal(store.browseFilters[0].key, 'all');
  assert.equal(store.browseFilters[1].key, 'official');
  assert.equal(store.browseFilters[1].label, 'Official');
  assert.equal(store.browseFilters[1].count, 0);
  store.page = 3;
  store.setBrowseFilter('official');
  assert.equal(store.browseFilter, 'official');
  assert.equal(store.page, 1);
  assert.equal(store.filteredPlugins.length, 0);
});

test('Official derives membership from the GitHub repository owner and combines with search', () => {
  const store = load();
  const excludedUrls = [
    undefined, '', 'not a URL',
    'https://github.com/community/plugin',
    'https://github.com/agent0ai-community/plugin',
    'https://github.com/community/agent0ai',
    'https://github.com/agent0ai',
    'https://github.com/agent0ai/',
    'https://github.com.evil.test/agent0ai/plugin',
    'https://github.com@evil.test/agent0ai/plugin',
    'https://example.com/agent0ai/plugin',
    'https://example.com/?repo=https://github.com/agent0ai/plugin',
    'ftp://github.com/agent0ai/plugin',
  ];
  store.index.plugins = {
    official: { github: 'https://github.com/agent0ai/plugin', title: 'Official tools' },
    mixedCase: { github: ' https://GitHub.com/Agent0AI/plugin.git/ ', title: 'Another plugin' },
    ...Object.fromEntries(excludedUrls.map((github, i) => [
      `excluded-${i}`, { github, author: 'agent0ai', tags: ['official', 'Official'] },
    ])),
  };
  assert.equal(store.browseFilters[1].key, 'official');
  assert.equal(store.browseFilters[1].count, 2);
  assert.equal(store.browseFilters.filter(filter => filter.label.toLowerCase() === 'official').length, 1);
  store.setBrowseFilter('official');
  assert.deepEqual(Array.from(store.filteredPlugins, plugin => plugin.key).sort(), ['mixedCase', 'official']);
  store.search = 'tools';
  assert.deepEqual(Array.from(store.filteredPlugins, plugin => plugin.key), ['official']);
  assert.equal(store.browseFilters[1].count, 2);
});

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
