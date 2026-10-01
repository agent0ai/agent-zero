from pathlib import Path
import re
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from helpers.file_browser import FileBrowser


def read(*parts: str) -> str:
    return PROJECT_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def flat(text: str) -> str:
    """Collapse whitespace so CSS contract checks survive reformat-only edits."""
    return " ".join(text.split())


def run_store_check(checks: str) -> None:
    source = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    source = re.sub(r'^import\b[\s\S]*?;\n', '', source, flags=re.M)
    source = source.replace('export const store = createStore', 'const store = createStore')
    preamble = '''
import assert from 'node:assert/strict';
const window = globalThis;
const createStore = (_name, model) => model;
const createFileTree = () => ({ shown: false, follow: async () => {} });
const localStorage = { getItem: () => null, setItem: () => {} };
let surface = null;
const document = Object.assign(new EventTarget(), { querySelector: () => surface, querySelectorAll: () => [], activeElement: null });
const requestAnimationFrame = callback => callback();
const callJsonApi = async () => ({settings: {}});
const formatDateTime = () => '';
const openLatestSurface = async () => {};
const setupFloatingSurfaceModalChrome = () => () => {};
const settle = () => new Promise(setImmediate);
const listing = (path, entries = []) => ({ok:true, json:async () => ({data:{current_path:path, entries}})});
let fetcher = async url => listing(new URL(url, 'http://local').searchParams.get('path'));
const fetchApi = (...args) => fetcher(...args);
let modalCalls = 0;
let activeModal = null;
const modals = new Map();
const modalGuards = new Map();
window.isModalOpen = path => modals.has(path);
window.openModal = (path, guard) => { modalCalls++; activeModal = path; modalGuards.set(path, guard); return new Promise(resolve => modals.set(path, resolve)); };
window.ensureModalOpen = async path => { if (!modals.has(path)) return window.openModal(path); activeModal = path; return null; };
window.closeModal = path => { modals.get(path)?.(); modals.delete(path); document.dispatchEvent(new CustomEvent('modal-closed', {detail:{modalPath:path}})); };
window.toastFrontendError = () => {};
'''
    subprocess.run(['node', '--input-type=module'], input=preamble + source + checks,
                   text=True, check=True, timeout=15)


def test_picker_modal_visibility_and_inline_new_file():
    run_store_check('''
const modal = 'modals/file-browser/file-browser.html';
for (const host of [null, {hidden:true, closest:() => null}, {hidden:false, closest:() => null}]) {
  surface = host;
  store.browser.currentPath = '/original';
  let closed = false;
  const request = store.openSaveAsPicker('/target', {filename:'draft.txt'}).then(() => closed = true);
  await settle();
  assert.equal(modals.has(modal), true, 'external picker is visible regardless of canvas state');
  assert.equal(closed, false, 'open waits for close');
  assert.equal(store.pickerFilename, 'draft.txt');
  await store.cancelPicker();
  await request;
  assert.equal(store.pickerMode, '');
  assert.equal(store.browser.currentPath, host ? '/original' : '');
}
surface = null;
const request = store.open('/a');
await settle();
const count = modalCalls;
activeModal = 'editor';
let reusedClosed = false;
const reused = store.openTextPicker('/b').then(() => reusedClosed = true);
await settle();
assert.equal(modalCalls, count, 'reuse existing modal');
assert.equal(activeModal, modal, 'activate Files parked behind Editor');
assert.equal(reusedClosed, false, 'reuse preserves await-close contract');
store.beginSurfaceHandoff();
await store.openSurface('/b');
assert.equal(store.pickerMode, 'text-open', 'docking preserves picker state');
store.cancelSurfaceHandoff();
await store.cancelPicker();
await Promise.all([request, reused]);
void window.openModal(modal);
activeModal = 'editor';
let genericClosed = false;
const generic = store.openSaveAsPicker('/generic', {filename:'draft.txt'}).then(() => genericClosed = true);
await settle();
assert.equal(activeModal, modal, 'activate a parked Files modal opened by surface controls');
assert.equal(genericClosed, false, 'surface-opened modal still awaits close');
await store.cancelPicker();
await generic;
store.browser.currentPath = '/a';
store.history = ['/'];
await store.openNewFile();
assert.equal(modalCalls, count + 1, 'New file configures current footer');
assert.equal(store.pickerMode, 'save-as');
assert.deepEqual(store.history, ['/'], 'inline New file preserves navigation');
await store.cancelPicker();
assert.equal(store.pickerMode, '');
assert.equal(store.browser.currentPath, '/a');
''')


def test_surface_reopening_preserves_pending_writes():
    run_store_check('''
store.browser.currentPath = '/files';
let finishRename;
let renamed;
const target = {name:'note.md', path:'/files/note.md'};
store.beginRename(target, {
  performRename: () => new Promise(resolve => finishRename = resolve),
  onRenamed: result => { renamed = result; },
});
store.renameName = 'renamed.md';
const pendingRename = store.confirmRename();
assert.equal(await store.openSurface('/other'), false);
assert.equal(store.isRenaming, true);
assert.equal(store.renameTarget, target);
assert.equal(store.browser.currentPath, '/files');
assert.equal(store.beginNewFolder(), false, 'another write cannot start');
finishRename({refreshFiles:false});
await pendingRename;
assert.equal(renamed.path, '/files/renamed.md', 'completion callback survives reactivation');
assert.equal(store.isRenaming, false);

let finishSave;
store.configurePicker({
  pickerMode:'save-as', filename:'draft.md',
  onConfirm: () => new Promise(resolve => finishSave = resolve),
});
const pendingSave = store.confirmPicker();
assert.equal(await store.openSurface('/other'), false);
assert.equal(store.isBulkBusy, true);
assert.equal(store.pickerMode, 'save-as');
assert.equal(store.pickerFilename, 'draft.md');
assert.equal(store.browser.currentPath, '/files');
finishSave(false);
await pendingSave;
assert.equal(store.isBulkBusy, false);
assert.equal(await store.openSurface('/other'), true, 'normal opening resumes after the write');
assert.equal(store.browser.currentPath, '/other');
''')


def test_rename_forms_preserve_picker_and_target_directory():
    run_store_check('''
store.browser.currentPath = '/files';
store.browser.entries = [{name:'taken.md', path:'/files/taken.md'}];
store.beginRename({name:'note.md', path:'/files/note.md'});
assert.equal(store.renameInline, true);
assert.equal(modalCalls, 0);
store.renameName = 'taken.md';
await store.confirmRename();
assert.match(store.renameError, /already exists/);
store.closeRenameModal();
store.configurePicker({pickerMode:'save-as', filename:'draft.md', onConfirm:() => assert.fail('folder form must win')});
store.beginNewFolder();
await store.confirmPicker();
assert.equal(store.pickerFilename, 'draft.md');
let body;
fetcher = async (url, options) => {
  if (options) { body = JSON.parse(options.body); return listing('/files'); }
  return listing('/files');
};
store.renameName = 'new-folder';
await store.confirmRename();
assert.equal(body.parentPath, '/files');
assert.equal(store.renameInline, false);
assert.equal(store.pickerFilename, 'draft.md', 'return to Save As draft after creating folder');
store.resetPickerState();
let finishRename;
store.openRenameModal({name:'note.md',path:'/external/note.md'}, {currentPath:'/external', performRename: () => new Promise(resolve => finishRename = resolve)});
assert.equal(modalCalls, 1);
assert.equal(store.renameInline, false);
assert.equal(store.browser.currentPath, '/files', 'external rename must not retarget Files');
assert.deepEqual(store.renameEntries, [], 'unrelated listing cannot reject external name');
store.renameName = 'renamed.md';
const pendingRename = store.confirmRename();
assert.equal(modalGuards.get('modals/file-browser/rename-modal.html')(), false, 'pending rename blocks X/Escape');
store.closeRenameModal();
assert.equal(store.isRenaming, true, 'cancel cannot clear a pending operation');
finishRename({refreshFiles:false});
await pendingRename;
assert.equal(modalGuards.get('modals/file-browser/rename-modal.html')(), true);
store.resetRenameState();
store.openNewFolderModal();
assert.equal(modalCalls, 2);
assert.equal(store.renameMode, 'create-folder');
store.closeRenameModal();
''')
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    assert 'x-if="$store.fileBrowser.isSaveAsPicker() && !$store.fileBrowser.renameInline"' in html
    assert 'container: file-browser-footer / inline-size;' in html
    assert '@container file-browser-footer (max-width: 620px)' in html


def test_autocomplete_root_paths_and_cancellation():
    run_store_check('''
let requested;
fetcher = async url => { requested = new URL(url, 'http://local').searchParams.get('path'); return listing(requested, [{name:'child', path:requested+'/child', is_dir:true}]); };
for (const [input, parent] of [['/','/'], ['a0/','/a0'], ['/a0/us','/a0'], ['/@connections/','/@connections']]) {
  store.pathInput = input;
  await store.updatePathSuggestions();
  assert.equal(requested, parent);
}
const originalTimer = globalThis.setTimeout;
globalThis.setTimeout = () => 123;
for (const cancel of [() => store.resetPathInput(), () => store.queuePathSuggestions(), () => store.hidePathSuggestions(), () => store.destroy()]) {
  let finish;
  fetcher = () => new Promise(resolve => finish = resolve);
  store.pathInput = '/a0/';
  const pending = store.updatePathSuggestions();
  cancel();
  finish(listing('/a0', [{name:'stale', path:'/a0/stale', is_dir:true}]));
  await pending;
  assert.deepEqual(store.pathSuggestions, [], 'cancelled request cannot resurrect results');
}
globalThis.setTimeout = originalTimer;
fetcher = async () => ({ok:false, json:async () => ({error:'denied'})});
store.pathInput = '/';
await store.updatePathSuggestions();
assert.deepEqual(store.pathSuggestions, []);
store.browser.currentPath = '/@connections/ssh/0123456789abcdef0123456789abcdef/docs';
assert.deepEqual(store.pathCrumbs().map(c => c.path), ['/', '/@connections', '/@connections/ssh/0123456789abcdef0123456789abcdef', '/@connections/ssh/0123456789abcdef0123456789abcdef/docs']);
store.pathSuggestions = [{name:'one',path:'a/one'}, {name:'two',path:'a/two'}];
store.pathSuggestionIndex = 0;
store.movePathSuggestion(-1);
assert.equal(store.activePathSuggestion.name, 'two');
fetcher = async url => listing(new URL(url, 'http://local').searchParams.get('path'));
assert.equal(store.selectPathSuggestion(), true);
assert.equal(store.pathInput, '/a/two/', 'Tab accepts active relative suggestion as an absolute child directory');
await settle();
store.pathInput = '/typed';
store.pathSuggestions = [{name:'other',path:'/other'}];
await store.submitPath();
assert.equal(store.browser.currentPath, '/typed', 'Enter submits typed input instead of selected suggestion');
store.browser.currentPath = '$WORK_DIR';
assert.deepEqual(store.pathCrumbs(), [{name:'/',path:'/'}], 'startup sentinel is not a directory crumb');
''')


def test_autocomplete_respects_connection_roots():
    run_store_check('''
let requested;
fetcher = async url => {
  requested = new URL(url, 'http://local').searchParams.get('path');
  return listing(requested, [{name:'child', path:requested+'/child', is_dir:true}]);
};
const id = '0123456789abcdef0123456789abcdef';
for (const root of [`/@connections/host/${id}`, `/@connections/ssh/${id}`, `/@ssh/${id}`]) {
  for (const input of [root, root+'/', root+'/ch']) {
    store.pathInput = input;
    await store.updatePathSuggestions();
    assert.equal(requested, root, 'suggestions stay inside the connection');
    assert.deepEqual(store.pathSuggestions, [{name:'child', path:root+'/child'}]);
  }
  store.pathInput = root+'/child/';
  await store.updatePathSuggestions();
  assert.equal(requested, root+'/child', 'nested folders remain browsable');
}
for (const input of ['/@connections/ssh', '/@connections/ssh/', '/@connections/ssh/0123', '/@connections/ssh/0123/', '/@ssh/0123/']) {
  requested = null;
  store.pathSuggestions = [{name:'stale',path:'/stale'}];
  store.pathInput = input;
  await store.updatePathSuggestions();
  assert.equal(requested, null, 'do not query namespaces or incomplete connection IDs');
  assert.deepEqual(store.pathSuggestions, []);
}
''')


def test_directory_requests_and_history_only_commit_success():
    run_store_check('''
store.browser.currentPath = '/a';
store.forwardHistory = ['/forward'];
fetcher = async () => ({ok:false,json:async () => ({error:'denied'})});
await store.navigateToFolder('/denied');
assert.equal(store.browser.currentPath, '/a');
assert.deepEqual(store.history, []);
assert.deepEqual(store.forwardHistory, ['/forward']);
let finish;
fetcher = () => new Promise(resolve => finish = resolve);
const pending = store.fetchFiles('/old');
fetcher = async () => listing('/new');
await store.fetchFiles('/new');
finish(listing('/old'));
await pending;
assert.equal(store.browser.currentPath, '/new', 'latest request wins');
fetcher = () => new Promise(resolve => finish = resolve);
const closing = store.fetchFiles('/late');
store.destroy();
finish(listing('/late'));
await closing;
assert.equal(store.browser.currentPath, '', 'late response cannot resurrect a closed browser');
const docking = store.fetchFiles('/docked');
store.beginSurfaceHandoff();
store.onUnmount();
finish(listing('/docked'));
await docking;
assert.equal(store.browser.currentPath, '/docked', 'docking does not cancel the shared directory load');
''')


def test_file_browser_remember_last_directory_defaults_enabled() -> None:
    settings_source = read("helpers", "settings.py")

    assert "file_browser_remember_last_directory: bool" in settings_source
    assert "file_browser_remember_last_directory=get_default_value(" in settings_source
    assert '"file_browser_remember_last_directory",\n            True,' in settings_source


def test_file_browser_editable_path_bar_and_remembered_directory_contract() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    workdir_settings = read("webui", "components", "settings", "file-browser", "file-browser-settings.html")

    assert 'class="path-navigator surface-toolbar"' in html
    assert 'class="nav-button back-button surface-control"' in html
    assert 'class="text-button back-button"' not in html
    assert ".nav-button:focus-visible" in html
    assert ".nav-button .material-symbols-outlined" in html
    assert 'class="nav-button-label">Up</span>' in html
    assert "flex-direction: column;" in html
    assert ".nav-button-label" in html
    assert 'x-model="$store.fileBrowser.pathInput"' in html
    assert '@submit.prevent="$store.fileBrowser.submitPath()"' in html
    assert '$store.fileBrowser.pathError' in html

    assert "FILE_BROWSER_LAST_DIRECTORY_STORAGE_KEY" in store
    assert 'callJsonApi("settings_get", null)' in store
    assert "file_browser_remember_last_directory" in store
    assert "getRememberedDirectory()" in store
    assert "rememberCurrentDirectory(this.browser.currentPath)" in store
    assert "clearRememberedDirectory()" in store
    assert "scheduleMountedDefaultLoad()" in store
    assert 'this.browser.currentPath = "";' in store
    assert 'this.browser.parentPath = "";' in store
    assert 'const requestedPath = this.normalizeOpeningPath(path) || "$WORK_DIR";' in store
    assert "`/get_work_dir_files?path=${encodeURIComponent(requestedPath)}`" in store
    assert 'result.current_path || (requestedPath === "$WORK_DIR" ? "/a0" : requestedPath)' in store

    explicit_path_index = store.index("const explicitPath = this.normalizeOpeningPath")
    remembered_path_index = store.index("const rememberedPath = !explicitPath")
    assert explicit_path_index < remembered_path_index

    assert "Remember last file browser location" in workdir_settings
    assert "$store.settings.settings.file_browser_remember_last_directory" in workdir_settings


def test_file_browser_path_controls_preserve_accessibility_and_cleanup():
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    assert 'aria-label="Edit directory path"' in html
    assert 'class="path-edit-toggle"' in html
    assert '@keydown.escape.stop.prevent=' in html
    assert 'x-destroy="$el._pinResizeObserver?.disconnect()"' in html
    assert 'x-destroy="$el._crumbFitObserver.disconnect()"' in html
    assert ':inert="$store.fileBrowser.isLoading || $store.fileBrowser.isRenaming || $store.fileBrowser.isBulkBusy"' in html


def test_file_browser_compact_controls_and_narrow_layout_contract() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    dox = read("webui", "components", "modals", "file-browser", "AGENTS.md")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")

    assert 'aria-label="New file"' in html
    assert 'title="New file"' in html
    assert 'aria-label="New folder"' in html
    assert 'title="New folder"' in html
    assert 'aria-label="Create new"' in html
    assert html.count('btn-new-item') == 1
    assert ">New File<" not in html
    assert ">New Folder<" not in html
    assert 'class="file-search-shell"' not in html
    assert 'class="file-tree-heading"' not in read("webui", "components", "modals", "file-browser", "file-tree.html")
    assert "file-status-bar" not in html
    assert html.index('aria-label="New file"') < html.index('aria-label="New folder"') < html.index('aria-label="Toggle file tree"')
    assert "btn-new-item" in html
    assert "width: 32px;" in html
    assert "height: 32px;" in html
    assert ".path-navigator { align-items: center; flex-direction: row;" in flat(html)
    assert ".path-navigator .nav-button-label { display: none;" in flat(html)

    assert "container: file-browser / inline-size;" in html
    assert "@container file-browser (max-width: 620px)" in html
    assert "grid-template-columns: 2.25rem minmax(0, 1fr) minmax(4.25rem, max-content) 8rem;" in flat(html)
    assert ".file-cell-date, .file-date { display: none;" in flat(html)
    assert ".file-cell-size,\n    .file-size" not in html

    assert "hiding the Modified date column" in dox
    assert "One Create new (+) control owns both create actions" in dox


def test_file_browser_editor_picker_modes_have_primary_footer_actions() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    dox = read("webui", "components", "modals", "file-browser", "AGENTS.md")

    assert "PICKER_MODE_TEXT_OPEN" in store
    assert "PICKER_MODE_SAVE_AS" in store
    assert "openTextPicker" in store
    assert "openSaveAsPicker" in store
    assert "isEditableFile(file = {})" in store
    assert "pickerSelectedFiles()" in store
    assert "validatePickerFilename" in store
    assert "handleFileNameClick(file = {})" in store
    assert "fileSurfaceTarget(file) === \"editor\"" in store
    assert "isEditorSurface(file = {})" in store
    assert "canOpenInActionMenu(file = {})" in store

    assert "file-browser-picker-actions" in html
    assert "file-editor-open-action" not in html
    assert "picker-filename-input" in html
    assert "Open Selected" in store
    assert "Save Here" in store
    assert "$store.fileBrowser.confirmPicker()" in html
    assert "picker-selection-label" not in html
    assert "$store.fileBrowser.isPickerMode()" in html
    assert "$store.fileBrowser.isTextOpenPicker()" in html
    assert "picker-confirm-button" in html

    assert "picker modes for Editor Open and Save As" in dox
    assert "text or code files" in dox
    assert "Keep Edit inside the overflow menu" in dox

    dropdown_menu_index = html.index('class="dropdown-menu file-actions-menu"')
    assert html.index('class="dropdown file-actions-dropdown"') < html.index('title="Download file"') < html.index('title="Delete item"')
    assert '<x-extension id="file-browser-actions-menu"></x-extension>' in html[dropdown_menu_index:]
    assert 'file-browser-actions-menu/*.html' in dox
    edit_button = html[dropdown_menu_index:html.index('<span>Edit</span>')]
    assert 'class="dropdown-item"' in edit_button
    assert 'x-show="$store.fileBrowser.isEditableFile(file)"' in edit_button
    assert '@click="$store.fileBrowser.openFileEditor(file)"' in edit_button
    assert 'always_enabled: true' in read("plugins", "_editor", "plugin.yaml")
    assert 'x-show="$store.fileBrowser.canOpenInActionMenu(file)"' in html


def test_file_browser_extract_and_editor_download_actions() -> None:
    browser_html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    browser_store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    editor_html = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")

    assert 'x-show="!file.is_dir && !$store.fileBrowser.isRemote(file.path) && $store.fileBrowser.isArchive(file.name)"' in browser_html
    assert '$store.fileBrowser.extractArchive(file)' in browser_html
    assert "ARCHIVE_SUFFIXES" in browser_store
    assert 'fetchApi("/extract_work_dir_archive"' in browser_store
    assert "async extractArchive(file = {})" in browser_store
    assert "<span>Extract</span>" in browser_html
    assert "downloadActiveFile()" in editor_store
    assert "$store.editor.downloadActiveFile()" in editor_html
    assert "<span>Download</span>" in editor_html


def test_file_browser_dropdown_escapes_scroll_container_and_header_is_opaque() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")

    assert '@scroll="$store.fileBrowser.closeDropdown(); closeMenu()"' in html
    assert 'const surfaceActive = Boolean(document.querySelector(".file-browser-root.is-surface"));' in store
    assert 'await this.openSurface(retainedPath);' in store
    assert 'overflow: auto;' in html
    assert 'x-teleport="body"' in html
    assert 'class="dropdown-menu file-actions-menu"' in html
    assert ':style="$store.fileBrowser.dropdownStyle"' in html
    assert '@click.stop="$store.fileBrowser.toggleDropdown(file.path, $event.currentTarget)"' in html
    assert "getDropdownStyle(triggerElement," in store
    assert 'position: "fixed"' in store
    assert 'zIndex: "6000"' in store

    assert "var(--secondary-bg)" not in html
    assert "var(--border-color)" not in html
    assert "var(--text-secondary)" not in html
    assert "background: color-mix(in srgb, var(--color-panel) 88%, var(--color-background) 12%);" in html
    assert "border-bottom: 1px solid var(--color-border);" in html


def test_file_browser_empty_api_path_uses_default_workdir_contract() -> None:
    api_source = read("api", "get_work_dir_files.py")
    api_dox = read("api", "get_work_dir_files.py.dox.md")

    assert 'current_path = request.args.get("path", "") or "$WORK_DIR"' in api_source
    assert 'current_path = "/a0"' in api_source
    assert "Empty `path` requests and explicit `$WORK_DIR` requests resolve" in api_dox


def test_file_browser_is_registered_as_right_canvas_surface() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    surfaces = read("webui", "js", "surfaces.js")
    register = read("extensions", "webui", "right_canvas_register_surfaces", "register-files.js")
    panel = read("extensions", "webui", "right-canvas-panels", "files-panel.html")
    input_store = read("webui", "components", "chat", "input", "input-store.js")
    welcome_store = read("webui", "components", "welcome", "welcome-store.js")

    assert 'id: "files"' in surfaces
    assert 'title: "Files"' in surfaces
    assert 'modalPath: "modals/file-browser/file-browser.html"' in surfaces
    assert 'await store.openSurface(payload.path || payload.filePath || payload.directory || "")' in surfaces
    assert 'data-surface-id="files"' in html
    assert 'data-surface-modal-path="modals/file-browser/file-browser.html"' in html
    assert 'class="surface-modal file-browser-modal modal-no-backdrop"' in html
    assert 'class="file-browser-modal-body"' in html
    assert 'x-create="$store.fileBrowser.onMount($el, xAttrs($el) || {})"' in html
    assert 'x-destroy="$store.fileBrowser.onUnmount($el)"' in html
    assert ".modal-inner.file-browser-modal" in html
    assert "resize: both" in html
    assert "openSurface(path" in store
    assert "setupFloatingSurfaceModalChrome" in store
    assert 'focusButtonClass: "file-browser-modal-focus-button"' in store
    assert "beginSurfaceHandoff()" in store
    assert "finishSurfaceHandoff()" in store
    assert 'id: "files"' in register
    assert "fileBrowserStore.openSurface" in register
    assert 'data-surface-id="files"' in panel
    assert 'path="modals/file-browser/file-browser.html" mode="canvas"' in panel
    assert 'openLatestSurface("files"' in input_store
    assert 'import { store as fileBrowserStore } from "/components/modals/file-browser/file-browser-store.js";' in welcome_store
    assert "fileBrowserStore.open()" in welcome_store
    assert "chatInputStore.browseFiles" not in welcome_store


def test_file_browser_reports_missing_directory(tmp_path: Path) -> None:
    missing_directory = tmp_path / "missing"

    result = FileBrowser().get_files(str(missing_directory))

    assert result["entries"] == []
    assert result["current_path"] == str(missing_directory)
    assert result["error"] == "Directory not found"


def test_file_browser_moves_selected_items_without_overwriting_or_self_nesting(tmp_path: Path) -> None:
    browser = FileBrowser()
    browser.base_dir = tmp_path
    source_file = tmp_path / "note.md"
    source_folder = tmp_path / "skills"
    destination = tmp_path / "archive"
    source_file.write_text("hello", encoding="utf-8")
    source_folder.mkdir()
    destination.mkdir()

    moved = browser.move_items(["note.md", "skills"], "archive")

    assert moved == [str(destination / "note.md"), str(destination / "skills")]
    assert (destination / "note.md").read_text(encoding="utf-8") == "hello"
    assert (destination / "skills").is_dir()

    collision = tmp_path / "collision.md"
    collision.write_text("source", encoding="utf-8")
    (destination / "collision.md").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        browser.move_items(["collision.md"], "archive")
    assert collision.read_text(encoding="utf-8") == "source"
    assert (destination / "collision.md").read_text(encoding="utf-8") == "keep"

    nested = destination / "skills" / "nested"
    nested.mkdir()
    with pytest.raises(ValueError, match="cannot be moved into itself"):
        browser.move_items(["archive/skills"], "archive/skills/nested")


def test_file_browser_drag_and_drop_contract() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    attachments = read("webui", "components", "chat", "attachments", "attachmentsStore.js")
    api = read("api", "rename_work_dir_file.py")

    assert ':draggable="!$store.fileBrowser.isPickerMode() && !$store.fileBrowser.isBulkBusy"' in html
    assert "$store.fileBrowser.dropItems(file.path, file.name, $event)" in html
    assert "$store.fileBrowser.dropItems($store.fileBrowser.browser.parentPath, 'parent folder', $event)" in html
    start_drag = store[store.index("  startDrag("):store.index("  isDraggingPath(")]
    assert "this.clearSelection()" not in start_drag
    assert "file.selected = true" not in start_drag
    assert ": [file.path]" in start_drag
    assert "decorateEntries(data.data?.entries || [], selectedPaths)" in store
    assert "application/x-agent-zero-files" in store
    assert 'action: "move"' in store
    assert 'fetchApi("/rename_work_dir_file"' in store
    assert 'if action == "move":' in api
    assert 'isExternalFileDrag(event)' in attachments
    assert 'includes("Files")' in attachments


def test_file_browser_preferences_validate_and_restore_defaults():
    source = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    source = re.sub(r'^import\b[\s\S]*?;\n', '', source, flags=re.M)
    source = source.replace('export const store = createStore', 'const store = createStore')
    script = '''
import assert from 'node:assert/strict';
const window = globalThis;
const createStore = (_name, model) => model;
const createFileTree = () => ({ shown: false, follow: async () => {} });
let saved = '{}';
const localStorage = { getItem: () => saved, setItem: (_key, value) => saved = value };
''' + source + '''
store.loadPreferences();
assert.deepEqual(store.preferences, {sortBy:'name', sortDirection:'asc', view:'list', treeShown:false, treeRoot:'/a0', pathBar:'buttons'});
store.preferences = {sortBy:'date', sortDirection:'desc', view:'icons', treeShown:true, treeRoot:'/a0/usr', pathBar:'raw'};
await store.savePreferences();
store.browser.sortBy = 'name';
store.loadPreferences();
assert.equal(store.browser.sortBy, 'date');
assert.equal(store.browser.sortDirection, 'desc');
assert.equal(store.fileTree.shown, true);
assert.equal(store.preferences.view, 'icons');
assert.equal(store.preferences.pathBar, 'raw');
assert.equal(store.preferences.treeRoot, '/a0/usr');
await store.saveTreeRoot(' /a0//usr/ ');
assert.equal(JSON.parse(saved).treeRoot, '/a0/usr');
await store.saveTreeRoot('/');
assert.equal(JSON.parse(saved).treeRoot, '/', 'filesystem root remains an explicit choice');
for (const path of ['', 'usr', '/a0/../usr', '/a0/./usr', null, 42]) {
  await store.saveTreeRoot(path);
  assert.equal(JSON.parse(saved).treeRoot, '/', 'invalid input does not replace the saved root');
  saved = JSON.stringify({treeRoot:path});
  store.loadPreferences();
  assert.equal(store.preferences.treeRoot, '/a0', 'invalid stored root falls back safely');
  await store.saveTreeRoot('/');
}

saved = '{"sortBy":"invalid","view":"invalid","treeShown":"true"}';
store.loadPreferences();
assert.deepEqual(store.preferences, {sortBy:'name', sortDirection:'asc', view:'list', treeShown:false, treeRoot:'/a0', pathBar:'buttons'});
const sorted = store.sortFiles([{name:'b',is_dir:false},{name:'a',is_dir:false},{name:'z',is_dir:true}]);
assert.deepEqual(sorted.map(x=>x.name), ['z','a','b']);
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True)


def test_file_browser_history_back_forward_stack_behavior():
    source = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    source = re.sub(r'^import\b[\s\S]*?;\n', '', source, flags=re.M)
    source = source.replace('export const store = createStore', 'const store = createStore')
    script = '''
import assert from 'node:assert/strict';
const window = globalThis;
const createStore = (_name, model) => model;
const createFileTree = () => ({ shown: false, follow: async () => {} });
let saved = '{}';
const localStorage = { getItem: () => saved, setItem: (_key, value) => saved = value };
window.toastFrontendError = () => {};
const dirs = {
  '/a': { current_path: '/a', parent_path: '', entries: [{name:'b', path:'/a/b', is_dir:true}] },
  '/a/b': { current_path: '/a/b', parent_path: '/a', entries: [{name:'c', path:'/a/b/c', is_dir:true}] },
  '/a/b/c': { current_path: '/a/b/c', parent_path: '/a/b', entries: [] },
};
const failPaths = new Set();
const fetchApi = async (url) => {
  const path = decodeURIComponent(url.split('path=')[1]);
  return { ok: !failPaths.has(path), json: async () => ({ data: dirs[path] }) };
};
''' + source + '''
await store.fetchFiles('/a');
await store.navigateToFolder('/a/b');
await store.navigateToFolder('/a/b/c');
assert.equal(store.browser.currentPath, '/a/b/c');
assert.deepEqual(store.history, ['/a', '/a/b']);
assert.deepEqual(store.forwardHistory, []);

await store.navigateBack();
assert.equal(store.browser.currentPath, '/a/b');
assert.deepEqual(store.history, ['/a']);
assert.deepEqual(store.forwardHistory, ['/a/b/c']);

await store.navigateBack();
assert.equal(store.browser.currentPath, '/a');
assert.deepEqual(store.history, []);
assert.deepEqual(store.forwardHistory, ['/a/b/c', '/a/b']);

await store.navigateForward();
assert.equal(store.browser.currentPath, '/a/b');
assert.deepEqual(store.history, ['/a']);
assert.deepEqual(store.forwardHistory, ['/a/b/c']);

await store.navigateToFolder('/a/b/c');
assert.equal(store.browser.currentPath, '/a/b/c');
assert.deepEqual(store.history, ['/a', '/a/b']);
assert.deepEqual(store.forwardHistory, []);

await store.navigateBack();
assert.equal(store.browser.currentPath, '/a/b');
failPaths.add('/a');
await store.navigateBack();
assert.equal(store.browser.currentPath, '/a/b');
assert.deepEqual(store.history, ['/a']);
assert.deepEqual(store.forwardHistory, ['/a/b/c']);
failPaths.delete('/a');

assert.equal(store.history.length === 0, false);
store.history = [];
store.forwardHistory = [];
assert.equal(store.history.length, 0);
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True)
