from pathlib import Path
import sys


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
    workdir_settings = read("webui", "components", "settings", "agent", "workdir.html")

    assert 'class="path-navigator"' in html
    assert 'class="nav-button back-button"' in html
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
    assert ".btn-new-item" in html
    assert "width: 2.8rem;" in html
    assert "height: 2.8rem;" in html
    assert ".path-navigator {\n      align-items: center;\n      flex-direction: row;" in html
    assert ".file-browser-toolbar {\n      align-items: center;\n      flex-direction: row;" in html
    assert ".file-search-shell {\n      flex: 1 1 auto;\n      min-width: 0;\n      width: auto;" in html
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
    assert 'new Set(["md", "txt"])' in store
    assert "pickerSelectedFiles()" in store
    assert "validatePickerFilename" in store
    assert "handleFileNameClick(file = {})" in store
    assert "fileSurfaceTarget(file) === \"editor\"" in store
    assert "isEditorSurface(file = {})" in store
    assert "canOpenInActionMenu(file = {})" in store

    assert "file-browser-picker-actions" in html
    assert "file-editor-open-action" in html
    assert 'aria-label="Open in Editor"' in html
    assert "picker-filename-input" in html
    assert "Open Selected" in store
    assert "Save Here" in store
    assert "$store.fileBrowser.confirmPicker()" in html
    assert "$store.fileBrowser.pickerSelectionLabel()" in html
    assert "$store.fileBrowser.isPickerMode()" in html
    assert "$store.fileBrowser.isTextOpenPicker()" in html
    assert "picker-confirm-button" in html

    assert "picker modes for Editor Open and Save As" in dox
    assert "Markdown or plain text files" in dox
    assert "Open in Editor action visible outside the overflow menu" in dox

    editor_button_index = html.index("file-editor-open-action")
    dropdown_menu_index = html.index('class="dropdown-menu file-actions-menu"')
    assert editor_button_index < dropdown_menu_index
    assert 'x-show="$store.fileBrowser.canOpenInActionMenu(file)"' in html


def test_file_browser_extract_and_editor_download_actions() -> None:
    browser_html = read("webui", "components", "modals", "file-browser", "file-browser.html")
    browser_store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    editor_html = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")

    assert 'x-show="!file.is_dir && $store.fileBrowser.isArchive(file.name)"' in browser_html
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

    assert '<div class="files-list" @scroll="$store.fileBrowser.closeDropdown()">' in html
    assert 'overflow: auto;' in html
    assert 'x-teleport="body"' in html
    assert 'class="dropdown-menu file-actions-menu"' in html
    assert ':style="$store.fileBrowser.dropdownStyle"' in html
    assert '@click.stop="$store.fileBrowser.toggleDropdown(file.path, $event.currentTarget)"' in html
    assert "getDropdownStyle(triggerElement)" in store
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
    assert 'x-destroy="$store.fileBrowser.onUnmount(xAttrs($el) || {})"' in html
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
