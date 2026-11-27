import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

test('automatic component discovery preserves moved content; explicit reloads and new paths still work', async () => {
  let changed, renders = 0;
  const component = {
    path: 'files.html', nodeType: 1,
    getAttribute(name) { return name === 'path' ? this.path : null; },
    matches: selector => selector === 'x-component',
    set innerHTML(value) { renders++; },
    appendChild() {}, querySelector: () => null,
  };
  const parent = { nodeType: 1, querySelectorAll: () => [component] };
  const source = readFileSync(new URL('../webui/js/components.js', import.meta.url), 'utf8').replace(/export /g, '');
  const { loadComponents, importComponent } = vm.runInNewContext(source + '\n({loadComponents, importComponent})', {
    console,
    document: { readyState: 'loading', addEventListener() {}, body: {} },
    MutationObserver: class { constructor(callback) { changed = callback; } observe() {} },
    fetch: async () => ({ ok: true, text: async () => '<body></body>' }),
    DOMParser: class { parseFromString() { return { querySelectorAll: () => [], body: { childNodes: [] } }; } },
  });
  await loadComponents(parent);
  assert.equal(renders, 1);
  await loadComponents(parent);
  changed([{ addedNodes: [component, parent] }]);
  await new Promise(setImmediate);
  assert.equal(renders, 1, 'moving a component or its parent must not reset content');
  await importComponent('files.html', component);
  assert.equal(renders, 2, 'explicit imports remain reloadable');
  component.path = 'editor.html';
  await loadComponents(parent);
  assert.equal(renders, 3, 'changing path loads the new component');
});

test('moving an extension or its parent retains its children, including during first load', async () => {
  let changed, resolveRequest, requests = 0;
  const writes = [];
  const extension = {
    id: 'panels', nodeType: 1, matches: selector => selector === 'x-extension',
    classList: { add() {}, remove() {} },
    getAttribute(name) { return name === 'id' ? this.id : null; },
    set innerHTML(html) { writes.push(html); },
  };
  const parent = { nodeType: 1, querySelectorAll: () => [extension] };
  const source = readFileSync(new URL('../webui/js/extensions.js', import.meta.url), 'utf8')
    .replace(/^import .*;$/gm, '').replace(/export /g, '');
  const { loadHtmlExtensions, reloadHtmlExtensions } = vm.runInNewContext(
    source + '\n({loadHtmlExtensions, reloadHtmlExtensions})', {
      console,
      document: { readyState: 'loading', addEventListener() {}, body: {} },
      MutationObserver: class { constructor(callback) { changed = callback; } observe() {} },
      cache: { get: () => null, add() {} },
      api: { callJsonApi() { requests++; return new Promise(resolve => { resolveRequest = resolve; }); } },
    },
  );
  const initial = loadHtmlExtensions(parent);
  changed([{ addedNodes: [parent, extension] }]);
  assert.equal(requests, 1);
  resolveRequest({ extensions: ['browser.html'] });
  await initial;
  const browser = '<x-component path="/browser.html"></x-component>';
  assert.deepEqual(writes, [browser]);
  changed([{ addedNodes: [extension, parent] }]);
  assert.equal(requests, 1);
  assert.deepEqual(writes, [browser]);

  const reload = reloadHtmlExtensions(parent);
  const finishReload = resolveRequest;
  extension.id = 'other';
  const switched = loadHtmlExtensions(parent);
  resolveRequest({ extensions: [] });
  await switched;
  finishReload({ extensions: ['browser.html'] });
  await reload;
  changed([{ addedNodes: [parent] }]);
  assert.equal(requests, 3);
  assert.deepEqual(writes, [browser, '', ''], 'a late reload must not overwrite the new point');
});
