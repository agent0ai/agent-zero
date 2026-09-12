from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from helpers.file_browser import FileBrowser


def read(*parts: str) -> str:
    return PROJECT_ROOT.joinpath(*parts).read_text(encoding="utf-8")


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
    assert "Go to directory" in html
    assert "$store.fileBrowser.pathError" in html

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


def test_file_browser_compact_controls_and_narrow_layout_contract() -> None:
    html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    dox = read("webui", "components", "modals", "file-browser", "AGENTS.md")

    assert 'aria-label="New file"' in html
    assert 'title="New file"' in html
    assert 'aria-label="New folder"' in html
    assert 'title="New folder"' in html
    assert ">New File<" not in html
    assert ">New Folder<" not in html
    assert 'class="file-search-shell"' not in html
    assert 'class="file-tree-heading"' not in read("webui", "components", "modals", "file-browser", "file-tree.html")
    assert "file-status-bar" not in html
    assert html.index('aria-label="New file"') < html.index('aria-label="New folder"') < html.index('aria-label="Toggle file tree"')
    assert "btn-new-item" in html
    assert "width: 32px;" in html
    assert "height: 32px;" in html
    assert ".path-navigator {\n      align-items: center;\n      flex-direction: row;" in html
    assert ".path-navigator .nav-button-label {\n        display: none;" in html

    assert "container: file-browser / inline-size;" in html
    assert "@container file-browser (max-width: 620px)" in html
    assert "grid-template-columns: 2.25rem minmax(0, 1fr) minmax(4.25rem, max-content) 8rem;" in html
    assert ".file-cell-date,\n    .file-date {\n        display: none;" in html
    assert ".file-cell-size,\n    .file-size" not in html

    assert "hiding the Modified date column" in dox
    assert "New file and New folder controls icon-only" in dox


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

    assert '@scroll="$store.fileBrowser.closeDropdown()"' in html
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
    import re
    import subprocess

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
assert.deepEqual(store.preferences, {sortBy:'name', sortDirection:'asc', view:'list', treeShown:false, treeRoot:'/a0'});
store.preferences = {sortBy:'date', sortDirection:'desc', view:'icons', treeShown:true, treeRoot:'/a0/usr'};
await store.savePreferences();
store.browser.sortBy = 'name';
store.loadPreferences();
assert.equal(store.browser.sortBy, 'date');
assert.equal(store.browser.sortDirection, 'desc');
assert.equal(store.fileTree.shown, true);
assert.equal(store.preferences.view, 'icons');
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
assert.deepEqual(store.preferences, {sortBy:'name', sortDirection:'asc', view:'list', treeShown:false, treeRoot:'/a0'});
const sorted = store.sortFiles([{name:'b',is_dir:false},{name:'a',is_dir:false},{name:'z',is_dir:true}]);
assert.deepEqual(sorted.map(x=>x.name), ['z','a','b']);
'''
    subprocess.run(['node', '--input-type=module'], input=script, text=True, check=True)
