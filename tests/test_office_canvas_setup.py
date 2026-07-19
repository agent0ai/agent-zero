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
    assert "/plugins/_browser/webui/main.html" in surfaces_js
    assert "/plugins/_desktop/webui/main.html" in surfaces_js
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

    assert 'await callJsExtensions("surfaces_register", this);' in canvas_store
    assert 'await callJsExtensions("right_canvas_register_surfaces", this);' in canvas_store
    assert "migratePersistedSurfaceState" in canvas_store
    assert "normalizeSurfaceId" in canvas_store
    assert "const saved = migratePersistedSurfaceState(JSON.parse" in canvas_store
    assert 'id: "desktop"' in desktop_register
    assert 'modalPath: "/plugins/_desktop/webui/main.html"' in desktop_register
    assert 'data-surface-id="desktop"' in desktop_panel
    assert "isSurfaceVisible('desktop')" in desktop_panel
    assert "right-canvas-desktop-actions" in desktop_new_menu
    assert "isSurfaceActive('desktop')" in desktop_new_menu
    assert "runNewMenuAction('writer')" in desktop_new_menu
    assert "runNewMenuAction('spreadsheet')" in desktop_new_menu
    assert "runNewMenuAction('presentation')" in desktop_new_menu
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

    assert "office-source-editor" in office_panel
    assert "data-office-source" in office_panel
    assert "openRenameModal" in office_store
    assert "office_save" in office_store
    assert 'callOffice("renamed"' in office_store
    assert "requires_desktop" in office_store
    assert "openSurface(\"desktop\"" in office_store


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
    assert "markdown_sessions" in desktop_api
    assert 'if ext == "md":' in desktop_api
    assert "return self._open_markdown(doc, input, request)" in desktop_api
    assert '"status": desktop.get("status") or {}' in desktop_api
    assert 'callJsonApi("/plugins/_desktop/desktop_session"' in desktop_store
    assert 'callDesktop("open_document"' in desktop_store
    assert 'callOffice("create"' in desktop_store
    assert "open_in_desktop: isOfficialExtension(fmt)" in desktop_store
    assert "DESKTOP_RUNTIME_INSTALL_MESSAGE" in desktop_store
    assert "openDesktopWhenRuntimeReady" in desktop_store
    assert "isDesktopRuntimeInstalling" in desktop_store
    assert "Installing Agent Zero Desktop runtime dependencies" in desktop_session
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


def test_document_artifacts_only_open_desktop_from_explicit_document_ui_requests():
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
        "document-artifact-handler.js",
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
    document_tool = read("plugins", "_office", "tools", "document_artifact.py")
    office_api = read("plugins", "_office", "api", "office_session.py")

    assert 'openSurface("desktop"' in auto_open
    assert "isExplicitDocumentUiRequest(payload)" in auto_open
    assert 'action === "open"' in auto_open
    assert "open_in_canvas" in auto_open
    assert "open_in_desktop" in auto_open
    assert 'surfaces.open("desktop"' not in auto_open
    assert "rightCanvas.open" not in auto_open
    assert "globalThis.Alpine" not in auto_open
    assert "syncDocumentResultsIntoOpenOfficeModal" in auto_open
    assert "isOfficeCanvas" not in auto_open
    assert "officeStore" in auto_open
    assert "desktopStore" in auto_open
    assert "syncOpenDesktopCanvas" in auto_open
    assert "syncOpenOfficeModal" in auto_open
    assert "isDesktopSurfaceOpen" in auto_open
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
    assert "openDocumentArtifact" in document_actions
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
    assert "Open in canvas with Writer" in document_actions
    assert "Open in canvas with Calc" in document_actions
    assert "Open in canvas with Impress" in document_actions
    assert '"md", "odt", "ods", "odp", "docx", "xlsx", "pptx"' in document_actions
    assert ".document-file-card" in messages_css
    assert ".document-response-file-cards" in messages_css
    assert ".document-file-action-label" not in messages_css
    assert ".process-step-detail-content.document-file-card-wrapper" not in messages_css
    assert "open_in_canvas: bool = False" in document_tool
    assert '"open_in_canvas": bool(open_in_canvas)' in document_tool
    assert '"open_in_desktop": bool(open_in_desktop)' in document_tool
    assert '"requires_desktop": True' in office_api
    assert 'input.get("open_in_desktop") is not True' in office_api


def test_office_and_desktop_skills_are_rehomed_and_renamed():
    office_skills = PROJECT_ROOT / "plugins" / "_office" / "skills"
    desktop_skills = PROJECT_ROOT / "plugins" / "_desktop" / "skills"

    assert not (office_skills / "linux-desktop").exists()
    assert (desktop_skills / "linux-desktop" / "SKILL.md").exists()
    assert not (office_skills / "office-artifacts").exists()
    assert not (office_skills / "word-documents").exists()
    assert not (office_skills / "excel-workbooks").exists()
    assert not (office_skills / "presentation-decks").exists()

    expected = {
        "document-artifacts": office_skills / "document-artifacts" / "SKILL.md",
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
