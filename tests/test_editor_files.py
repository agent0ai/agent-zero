"""File routing and shared Editor state, executed without a browser."""
from pathlib import Path
import re
import subprocess


def test_shared_editor_file_routing_and_dirty_tabs():
    def model(path):
        source = Path(path).read_text()
        source = re.sub(r'^import\b[\s\S]*?;\n', '', source, flags=re.M)
        return source.replace('export const store = createStore', 'const store = createStore')

    browser = model('webui/components/modals/file-browser/file-browser-store.js')
    editor = model('plugins/_editor/webui/editor-store.js')
    script = r'''
import assert from 'node:assert/strict';
const window = globalThis;
const createStore = (_name, model) => model;
const createFileTree = () => ({});
const getNamespacedClient = () => ({ addHandlers() {} });
const registerUrlHandler = () => {};
const opened = [];
const openLatestSurface = async (...args) => opened.push(args);
const fileBrowserStore = (() => {
''' + browser + r'''
return store;
})();
fileBrowserStore.limits = { max_text_bytes: 42, max_file_bytes: 1000 };
const file = name => ({ name, path: `/a0/${name}`, size: 42 });
for (const name of ['file.py', 'probe.jsonl', 'config.yaml', 'Dockerfile', '.env', 'file.unknown', 'note.md', 'note.txt']) {
  assert.equal(fileBrowserStore.fileSurfaceTarget(file(name)), 'editor', name);
}
assert.equal(fileBrowserStore.fileSurfaceTarget(file('page.html')), 'browser');
assert.equal(fileBrowserStore.fileSurfaceTarget(file('sheet.xlsx')), 'desktop');
assert.equal(fileBrowserStore.isEditableFile(file('page.html')), true);
assert.equal(fileBrowserStore.isEditableFile(file('image.png')), false);
assert.equal(fileBrowserStore.isEditableFile({ ...file('big.py'), size: 43 }), false);
fileBrowserStore.configurePicker({ pickerMode: 'text-open' });
assert.equal(fileBrowserStore.pickerAllowsEntry(file('page.html')), true);
fileBrowserStore.configurePicker({ pickerMode: 'save-as', filename: 'Dockerfile', defaultExtension: '' });
assert.equal(fileBrowserStore.pickerFilenameValue(), 'Dockerfile');
assert.equal(fileBrowserStore.validatePickerFilename(), true);
fileBrowserStore.pickerFilename = '../escape.py';
assert.equal(fileBrowserStore.validatePickerFilename(), false);
const canvasRow = {}, modalRow = {};
fileBrowserStore.getDropdownStyle = () => ({});
fileBrowserStore.toggleDropdown('/a0/test.py', { closest: () => canvasRow });
assert.equal(fileBrowserStore.isDropdownOpen('/a0/test.py', canvasRow), true);
assert.equal(fileBrowserStore.isDropdownOpen('/a0/test.py', modalRow), false);
fileBrowserStore.toggleDropdown('/a0/test.py', { closest: () => modalRow });
assert.equal(fileBrowserStore.isDropdownOpen('/a0/test.py', canvasRow), false);
assert.equal(fileBrowserStore.isDropdownOpen('/a0/test.py', modalRow), true);
fileBrowserStore.closeDropdown();
assert.equal(fileBrowserStore.dropdownOwner, null);
fileBrowserStore.toggleDropdown('/a0/test.py', { closest: () => modalRow });
fileBrowserStore.destroy();
assert.equal(fileBrowserStore.dropdownOwner, null, 'closing Files releases its menu owner');
fileBrowserStore.openInSurface = async (...args) => opened.push(args);
await fileBrowserStore.openFileEditor(file('test.py'));
assert.equal(opened[0][1], 'editor');
const editorStore = (() => {
''' + editor + r'''
return store;
})();
const tab = { tab_id: 'tab', session_id: 'session', path: '/a0/test.py', extension: 'py', text: 'unsaved', dirty: true };
editorStore.tabs = [tab];
editorStore.session = tab;
editorStore.activeTabId = tab.tab_id;
editorStore.selectTab = id => assert.equal(id, tab.tab_id);
assert.equal(await editorStore.openSession({ path: tab.path }), tab, 'reopening must not fetch over unsaved text');
assert.equal(editorStore.isTextDocument(tab), true);
assert.equal(editorStore.canPreview(tab), false);
assert.equal(editorStore.canPreview({ extension: 'md' }), true);
assert.equal(editorStore.visibleTabs().length, 1);
assert.equal(editorStore.sourceEditorMode({ path: '/a0/probe.jsonl' }), 'ace/mode/json');
globalThis.ace = { require(name) {
  assert.equal(name, 'ace/ext/modelist');
  return { getModeForPath(path) { assert.equal(path, tab.path); return { mode: 'ace/mode/python' }; } };
}};
assert.equal(editorStore.sourceEditorMode(tab), 'ace/mode/python');
let prevented = 0, stopped = 0, previewSearches = 0;
const find = { ctrlKey: true, key: 'f', preventDefault() { prevented++; }, stopPropagation() { stopped++; } };
editorStore.openSearch = () => previewSearches++;
editorStore.viewMode = 'source';
editorStore.handleEditorKeydown(find);
assert.deepEqual([prevented, stopped, previewSearches], [0, 0, 0], 'source search belongs to ACE');
editorStore.viewMode = 'preview';
editorStore.handleEditorKeydown(find);
assert.deepEqual([prevented, stopped, previewSearches], [1, 1, 1], 'preview search consumes the event once');
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True)


def test_tool_results_refresh_open_code_but_preserve_dirty_text():
    source = Path('plugins/_editor/extensions/webui/set_messages_after_loop/sync-text-editor-results.js').read_text()
    source = re.sub(r'^import[^\n]*\n', '', source, flags=re.M).replace('export default ', '')
    script = r'''
import assert from 'node:assert/strict';
const calls = [];
const editorStore = { session: { path: '/a0/test.py' }, openSession: async payload => calls.push(payload) };
globalThis.document = { querySelector: () => ({}) };
globalThis.setTimeout = callback => callback();
''' + source + r'''
const result = id => ({ results: [{ args: { id, timestamp: Date.now(), kvps: { tool_name: 'text_editor', action: 'write', path: '/a0/test.py' } } }] });
await syncTextEditorResultsIntoOpenEditor(result('clean'));
assert.equal(calls.length, 1);
assert.equal(calls[0].path, '/a0/test.py');
editorStore.session.dirty = true;
await syncTextEditorResultsIntoOpenEditor(result('dirty'));
assert.equal(calls.length, 1);
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True)
