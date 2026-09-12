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
  return path === '/' ? response(path, [entry('a0', true, ''), entry('a0-other', true, '')])
    : path === '/a0/folder' ? response(path, [entry('nested.md', false, path)])
    : response(path === '$WORK_DIR' ? '/a0' : path, [entry('file10.txt'), entry('folder', true), entry('file2.txt')]);
};
const tree = createFileTree(node => opened.push(node.path), () => '/');
await tree.follow('/ignored');
assert.equal(requests.length, 0, 'hidden tree does no work');
await tree.toggle('');
assert.equal(tree.root.path, '/', 'filesystem root can be explicitly configured');
assert.deepEqual(tree.rows.map(row => row.node.name), ['/', 'a0', 'folder', 'file2.txt', 'file10.txt', 'a0-other']);
assert.ok(requests.includes('$WORK_DIR'), 'default is resolved by existing API');
const root = tree.root;
const a0 = root.children[0];
const folder = a0.children[0];
requests.length = 0;
await tree.follow('/a0/folder', '/a0/folder/nested.md');
assert.equal(tree.root, root, 'navigation from the main pane retains the root');
assert.equal(folder.expanded, true, 'navigation reveals an unexpanded folder');
assert.equal(tree.selectedPath, '/a0/folder/nested.md');
assert.equal(tree.rows.find(row => row.node.name === 'nested.md').depth, 3);
assert.deepEqual(requests, ['/a0/folder'], 'only the newly revealed folder is fetched');
await tree.expand(folder);
assert.equal(folder.expanded, false, 'chevron collapses without navigating');
assert.deepEqual(opened, []);
await tree.open(folder);
await tree.open(folder);
assert.equal(folder.expanded, true, 'name opens and preserves expansion');
assert.deepEqual(opened.splice(0), ['/a0/folder', '/a0/folder'], 'name always invokes host navigation');
assert.equal(requests.length, 1, 'reopening uses loaded children');
tree.query = 'NESTED';
assert.deepEqual(tree.rows.map(row => row.node.name), ['/', 'a0', 'folder', 'nested.md'], 'filter retains ancestors');
await tree.open(folder.children[0]);
assert.deepEqual(opened.splice(0), ['/a0/folder/nested.md']);
tree.query = '';
await tree.open(a0);
assert.deepEqual(opened.splice(0), ['/a0'], 'expanded parent is directly clickable');
await tree.follow('/a0');
assert.equal(folder.expanded, true, 'returning to parent preserves inspected branches');
await tree.follow('/a0-other');
assert.equal(tree.root, root, 'sibling navigation keeps the full tree');
assert.equal(root.children[1].expanded, true, 'similar prefixes select the correct branch');
await tree.expand(a0);
await tree.follow('/a0/folder');
assert.equal(a0.expanded, true, 'navigation reveals manually collapsed ancestors');
assert.equal(tree.root, root);
await tree.open(root);
assert.deepEqual(opened.splice(0), ['/'], 'filesystem root is clickable too');
const nested = createFileTree(() => {});
await nested.toggle('/a0/folder');
assert.deepEqual(nested.rows.filter(row => row.node.expanded).map(row => row.node.path), ['/a0', '/a0/folder'], 'default tree starts at /a0 without filesystem-root indentation');
assert.equal(nested.rows[0].depth, 0);
assert.equal(nested.rows.find(row => row.node.path === '/a0/folder').depth, 1);
await nested.follow('/usr');
assert.equal(nested.root.path, '/a0', 'navigation outside the starting folder never widens the tree');
let configuredRoot = '/a0';
const configured = createFileTree(() => {}, () => configuredRoot);
await configured.toggle('/a0/folder');
configuredRoot = '/a0/folder';
await configured.follow('/a0/folder');
assert.equal(configured.root.path, '/a0/folder', 'root setting applies even when the current directory is unchanged');
assert.equal(nested.root.path, '/a0', 'tree state stays independent');
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
assert.equal(tree.rows[1].node.name, 'new.md');
globalThis.fetchTree = async () => ({ ok: true, json: async () => ({ data: { error: 'Permission denied' } }) });
await tree.loadRoot('/denied');
assert.equal(tree.root.error, 'Permission denied');
assert.equal(tree.root.loading, false);
globalThis.fetchTree = async () => response('/denied');
await tree.load(tree.root);
assert.equal(tree.root.error, '');
assert.deepEqual(tree.root.children, [], 'empty directory is distinct from failed load');
assert.equal(tree.rows.length, 1, 'empty root remains clickable');
let finishRoot;
globalThis.fetchTree = async url => {
  const path = new URL(url, 'http://local').searchParams.get('path');
  if (path === '/') return new Promise(resolve => { finishRoot = resolve; });
  return response(path);
};
const rapid = createFileTree(() => {}, () => '/');
rapid.shown = true;
const firstFollow = rapid.follow('/a0');
const latestFollow = rapid.follow('/a0-other');
finishRoot(response('/', [entry('a0', true, ''), entry('a0-other', true, '')]));
await Promise.all([firstFollow, latestFollow]);
assert.equal(rapid.root.children[0].expanded, false, 'stale navigation does not expand old target');
assert.equal(rapid.root.children[1].expanded, true, 'latest navigation waits for the shared pending load');
requests.length = 0;
globalThis.fetchTree = async url => {
  const path = new URL(url, 'http://local').searchParams.get('path');
  requests.push(path);
  return path === '/@connections' ? response(path, [{ name: 'Server', path: '/@connections/ssh/server', is_dir: true }])
    : path === '/@connections/ssh/server' ? response(path, [entry('docs', true, path)])
    : response(path);
};
await rapid.follow('/@connections/ssh/server/docs');
assert.equal(rapid.root.name, 'Remote folders');
assert.deepEqual(requests, ['/@connections', '/@connections/ssh/server', '/@connections/ssh/server/docs'], 'remote tree follows real connection entries without requesting a provider directory');
assert.deepEqual(rapid.rows.map(row => row.node.name), ['Remote folders', 'Server', 'docs']);
const scrolled = [];
let visible = true;
const selectedRow = { checkVisibility: () => visible, scrollIntoView: options => scrolled.push(options) };
const element = { querySelector: selector => {
  assert.equal(selector, '.file-tree-row.is-selected');
  return selectedRow;
} };
rapid.scrollToSelected(element);
assert.deepEqual(scrolled, [{block:'center', inline:'nearest'}], 'selected row is brought into view');
visible = false;
rapid.scrollToSelected(element);
visible = true;
rapid.shown = false;
rapid.scrollToSelected(element);
rapid.shown = true;
rapid.scrollToSelected({querySelector: () => null});
assert.equal(scrolled.length, 1, 'hidden hosts, hidden trees and missing selections do not scroll');


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
