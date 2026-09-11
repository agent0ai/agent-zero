"""Exercise the shared frontend tree without network or browser dependencies."""
from pathlib import Path
import subprocess


def test_file_tree_navigation_filter_errors_and_stale_loads():
    source = Path('webui/components/modals/file-browser/file-tree.js').read_text()
    source = source.replace('import { fetchApi } from "/js/api.js";', 'const fetchApi = (...args) => globalThis.fetchTree(...args);')
    script = source + r'''
import assert from 'node:assert/strict';
const requests = [];
const opened = [];
const response = (path, entries = []) => ({ ok: true, json: async () => ({ data: { current_path: path, parent_path: '/', entries } }) });
const entry = (name, is_dir = false, parent = '/a0') => ({ name, is_dir, path: `${parent}/${name}`.replace(/^\//, '') });
globalThis.fetchTree = async url => {
  const path = new URL(url, 'http://local').searchParams.get('path');
  requests.push(path);
  return path === '/a0/folder' ? response(path, [entry('nested.md', false, path)])
    : response(path === '$WORK_DIR' ? '/a0' : path, [entry('file10.txt'), entry('folder', true), entry('file2.txt')]);
};
const tree = createFileTree(node => opened.push(node.path));
await tree.follow('/ignored');
assert.equal(requests.length, 0, 'hidden tree does no work');
await tree.toggle('');
assert.equal(tree.root.path, '/a0', 'default is resolved by existing API');
assert.deepEqual(tree.rows.map(row => row.node.name), ['folder', 'file2.txt', 'file10.txt']);
const folder = tree.rows[0].node;
await tree.expand(folder);
assert.equal(requests.length, 2, 'only expanded folder fetched');
assert.equal(tree.rows[1].depth, 1);
await tree.expand(folder);
await tree.expand(folder);
assert.equal(requests.length, 2, 'reopening a branch uses loaded children');
await tree.open(folder);
assert.equal(folder.expanded, false, 'folder name collapses an expanded branch');
assert.deepEqual(opened, [], 'collapse does not navigate and reopen the branch');
assert.equal(tree.rows.some(row => row.node.name === 'nested.md'), false);
await tree.open(folder);
assert.equal(folder.expanded, true, 'folder name expands a collapsed branch');
assert.deepEqual(opened.splice(0), ['/a0/folder'], 'expanding still navigates');
assert.equal(requests.length, 2, 'name toggle reuses loaded children');
tree.query = 'NESTED';
assert.deepEqual(tree.rows.map(row => row.node.name), ['folder', 'nested.md'], 'filter retains parent');
await tree.open(folder.children[0]);
assert.deepEqual(opened, ['/a0/folder/nested.md']);
await tree.follow('/a0/folder', '/a0/folder/nested.md');
assert.equal(tree.root.path, '/a0', 'navigation inside root preserves expansions');
assert.equal(tree.selectedPath, '/a0/folder/nested.md');
await tree.follow('/a0-other');
assert.equal(tree.root.path, '/a0-other', 'sibling with same prefix is outside root');
const other = createFileTree(() => {});
assert.equal(other.shown, false, 'host state is independent');
let finishOld;
globalThis.fetchTree = () => new Promise(resolve => { finishOld = resolve; });
const oldLoad = tree.loadRoot('/old');
globalThis.fetchTree = async () => response('/new', [entry('new.md', false, '/new')]);
await tree.loadRoot('/new');
finishOld(response('/old', [entry('stale.md')]));
await oldLoad;
assert.equal(tree.root.path, '/new');
assert.equal(tree.rows[0].node.name, 'new.md');
globalThis.fetchTree = async () => ({ ok: true, json: async () => ({ data: { error: 'Permission denied' } }) });
await tree.loadRoot('/denied');
assert.equal(tree.root.error, 'Permission denied');
assert.equal(tree.root.loading, false);
globalThis.fetchTree = async () => response('/denied');
await tree.load(tree.root);
assert.equal(tree.root.error, '');
assert.equal(tree.rows.length, 0, 'empty directory is distinct from failed load');
'''
    subprocess.run(['node', '--input-type=module', '-e', script], check=True, timeout=15)


def test_unmounting_old_canvas_keeps_current_modal_alive():
    import json
    import re

    cases = [
        ('plugins/_editor/webui/editor-store.js', 'cleanup', '_root'),
        ('webui/components/modals/file-browser/file-browser-store.js', 'onUnmount', '_mountedElement'),
    ]
    for path, method, owner in cases:
        source = Path(path).read_text()
        body = re.search(rf'  {method}\(element = null\) {{(.*?)\n  }},', source, re.S).group(1)
        script = f'''
const assert = require('node:assert/strict');
const cleanup = new Function('element', {json.dumps(body)});
const modal = {{}};
let calls = 0;
const state = {{
  {owner}: modal, _mode: 'modal',
  flushInput() {{ calls++; }}, destroySourceEditor() {{ calls++; }},
  _headerCleanup() {{ calls++; }}, _floatingCleanup() {{ calls++; }},
  cancelMountedDefaultLoad() {{ calls++; }}, closeDropdown() {{ calls++; }},
}};
cleanup.call(state, {{}});
assert.equal(calls, 0, 'old canvas must not tear down active modal');
assert.equal(state.{owner}, modal);
cleanup.call(state, modal);
assert.ok(calls > 0, 'current host still cleans up');
'''
        subprocess.run(['node', '-e', script], check=True, timeout=15)

    registration = Path('plugins/_editor/extensions/webui/right_canvas_register_surfaces/register-editor.js').read_text()
    registration = re.sub(r'^import .*;\n', '', registration)
    registration = registration.replace('export default ', '')
    script = '''
const assert = require('node:assert/strict');
const panel = {};
let cleaned;
let surface;
const editorStore = { cleanup(element) { cleaned = element; } };
const document = { querySelector(selector) { assert.equal(selector, '.editor-canvas-surface .editor-panel'); return panel; } };
''' + registration + '''
await registerEditorSurface({registerSurface(value) { surface = value; }});
await surface.close();
assert.equal(cleaned, panel, 'surface close identifies the canvas host');
'''
    subprocess.run(['node', '-e', '(async () => {' + script + '})()'], check=True, timeout=15)
