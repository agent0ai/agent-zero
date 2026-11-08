from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return (PROJECT_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def test_modals_are_generic_and_surfaces_own_live_surface_paths():
    modals_js = read("webui", "js", "modals.js")
    modals_css = read("webui", "css", "modals.css")
    surfaces_js = read("webui", "js", "surfaces.js")
    surfaces_css = read("webui", "css", "surfaces.css")

    for forbidden in (
        "right-canvas-store",
        "/plugins/_browser",
        "/plugins/_office",
        "/plugins/_desktop",
        "SINGLE_VISIBLE_MODAL_SURFACE_PATHS",
        "data-canvas",
        "surface-window",
    ):
        assert forbidden not in modals_js

    assert "modalStack" in modals_js
    assert 'const backdrop = document.createElement("div")' in modals_js
    assert "backdrop.style.display" in modals_js
    assert "modalSurfaceMetadata" not in modals_js
    assert "modal-content-loaded" in modals_js
    assert "modal.returnFocus = returnFocus" in modals_js
    assert "modal.returnFocus?.isConnected" in modals_js
    assert ".surface-floating" not in modals_css
    assert ".surface-switcher" not in modals_css

    assert "CORE_SURFACES" in surfaces_js
    assert "modalSurfaceMetadata" in surfaces_js
    assert "closeSurfaceGroupModals" in surfaces_js
    assert 'id: "browser"' in surfaces_js
    assert 'id: "desktop"' in surfaces_js
    assert 'id: "editor"' in surfaces_js
    assert "/plugins/_browser/webui/main.html" in surfaces_js
    assert "/plugins/_desktop/webui/main.html" in surfaces_js
    assert "/plugins/_editor/webui/main.html" in surfaces_js
    assert "LEGACY_SURFACE_IDS" in surfaces_js
    assert '["office", "desktop"]' not in surfaces_js
    assert "htmlDataset.surfaceId" in surfaces_js
    assert "htmlDataset.canvasSurface" in surfaces_js
    assert ".surface-modal" in surfaces_css
    assert ".surface-floating" in surfaces_css
    assert ".surface-resize-handle" in surfaces_css
    assert ".surface-switcher" in surfaces_css
    assert "surface-window" not in surfaces_js + surfaces_css


def test_right_canvas_registers_desktop_and_keeps_editor_controls():
    canvas_store = read("webui", "components", "canvas", "right-canvas-store.js")
    desktop_register = read(
        "plugins",
        "_desktop",
        "extensions",
        "webui",
        "surfaces_register",
        "register-desktop.js",
    )
    desktop_panel = read(
        "plugins",
        "_desktop",
        "extensions",
        "webui",
        "right-canvas-panels",
        "desktop-panel.html",
    )

    right_canvas_css = read("webui", "components", "canvas", "right-canvas.css")
    desktop_web_panel = read("plugins", "_desktop", "webui", "desktop-panel.html")
    editor_register = read(
        "plugins",
        "_editor",
        "extensions",
        "webui",
        "right_canvas_register_surfaces",
        "register-editor.js",
    )
    editor_panel = read(
        "plugins",
        "_editor",
        "extensions",
        "webui",
        "right-canvas-panels",
        "editor-panel.html",
    )
    editor_main = read("plugins", "_editor", "webui", "main.html")
    editor_web_panel = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")
    editor_preview = read("plugins", "_editor", "webui", "editor-preview.js")
    safe_markdown = read("webui", "js", "safe-markdown.js")

    assert 'await callJsExtensions("surfaces_register", this);' in canvas_store
    assert 'await callJsExtensions("right_canvas_register_surfaces", this);' in canvas_store
    assert "migratePersistedSurfaceState" in canvas_store
    assert "normalizeSurfaceId" in canvas_store
    assert "const saved = migratePersistedSurfaceState(JSON.parse" in canvas_store
    assert 'id: "desktop"' in desktop_register
    assert 'modalPath: "/plugins/_desktop/webui/main.html"' in desktop_register
    assert 'id: "editor"' in editor_register
    assert 'title: "Editor"' in editor_register
    assert 'order: 30' in editor_register
    assert 'modalPath: "/plugins/_editor/webui/main.html"' in editor_register
    assert 'data-surface-id="desktop"' in desktop_panel
    assert "isSurfaceVisible('desktop')" in desktop_panel
    assert 'data-surface-id="editor"' in editor_panel
    assert "isSurfaceVisible('editor')" in editor_panel
    assert 'data-surface-id="editor"' in editor_main
    assert 'data-surface-modal-path="/plugins/_editor/webui/main.html"' in editor_main
    assert "editor-source-editor" in editor_web_panel
    assert "data-editor-source" in editor_web_panel
    assert "editor-tabs" in editor_web_panel
    assert "editor-new-tab" in editor_web_panel
    assert 'aria-label="New Markdown"' in editor_web_panel
    assert "editor-close-confirm" in editor_web_panel
    assert "Save &amp; Close" in editor_web_panel
    assert "Close All" in editor_web_panel
    assert "editor-document-header" not in editor_web_panel
    assert "editor-document-save-button" not in editor_web_panel
    assert "data-editor-ace" in editor_web_panel
    assert "data-editor-preview" in editor_web_panel
    assert "data-editor-preview-source" in editor_web_panel
    assert "editor-mode-toggle" in editor_web_panel
    assert "editor-search-bar" in editor_web_panel
    assert "editor-preview-title" in editor_web_panel
    assert "editor-preview-page-editor" in editor_web_panel
    assert "editor-table-wrap" in editor_web_panel
    assert "editor-empty" in editor_web_panel
    assert "runNewMenuAction('open')" in editor_web_panel
    assert "runNewMenuAction('markdown')" in editor_web_panel
    assert "closeAllFiles" in editor_store
    assert "confirmPendingClose" in editor_store
    assert "ensureInitialMarkdownFile" not in editor_store
    assert "_initialCreatePromise" not in editor_store
    assert "startPreviewEdit" in editor_store
    assert "applyPreviewEdit" in editor_store
    assert "previewEditDirty" in editor_store
    assert "replacePageMarkdown" in editor_store
    assert "enhanceTaskLists" in editor_store
    assert "togglePreviewTask" in editor_store
    assert 'input[type="checkbox"]' in editor_store
    assert "renderEditorPreviewMarkdown" in editor_store
    assert "buildMarkdownPages" in editor_store
    assert "PAGE_HEADING_RE" not in editor_preview
    assert "markdown: source" in editor_preview
    assert "hydrateActiveSession" in editor_store
    assert "refreshSourceEditorLayout" in editor_store
    assert "editor.resize?.(true)" in editor_store
    assert "openSearch" in editor_store
    assert "handlePreviewClick" in editor_store
    assert "ace.edit" in editor_store
    assert "showGutter: true" in editor_store
    assert ".editor-ace .ace_gutter" not in editor_web_panel
    assert ".editor-ace .ace_scroller" not in editor_web_panel
    assert "globalThis.confirm" not in editor_store
    assert ".editor-toolbar" in editor_web_panel
    assert "overflow: visible;" in editor_web_panel
    assert "z-index: 10000;" in editor_web_panel
    assert "renderSafeMarkdown" in editor_preview
    assert "prepareFootnotes" in editor_preview
    assert "resolveDocumentRelativePath" in editor_preview
    assert "allowDataImages: true" in editor_preview
    assert "allowLatex: true" in editor_preview
    assert "html = sanitizeHtml(html, options);" in safe_markdown
    assert ".right-canvas-header" in right_canvas_css
    assert "overflow: visible;" in right_canvas_css
    assert ".right-canvas-toolbar" in right_canvas_css
    assert not (PROJECT_ROOT / "plugins" / "_office" / "extensions" / "webui" / "right_canvas_register_surfaces" / "register-office.js").exists()
    assert not (PROJECT_ROOT / "plugins" / "_office" / "extensions" / "webui" / "right-canvas-panels" / "office-panel.html").exists()


def test_browser_surface_restores_focus_mode_chrome():
    browser_store = read("plugins", "_browser", "webui", "browser-store.js")
    browser_panel = read("plugins", "_browser", "webui", "browser-panel.html")

    assert "browser-modal-focus-button" in browser_store
    assert "is-focus-mode" in browser_store
    assert "fullscreen_exit" in browser_store
    assert "Focus mode" in browser_store
    assert "Restore size" in browser_store
    assert ".modal-inner.browser-modal.is-focus-mode" in browser_panel


def test_files_and_editor_surface_modals_have_draggable_focus_chrome():
    surfaces_js = read("webui", "js", "surfaces.js")
    surfaces_css = read("webui", "css", "surfaces.css")
    file_store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")
    file_modal = read("webui", "components", "modals", "file-browser", "file-browser.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")
    editor_panel = read("plugins", "_editor", "webui", "editor-panel.html")

    assert "setupFloatingSurfaceModalChrome" in surfaces_js
    assert "is-draggable-surface-modal" in surfaces_js
    assert "surface-modal-focus-button" in surfaces_js
    assert "fullscreen_exit" in surfaces_js
    assert "Focus mode" in surfaces_js
    assert "Restore size" in surfaces_js
    assert ".modal-inner.surface-modal.is-draggable-surface-modal .modal-header" in surfaces_css
    assert "cursor: move" in surfaces_css
    assert ".surface-modal-focus-button.is-active" in surfaces_css

    assert "setupFloatingSurfaceModalChrome" in file_store
    assert 'focusButtonClass: "file-browser-modal-focus-button"' in file_store
    assert ".modal-inner.file-browser-modal" in file_modal
    assert "resize: both" in file_modal

    assert "setupFloatingSurfaceModalChrome" in editor_store
    assert 'focusButtonClass: "editor-modal-focus-button"' in editor_store
    assert "onBoundsChange: () => this.refreshSourceEditorLayout()" in editor_store
    assert "editor.resize?.(true)" in editor_store
    assert ".modal-inner.editor-modal.is-focus-mode" in editor_panel










def test_editor_plugin_owns_markdown_sessions_and_active_context_extras():
    editor_plugin = PROJECT_ROOT / "plugins" / "_editor"
    assert (editor_plugin / "plugin.yaml").exists()
    assert (editor_plugin / "api" / "editor_session.py").exists()
    assert (editor_plugin / "api" / "ws_editor.py").exists()

    editor_session = read("plugins", "_editor", "helpers", "markdown_sessions.py")
    editor_api = read("plugins", "_editor", "api", "editor_session.py")
    editor_ws = read("plugins", "_editor", "api", "ws_editor.py")
    editor_context = read("plugins", "_editor", "helpers", "open_files_context.py")
    editor_result_sync = read(
        "plugins",
        "_editor",
        "extensions",
        "webui",
        "set_messages_after_loop",
        "sync-text-editor-results.js",
    )
    editor_extras = read(
        "plugins",
        "_editor",
        "extensions",
        "python",
        "message_loop_prompts_after",
        "_55_include_editor_open_files.py",
    )



    assert "context_id: str" in editor_session
    assert "self._active_by_context" in editor_session
    assert "def list_open" in editor_session
    assert "session.context_id == context_id" in editor_session
    assert "dirty" in editor_session
    assert "active" in editor_session
    assert 'action == "list"' in editor_api
    assert 'action == "activate"' in editor_api
    assert 'event == "editor_activate"' in editor_ws
    assert "[EDITOR OPEN FILES]" in read("plugins", "_editor", "prompts", "agent.extras.editor_open_files.md")
    assert "Content is omitted" in editor_context
    assert "self.agent.context.id" in editor_extras
    assert "editor_open_files" in editor_extras
    assert not (PROJECT_ROOT / "plugins" / "_office" / "helpers" / "markdown_sessions.py").exists()
    assert "syncTextEditorResultsIntoOpenEditor" in editor_result_sync


def test_editor_open_file_browser_prefers_context_home_before_workdir_fallback():
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")
    start = editor_store.index("async openFileBrowser()")
    end = editor_store.index("\n  async openPath", start)
    open_file_browser = editor_store[start:end]

    home_lookup = open_file_browser.index('const home = await callEditor("home");')
    settings_fallback = open_file_browser.index('const response = await callJsonApi("settings_get", null);')

    assert home_lookup < settings_fallback
    assert "workdirPath = home.path;" in open_file_browser
    assert "workdirPath = response?.settings?.workdir_path || workdirPath;" in open_file_browser
    assert "fileBrowserStore.openTextPicker" in open_file_browser
    assert "selectedFiles" in open_file_browser
    assert "fileBrowserStore.normalizePath(file.path)" in open_file_browser


def test_editor_toolbar_places_preview_toggle_left_and_save_on_right():
    editor_panel = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")
    toolbar_start = editor_panel.index('<div class="editor-toolbar surface-toolbar"')
    toolbar_end = editor_panel.index('<div class="editor-search-bar"', toolbar_start)
    toolbar = editor_panel[toolbar_start:toolbar_end]

    mode_toggle = toolbar.index("editor-mode-toggle")
    history_tools = toolbar.index("editor-history-tools")
    source_tools = toolbar.index("editor-source-tools")
    preview_tools = toolbar.index("editor-preview-tools")
    spacer = toolbar.index("editor-toolbar-spacer")
    save_button = toolbar.index("editor-save-button")
    save_as_button = toolbar.index("editor-save-as-button")
    file_actions = toolbar.index("editor-file-actions")
    file_menu = toolbar.index("editor-file-menu")

    assert mode_toggle < history_tools < source_tools
    assert history_tools < preview_tools
    assert spacer < save_button < save_as_button < file_actions < file_menu
    assert "@click=\"$store.editor.save()\"" in toolbar
    assert "@click=\"$store.editor.saveAs()\"" in toolbar
    assert "async saveAs()" in editor_store
    assert "fileBrowserStore.openSaveAsPicker" in editor_store
    assert 'callEditor("save_as"' in editor_store
    assert "isTextDocument()" in toolbar
    assert 'data-editor-new-action="text"' in editor_store

    file_menu_markup = toolbar[file_menu:]
    assert "<span>Save</span>" not in file_menu_markup
    assert "<span>Rename</span>" in file_menu_markup
    assert "<span>Close File</span>" in file_menu_markup


def test_editor_uses_full_document_preview_and_matching_markdown_text_tools():
    editor_panel = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")

    assert "Previous page" not in editor_panel
    assert "Next page" not in editor_panel
    assert "editor-page-count" not in editor_panel
    assert "pagePositionLabel" not in editor_store
    assert "nextPage()" not in editor_store
    assert "previousPage()" not in editor_store
    assert 'x-show="$store.editor.isTextDocument()"' in editor_panel
    assert '$store.editor.isTextDocument() && $store.editor.isPreviewMode()' in editor_panel
    assert 'mode === PREVIEW_MODE && this.canPreview()' in editor_store
    assert "if (!this.session || !this.isTextDocument()) return;" in editor_store

    source_tools_start = editor_panel.index('class="editor-tool-group surface-toolbar-group editor-source-tools"')
    preview_tools_start = editor_panel.index('class="editor-tool-group surface-toolbar-group editor-preview-tools"')
    source_tools = editor_panel[source_tools_start:preview_tools_start]
    for action in ("Bold", "Italic", "List", "Numbered list", "Table"):
        assert f'title="{action}"' in source_tools
    assert "isMarkdown()" not in source_tools


def test_editor_history_shortcuts_and_toolbar_controls_cover_markdown_and_text():
    editor_panel = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")

    assert '@keydown.capture="$store.editor.handleEditorKeydown($event)"' in editor_panel
    history_start = editor_panel.index('class="editor-tool-group surface-toolbar-group editor-history-tools"')
    source_start = editor_panel.index('class="editor-tool-group surface-toolbar-group editor-source-tools"')
    history_tools = editor_panel[history_start:source_start]
    assert 'x-show="$store.editor.isTextDocument()"' in history_tools
    assert 'title="Undo"' in history_tools
    assert 'title="Redo"' in history_tools
    assert "$store.editor.previewEditing || !$store.editor.canUndo()" in history_tools
    assert "$store.editor.previewEditing || !$store.editor.canRedo()" in history_tools

    keydown_start = editor_store.index("handleEditorKeydown(event)")
    create_start = editor_store.index("\n  async create", keydown_start)
    keydown = editor_store[keydown_start:create_start]
    assert 'key === "z"' in keydown
    assert 'key === "y"' in keydown
    assert "event.stopPropagation()" in keydown
    assert "this[historyAction]()" in keydown
    assert "nativeEditing" in keydown

    undo_start = editor_store.index("\n  undo()")
    can_undo_start = editor_store.index("\n  canUndo()", undo_start)
    history_actions = editor_store[undo_start:can_undo_start]
    assert "sourceEditor.undo" not in history_actions
    assert "sourceEditor.redo" not in history_actions
    assert "pushHistory(text, coalesce = false)" in editor_store
    assert "this.pushHistory(this.editorText, true)" in editor_store






def test_skill_catalog_and_connector_boundaries_are_static_guarded():
    skills_py = read("helpers", "skills.py")
    connector_list = read("plugins", "_a0_connector", "api", "v1", "skills_list.py")
    connector_delete = read("plugins", "_a0_connector", "api", "v1", "skills_delete.py")

    assert "RENAMED_SKILLS" not in skills_py
    assert "RENAMED_SKILL_PATHS" not in skills_py
    assert "_migrate_skill_name" not in skills_py
    assert "_migrate_skill_path" not in skills_py
    assert "Built-in plugin skills cannot be deleted" in skills_py
    assert "list_skill_catalog" in connector_list
    assert "list_skills(" not in connector_list
    assert '"origin": skill["origin"]' in connector_list
    assert "list_skill_catalog" in connector_delete
    assert 'match.get("origin") not in {"User", "Project"}' in connector_delete
    assert "only user or project skills can be deleted" in connector_delete
