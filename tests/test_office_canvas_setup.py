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
    assert '["office", "desktop"]' in surfaces_js
    assert "htmlDataset.surfaceId" in surfaces_js
    assert "htmlDataset.canvasSurface" in surfaces_js
    assert ".surface-modal" in surfaces_css
    assert ".surface-floating" in surfaces_css
    assert ".surface-resize-handle" in surfaces_css
    assert ".surface-switcher" in surfaces_css
    assert "surface-window" not in surfaces_js + surfaces_css


def test_right_canvas_uses_desktop_surface_id_and_migrates_legacy_office_state():
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
    desktop_new_menu = read(
        "plugins",
        "_desktop",
        "extensions",
        "webui",
        "right-canvas-toolbar-start",
        "desktop-new-menu.html",
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
    assert "showGutter: false" in editor_store
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
    assert "right-canvas-desktop-actions" in desktop_new_menu
    assert "isSurfaceActive('desktop')" in desktop_new_menu
    assert "runNewMenuAction('writer')" in desktop_new_menu
    assert "runNewMenuAction('spreadsheet')" in desktop_new_menu
    assert "runNewMenuAction('presentation')" in desktop_new_menu
    assert "runNewMenuAction('markdown')" not in desktop_new_menu
    assert ".right-canvas-header" in right_canvas_css
    assert "overflow: visible;" in right_canvas_css
    assert ".right-canvas-toolbar" in right_canvas_css
    assert ".right-canvas-desktop-actions .office-new-menu" in desktop_web_panel
    assert "z-index: 4000;" in desktop_web_panel
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


def test_office_frontend_is_document_only_and_does_not_import_browser_or_desktop_runtime_code():
    office_store = read("plugins", "_office", "webui", "office-store.js")
    office_panel = read("plugins", "_office", "webui", "office-panel.html")
    office_modal = read("plugins", "_office", "webui", "main.html")

    assert "/plugins/_browser" not in office_store
    assert "right-canvas-store" not in office_store
    assert "handleUrlIntent" not in office_store
    assert "ensureDesktopSession" not in office_store
    assert "desktop_save" not in office_store
    assert "desktop_sync" not in office_store
    assert "desktop_state" not in office_store
    assert "desktop_shutdown" not in office_store
    assert "Xpra" not in office_store
    assert "xpra" not in office_store
    assert "data-office-desktop-host" not in office_panel
    assert "office-desktop-frame" not in office_panel
    assert "Restart Desktop" not in office_panel
    assert "data-surface-id" not in office_modal
    assert "modal-no-backdrop" not in office_modal
    assert "data-canvas-surface" not in office_modal

    assert "office-source-editor" not in office_panel
    assert "data-office-source" not in office_panel
    assert "office-document-header" not in office_panel
    assert "runNewMenuAction('markdown')" not in office_panel
    assert 'data-office-new-action="markdown"' not in office_store
    assert "openRenameModal" not in office_store
    assert "office_save" not in office_store
    assert 'callOffice("renamed"' not in office_store
    assert "data-office-source" not in office_store
    assert "office_input" not in office_store
    assert "requires_desktop" in office_store
    assert "openSurface(\"desktop\"" not in office_store


def test_desktop_plugin_owns_routes_runtime_surface_and_state_paths():
    desktop_plugin = PROJECT_ROOT / "plugins" / "_desktop"
    assert (desktop_plugin / "plugin.yaml").exists()
    assert (desktop_plugin / "api" / "desktop_session.py").exists()
    assert (desktop_plugin / "helpers" / "desktop_session.py").exists()
    assert (desktop_plugin / "helpers" / "desktop_state.py").exists()
    assert (desktop_plugin / "skills" / "linux-desktop" / "scripts" / "desktopctl.sh").exists()

    desktop_startup = read("plugins", "_desktop", "extensions", "python", "startup_migration", "_20_desktop_routes.py")
    desktop_api = read("plugins", "_desktop", "api", "desktop_session.py")
    desktop_session = read("plugins", "_desktop", "helpers", "desktop_session.py")
    desktop_state = read("plugins", "_desktop", "helpers", "desktop_state.py")
    desktop_store = read("plugins", "_desktop", "webui", "desktop-store.js")
    desktop_main = read("plugins", "_desktop", "webui", "main.html")
    desktop_web_panel = read("plugins", "_desktop", "webui", "desktop-panel.html")

    assert "virtual_desktop_routes.install_route_hooks()" in desktop_startup
    assert 'action in {"open_document", "document"}' in desktop_api
    assert "document_store.EDITOR_TEXT_EXTENSIONS" in desktop_api
    assert "Text documents use the Editor surface." in desktop_api
    assert "return self._open_markdown(doc, input, request)" not in desktop_api
    assert "markdown_sessions" not in desktop_api
    assert '"status": desktop.get("status") or {}' in desktop_api
    assert 'callJsonApi("/plugins/_desktop/desktop_session"' in desktop_store
    assert 'callDesktop("open_document"' in desktop_store
    assert 'callOffice("create"' in desktop_store
    assert "open_in_desktop: isOfficialExtension(fmt)" in desktop_store
    assert "DESKTOP_RUNTIME_INSTALL_MESSAGE" in desktop_store
    assert "openDesktopWhenRuntimeReady" in desktop_store
    assert "isDesktopRuntimeInstalling" in desktop_store
    assert "_desktopDisplaySizes: {}" in desktop_store
    assert "desktopDisplaySizeForToken(token" in desktop_store
    assert "rememberDesktopDisplaySize(token" in desktop_store
    assert "options.displaySize || this.desktopDisplaySizeForToken(token)" in desktop_store
    assert "result?.width || width" in desktop_store
    assert "canvas.width = normalizedWidth" in desktop_store
    assert "canvas.height = normalizedHeight" in desktop_store
    assert "canvas?.clientWidth || canvas?.width" in desktop_store
    assert "overflow: auto !important;" in desktop_store
    assert "Installing Agent Zero Desktop runtime dependencies" in desktop_session
    assert "normalize_desktop_display_size" in desktop_session
    assert "__a0XpraOffsetWarnPatched" in desktop_store
    assert "window does not fit in canvas, offsets" in desktop_store
    assert "decode error packet" in desktop_store
    assert 'data-surface-id="desktop"' in desktop_main
    assert "virtual_desktop.session_url" in desktop_session
    assert 'owner="desktop"' in desktop_session
    assert 'STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME))' in desktop_session
    assert 'STATE_DIR = BASE_DIR / "usr" / "plugins" / PLUGIN_NAME' in desktop_state
    assert "> x-component > div[x-data] > .office-panel" in desktop_web_panel
    assert ".office-state-line > span:not(.material-symbols-outlined)" in desktop_web_panel

    assert not (PROJECT_ROOT / "plugins" / "_office" / "helpers" / "desktop_state.py").exists()
    assert not (PROJECT_ROOT / "plugins" / "_office" / "helpers" / "libreoffice_desktop.py").exists()
    assert not (PROJECT_ROOT / "plugins" / "_office" / "helpers" / "libreoffice_desktop_routes.py").exists()
    assert not (PROJECT_ROOT / "plugins" / "_office" / "assets" / "desktop").exists()


def test_plugin_owned_runtime_state_paths_are_declared():
    office_documents = read("plugins", "_office", "helpers", "document_store.py")
    browser_playwright = read("plugins", "_browser", "helpers", "playwright.py")
    browser_extensions = read("plugins", "_browser", "helpers", "extension_manager.py")
    docker_playwright = read("docker", "run", "fs", "ins", "install_playwright.sh")

    assert 'PLUGIN_NAME = "_office"' in office_documents
    assert 'STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME, "documents"))' in office_documents
    assert 'PLAYWRIGHT_CACHE_DIR = ("tmp", "playwright")' in browser_playwright
    assert '"usr", "plugins", "_browser", "playwright"' in browser_playwright
    assert "Path(files.get_abs_path(*PLAYWRIGHT_CACHE_DIR))" in browser_playwright
    assert "find_playwright_binary(_primary_cache_dir())" in browser_playwright
    assert "Path(files.get_abs_path(*EXTENSIONS_ROOT_DIR))" in browser_extensions
    assert "PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright" in docker_playwright


def test_office_artifacts_only_open_desktop_from_explicit_document_ui_requests():
    auto_open = read(
        "plugins",
        "_office",
        "extensions",
        "webui",
        "set_messages_after_loop",
        "auto-open-document-results.js",
    )
    document_actions = read("plugins", "_office", "extensions", "webui", "lib", "document-actions.js")
    document_handler = read(
        "plugins",
        "_office",
        "extensions",
        "webui",
        "get_tool_message_handler",
        "office-artifact-handler.js",
    )
    response_cards = read(
        "plugins",
        "_office",
        "extensions",
        "webui",
        "set_messages_after_loop",
        "document-response-file-cards.js",
    )
    messages_css = read("webui", "css", "messages.css")
    document_tool = read("plugins", "_office", "tools", "office_artifact.py")
    office_api = read("plugins", "_office", "api", "office_session.py")
    editor_sync = read(
        "plugins",
        "_editor",
        "extensions",
        "webui",
        "set_messages_after_loop",
        "sync-text-editor-results.js",
    )

    assert 'openSurface(surfaceForDocument' in auto_open
    assert 'return "desktop";' in auto_open
    assert "isExplicitDocumentUiRequest(payload)" in auto_open
    assert 'action === "open"' in auto_open
    assert "open_in_canvas" in auto_open
    assert "open_in_desktop" in auto_open
    assert 'surfaces.open("desktop"' not in auto_open
    assert "rightCanvas.open" not in auto_open
    assert "globalThis.Alpine" not in auto_open
    assert "syncDocumentResultsIntoOpenSurfaces" in auto_open
    assert "isOfficeCanvas" not in auto_open
    assert "officeStore" in auto_open
    assert "desktopStore" in auto_open
    assert "store?.previewEditDirty" in auto_open
    assert "syncOpenDesktopCanvas" in auto_open
    assert "syncOpenOfficeModal" in auto_open
    assert "isDesktopSurfaceOpen" in auto_open
    assert "function documentTarget(payload = {}, document = {})" in auto_open
    assert 'toolName !== "office_artifact"' in auto_open
    assert "syncTextEditorResultsIntoOpenEditor" in editor_sync
    assert 'toolName(payload) !== "text_editor"' in editor_sync
    assert 'return ["write", "patch"].includes(action);' in editor_sync
    assert "if (!context?.results?.length) return;" in editor_sync
    assert "if (context.historyEmpty && !explicitOpen) continue;" in editor_sync
    assert "syncOpenEditorSurface" in editor_sync
    assert "isEditorSurfaceOpen" in editor_sync
    assert "context_id" in editor_sync
    assert "ctxid" in editor_sync
    assert "void syncOpenDocumentSurfaces(target);" in auto_open
    assert "void syncOpenDocumentSurfaces({ path, file_id: fileId });" not in auto_open
    assert "editorStore" not in auto_open
    assert "text_editor" not in auto_open
    assert "hasSameDocument" in auto_open
    assert 'source: "tool-result-sync"' in auto_open
    assert '".modal .office-panel"' not in auto_open
    assert "normalizeDocumentMetadata" in document_actions
    assert "buildDocumentFileCard" in document_actions
    assert "document-file-card" in document_actions
    assert "buildDocumentFileCard" not in document_handler
    assert "buildDocumentFileActionButtons" not in document_handler
    assert "document-file-card-wrapper" not in document_handler
    assert "message-document-artifact" not in document_handler
    assert "actionButtons: []" in document_handler
    assert "injectDocumentCardsIntoFinalResponses" in response_cards
    assert "buildDocumentFileCard" in response_cards
    assert "buildDocumentFileActionButtons" in response_cards
    assert "message-agent-response" in response_cards
    assert "document-response-file-cards" in response_cards
    assert "document-response-file-action" in response_cards
    assert "RESPONSE_CARD_ACTIONS" in response_cards
    assert "documentIdentityKey" in response_cards
    assert "uniqueByDocument" in response_cards
    assert "PENDING_TTL_MS" in response_cards
    assert "pendingContextId" in response_cards
    assert "globalThis.getContext" in response_cards
    assert "prunePendingDocuments" in response_cards
    assert "wrapper.dataset.documents" in response_cards
    assert "refreshResponseFileActions" in response_cards
    assert "parseStoredDocuments" in response_cards
    assert "openDocumentInDesktop" in document_actions
    assert "openDocumentInEditor" not in document_actions
    assert "openOfficeArtifact" in document_actions
    assert "openDocumentArtifact" not in document_actions
    assert 'await openSurface("editor"' not in document_actions
    assert "await openDocumentInDesktop(document);" in document_actions
    assert 'ensureModalOpen("/plugins/_office/webui/main.html")' not in document_actions
    assert 'ensureModalOpen("/plugins/_office/webui/main.html")' not in auto_open
    assert "Open in canvas" in document_actions
    assert "Copy path" not in document_actions
    assert "copyToClipboard" not in document_actions
    assert "Details" not in document_handler
    assert "Details" not in response_cards
    assert "/api/download_work_dir_file" in document_actions
    assert 'openSurface("desktop"' in document_actions
    assert 'openSurface("editor"' not in document_actions
    assert "Open in canvas with Writer" in document_actions
    assert "Open in canvas with Calc" in document_actions
    assert "Open in canvas with Impress" in document_actions
    assert 'const DESKTOP_FORMATS = ["odt", "ods", "odp", "docx", "xlsx", "pptx"]' in document_actions
    assert ".document-file-card" in messages_css
    assert ".document-response-file-cards" in messages_css
    assert ".document-file-action-label" not in messages_css
    assert ".process-step-detail-content.document-file-card-wrapper" not in messages_css
    assert "open_in_canvas: bool = False" in document_tool
    assert '"open_in_canvas": bool(open_in_canvas)' in document_tool
    assert '"open_in_desktop": bool(open_in_desktop)' in document_tool
    assert '"requires_desktop": True' in office_api
    assert 'input.get("open_in_desktop") is not True' in office_api
    assert 'action == "desktop"' not in office_api
    assert 'action == "desktop_state"' not in office_api
    assert 'action == "desktop_shutdown"' not in office_api
    assert "Text documents use the Editor surface." in office_api
    assert '"requires_editor": True' not in office_api


def test_editor_plugin_owns_markdown_sessions_and_active_context_extras():
    editor_plugin = PROJECT_ROOT / "plugins" / "_editor"
    assert (editor_plugin / "plugin.yaml").exists()
    assert (editor_plugin / "api" / "editor_session.py").exists()
    assert (editor_plugin / "api" / "ws_editor.py").exists()

    editor_session = read("plugins", "_editor", "helpers", "markdown_sessions.py")
    editor_api = read("plugins", "_editor", "api", "editor_session.py")
    editor_ws = read("plugins", "_editor", "api", "ws_editor.py")
    editor_context = read("plugins", "_editor", "helpers", "open_files_context.py")
    office_ws = read("plugins", "_office", "api", "ws_office.py")
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
    desktop_context = read(
        "plugins",
        "_desktop",
        "extensions",
        "python",
        "message_loop_prompts_after",
        "_55_include_desktop_state.py",
    )
    office_context = read(
        "plugins",
        "_office",
        "extensions",
        "python",
        "message_loop_prompts_after",
        "_55_include_office_canvas_context.py",
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
    assert "desktop_state" in desktop_context
    assert 'pop("office_canvas"' in office_context
    assert "Office WebSocket editing is not available for text documents; use the Editor surface." in office_ws
    assert "from plugins._office.helpers import document_store, markdown_sessions" not in office_ws
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
    toolbar_start = editor_panel.index('<div class="editor-toolbar"')
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
    assert 'mode === PREVIEW_MODE && this.isTextDocument()' in editor_store
    assert "if (!this.session || !this.isTextDocument()) return;" in editor_store

    source_tools_start = editor_panel.index('class="editor-tool-group editor-source-tools"')
    preview_tools_start = editor_panel.index('class="editor-tool-group editor-preview-tools"')
    source_tools = editor_panel[source_tools_start:preview_tools_start]
    for action in ("Bold", "Italic", "List", "Numbered list", "Table"):
        assert f'title="{action}"' in source_tools
    assert "isMarkdown()" not in source_tools


def test_editor_history_shortcuts_and_toolbar_controls_cover_markdown_and_text():
    editor_panel = read("plugins", "_editor", "webui", "editor-panel.html")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")

    assert '@keydown.capture="$store.editor.handleEditorKeydown($event)"' in editor_panel
    history_start = editor_panel.index('class="editor-tool-group editor-history-tools"')
    source_start = editor_panel.index('class="editor-tool-group editor-source-tools"')
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


def test_desktop_text_open_with_routes_to_editor_surface():
    desktop_session = read("plugins", "_desktop", "helpers", "desktop_session.py")
    desktop_store = read("plugins", "_desktop", "webui", "desktop-store.js")
    editor_store = read("plugins", "_editor", "webui", "editor-store.js")
    browser_store = read("plugins", "_browser", "webui", "browser-store.js")

    assert 'EDITOR_HANDLER_DESKTOP_ID = "agent-zero-editor.desktop"' in desktop_session
    assert "def _write_editor_bridge_script" in desktop_session
    assert "a0-editor://open?path=" in desktop_session
    assert "_editor_text_handler_mime_types()" in desktop_session
    assert '"text/markdown"' in desktop_session
    assert '"text/x-markdown"' in desktop_session
    assert '"text/plain"' in desktop_session
    assert "applications_dir / EDITOR_HANDLER_DESKTOP_ID" in desktop_session
    assert 'desktop_dir / "Editor.desktop"' in desktop_session
    assert "Opened text in Editor" in desktop_store
    assert "registerUrlHandler" in editor_store
    assert "handleEditorUrlIntent" in editor_store
    assert 'openLatestSurface("editor"' in editor_store

    # Text files default to LibreOffice Writer inside the Desktop; the Agent
    # Zero Editor stays available as a secondary "Open With" association.
    assert 'WRITER_HANDLER_DESKTOP_ID = "libreoffice-writer.desktop"' in desktop_session
    assert "{mime_type}={WRITER_HANDLER_DESKTOP_ID}" in desktop_session
    assert "[WRITER_HANDLER_DESKTOP_ID, editor_desktop_id, " in desktop_session

    # The browser surface must not claim a0-editor: intents, otherwise the
    # editor "Open With" handler lands on an unloadable about:blank page.
    assert "function isWebUrlIntent" in browser_store
    assert "if (!isWebUrlIntent(url)) return false;" in browser_store


def test_office_and_desktop_skills_are_rehomed_and_renamed():
    office_skills = PROJECT_ROOT / "plugins" / "_office" / "skills"
    desktop_skills = PROJECT_ROOT / "plugins" / "_desktop" / "skills"

    assert not (office_skills / "linux-desktop").exists()
    assert (desktop_skills / "linux-desktop" / "SKILL.md").exists()
    assert (office_skills / "office-artifacts" / "SKILL.md").exists()
    assert not (office_skills / "document-artifacts").exists()
    assert not (office_skills / "word-documents").exists()
    assert not (office_skills / "excel-workbooks").exists()
    assert not (office_skills / "presentation-decks").exists()

    expected = {
        "office-artifacts": office_skills / "office-artifacts" / "SKILL.md",
        "writer-documents": office_skills / "writer-documents" / "SKILL.md",
        "calc-spreadsheets": office_skills / "calc-spreadsheets" / "SKILL.md",
        "impress-presentations": office_skills / "impress-presentations" / "SKILL.md",
        "markdown-documents": office_skills / "markdown-documents" / "SKILL.md",
    }
    for name, path in expected.items():
        text = path.read_text(encoding="utf-8")
        assert f"name: {name}" in text

    desktop_skill = (desktop_skills / "linux-desktop" / "SKILL.md").read_text(encoding="utf-8")
    desktopctl = (desktop_skills / "linux-desktop" / "scripts" / "desktopctl.sh").read_text(encoding="utf-8")
    assert "/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh" in desktop_skill
    assert "Open in Desktop action" in desktop_skill
    assert "$BASE_DIR/usr/plugins/_desktop/profiles/$SESSION" in desktopctl
    assert "$BASE_DIR/usr/plugins/_desktop/sessions/$SESSION.json" in desktopctl
    assert "sequence|batch)" in desktopctl
    assert "dispatch_command $line" in desktopctl
    assert '"$0" $line' not in desktopctl


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
