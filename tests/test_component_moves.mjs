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
