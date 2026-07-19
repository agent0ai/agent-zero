import asyncio
import json
import sys
import threading
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _TestAgentContext:
    @staticmethod
    def get(context_id):
        return None


class _TestResponse(SimpleNamespace):
    def __init__(self, message="", break_loop=False, **kwargs):
        super().__init__(message=message, break_loop=break_loop, **kwargs)


class _TestTool:
    def __init__(
        self,
        agent=None,
        name="",
        method=None,
        args=None,
        message="",
        loop_data=None,
        **kwargs,
    ):
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args or {}
        self.message = message
        self.loop_data = loop_data


class _TestWsHandler:
    def __init__(self, *args, **kwargs):
        self.emitted = []

    async def emit_to(self, sid, event, data, correlation_id=None):
        self.emitted.append((sid, event, data, correlation_id))


class _TestWsResult(dict):
    @staticmethod
    def error(code="", message="", correlation_id=None):
        return _TestWsResult(
            {
                "ok": False,
                "code": code,
                "error": message,
                "correlation_id": correlation_id,
            }
        )


sys.modules.setdefault("agent", SimpleNamespace(AgentContext=_TestAgentContext))
sys.modules.setdefault("helpers.tool", SimpleNamespace(Response=_TestResponse, Tool=_TestTool))
sys.modules.setdefault("helpers.ws", SimpleNamespace(WsHandler=_TestWsHandler))
sys.modules.setdefault("helpers.ws_manager", SimpleNamespace(WsResult=_TestWsResult))
_model_config_stub = ModuleType("plugins._model_config.helpers.model_config")
_model_config_stub.get_presets = lambda: []
_model_config_stub.get_preset_by_name = lambda name: None
_model_config_stub.get_chat_model_config = lambda agent=None: {}
sys.modules.setdefault("plugins._model_config.helpers.model_config", _model_config_stub)


@pytest.fixture
def anyio_backend():
    return "asyncio"

from helpers.errors import RepairableException
from plugins._browser.helpers.config import (
    build_browser_launch_config,
    get_browser_main_model_summary,
    get_browser_model_preset_options,
    normalize_browser_config,
    resolve_browser_model_selection,
)
from plugins._browser.helpers.extension_manager import (
    _build_web_store_download_url,
    _crx_zip_payload,
    _detect_chrome_prodversion,
    _normalize_chrome_prodversion,
    get_extensions_root,
    parse_chrome_web_store_extension_id,
    uninstall_browser_extension,
)
import plugins._browser.helpers.extension_manager as browser_extension_manager_module
from plugins._browser.helpers.runtime import (
    BrowserPage,
    _BrowserRuntimeCore,
    _BrowserScreencast,
    list_runtime_sessions,
    normalize_url,
)
import plugins._browser.helpers.runtime as browser_runtime_module
from plugins._browser.helpers.playwright import (
    get_playwright_binary,
    get_playwright_cache_dir,
)
import plugins._browser.helpers.playwright as browser_playwright_module
import plugins._browser.hooks as browser_hooks_module
import plugins._browser.tools.browser as browser_tool_module
import plugins._browser.api.ws_browser as ws_browser_module


SMALL_JPEG_10X10 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsL"
    "DBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/"
    "2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAKAAoDASIAAhEBAxEB/8QAFQAB"
    "AAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhADE"
    "AAAAKf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAA"
    "AAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECA"
    "QE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAA"
    "AAAAAAAAAAAAAA/9oACAEBAAE/ISf/2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAA"
    "AAAAAAAAAAP/aAAgBAwEBPxAk/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEB"
    "PxAk/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxAn/9k="
)


def test_browser_url_normalization_matches_address_bar_hosts():
    assert normalize_url("localhost:3000") == "http://localhost:3000/"
    assert normalize_url("127.0.0.1:8000/path") == "http://127.0.0.1:8000/path"
    assert normalize_url("novinky.cz") == "https://novinky.cz/"
    assert normalize_url("https://example.com") == "https://example.com/"
    assert normalize_url("about:blank") == "about:blank"
    with pytest.raises(RepairableException, match="relative"):
        normalize_url("/docs")


def test_browser_config_normalizes_extension_paths(tmp_path):
    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()

    config = normalize_browser_config(
        {
            "extension_paths": [str(extension_dir), "", "  ", str(extension_dir)],
        }
    )

    assert config == {
        "extension_paths": [str(extension_dir)],
        "default_homepage": "about:blank",
        "autofocus_active_page": True,
        "max_open_tabs": 32,
        "runtime_backend": "container",
        "host_browser_privacy_policy": "allow",
        "host_browser_profile_mode": "existing",
        "model_preset": "",
    }


def test_browser_config_normalizes_model_preset():
    assert normalize_browser_config({"model_preset": "  Research  "})["model_preset"] == "Research"
    assert "model" not in normalize_browser_config({"model": "main"})


def test_browser_config_normalizes_host_backend_and_privacy_policy():
    config = normalize_browser_config(
        {
            "runtime_backend": "host-required",
            "host_browser_privacy_policy": "warn",
            "host_browser_profile_mode": "agent",
        }
    )

    assert config["runtime_backend"] == "host_required"
    assert config["host_browser_privacy_policy"] == "warn"
    assert config["host_browser_profile_mode"] == "agent"
    assert (
        normalize_browser_config({"runtime_backend": "host_when_available"})["runtime_backend"]
        == "host_required"
    )


def test_browser_config_normalizes_max_open_tabs():
    assert normalize_browser_config({"max_open_tabs": "12"})["max_open_tabs"] == 12
    assert normalize_browser_config({"max_open_tabs": "0"})["max_open_tabs"] == 1
    assert normalize_browser_config({"max_open_tabs": "200"})["max_open_tabs"] == 50
    assert normalize_browser_config({"max_open_tabs": "oops"})["max_open_tabs"] == 32


def test_browser_model_selection_uses_presets(monkeypatch):
    import plugins._browser.helpers.config as browser_config_module
    from plugins._model_config.helpers import model_config

    monkeypatch.setattr(
        browser_config_module,
        "get_browser_config",
        lambda agent=None: {"model_preset": "Research", "extension_paths": []},
    )
    monkeypatch.setattr(
        model_config,
        "get_preset_by_name",
        lambda name: {
            "name": "Research",
            "chat": {"provider": "openrouter", "name": "example/model"},
        } if name == "Research" else None,
    )

    selection = resolve_browser_model_selection(SimpleNamespace())

    assert selection["source_kind"] == "preset"
    assert selection["config"] == {"provider": "openrouter", "name": "example/model"}


def test_browser_model_selection_falls_back_to_main_for_missing_preset(monkeypatch):
    from plugins._model_config.helpers import model_config

    monkeypatch.setattr(model_config, "get_preset_by_name", lambda name: None)
    monkeypatch.setattr(
        model_config,
        "get_chat_model_config",
        lambda agent=None: {"provider": "openrouter", "name": "main/model"},
    )

    selection = resolve_browser_model_selection(SimpleNamespace(), {"model_preset": "Missing"})

    assert selection["source_kind"] == "main"
    assert selection["preset_status"] == "missing"
    assert selection["config"] == {"provider": "openrouter", "name": "main/model"}


def test_browser_model_preset_options_include_missing_selected(monkeypatch):
    from plugins._model_config.helpers import model_config

    monkeypatch.setattr(
        model_config,
        "get_presets",
        lambda: [{"name": "Balance", "chat": {"provider": "openrouter", "name": "model"}}],
    )

    options = get_browser_model_preset_options(settings={"model_preset": "Deleted"})

    assert options[-1]["name"] == "Deleted"
    assert options[-1]["missing"] is True


def test_browser_main_model_summary_shows_current_model(monkeypatch):
    from plugins._model_config.helpers import model_config

    monkeypatch.setattr(
        model_config,
        "get_chat_model_config",
        lambda agent=None: {"provider": "openrouter", "name": "example/main"},
    )

    assert get_browser_main_model_summary() == "openrouter / example/main"


def test_browser_launch_config_uses_full_chromium_for_all_sessions(tmp_path):
    default_launch = build_browser_launch_config(
        {
            "extension_paths": [],
        }
    )

    assert default_launch["browser_mode"] == "chromium"
    assert default_launch["channel"] is None
    assert default_launch["requires_full_browser"] is True
    assert not any(arg.startswith("--load-extension=") for arg in default_launch["args"])
    assert "--headless=new" not in default_launch["args"]

    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()

    launch = build_browser_launch_config(
        {
            "extension_paths": [str(extension_dir)],
        }
    )

    assert launch["browser_mode"] == "chromium"
    assert launch["channel"] is None
    assert launch["requires_full_browser"] is True
    assert launch["extensions"]["active"] is True
    assert any(arg.startswith("--load-extension=") for arg in launch["args"])
    assert "--headless=new" not in launch["args"]


def _patch_playwright_cache_root(monkeypatch, tmp_path):
    monkeypatch.delenv("A0_BROWSER_PLAYWRIGHT_CACHE_DIR", raising=False)
    monkeypatch.setattr(
        browser_playwright_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )


def _write_playwright_binary(cache_dir: Path) -> Path:
    browser_binary = cache_dir / "chromium-1169" / "chrome-linux" / "chrome"
    browser_binary.parent.mkdir(parents=True)
    browser_binary.write_text("#!/bin/sh\n", encoding="utf-8")
    return browser_binary


def test_browser_playwright_cache_uses_tmp_path(monkeypatch, tmp_path):
    _patch_playwright_cache_root(monkeypatch, tmp_path)
    primary_cache = tmp_path / "tmp" / "playwright"
    browser_binary = _write_playwright_binary(primary_cache)

    assert get_playwright_cache_dir() == str(
        tmp_path / "tmp" / "playwright"
    )
    assert browser_playwright_module.get_playwright_cache_dirs() == [
        tmp_path / "tmp" / "playwright",
        tmp_path / "usr" / "plugins" / "_browser" / "playwright",
        tmp_path / "usr" / "browser" / "playwright",
    ]
    assert get_playwright_binary() == browser_binary


def test_browser_playwright_binary_ignores_retired_usr_cache(monkeypatch, tmp_path):
    _patch_playwright_cache_root(monkeypatch, tmp_path)
    _write_playwright_binary(
        tmp_path / "usr" / "plugins" / "_browser" / "playwright"
    )

    assert get_playwright_binary() is None


def test_browser_playwright_cache_migrates_valid_retired_usr_cache(monkeypatch, tmp_path):
    _patch_playwright_cache_root(monkeypatch, tmp_path)
    retired_cache = tmp_path / "usr" / "plugins" / "_browser" / "playwright"
    _write_playwright_binary(retired_cache)

    result = browser_hooks_module.cleanup_playwright_cache()

    assert result["errors"] == []
    assert result["migrated"] == str(retired_cache)
    assert get_playwright_binary() == (
        tmp_path / "tmp" / "playwright" / "chromium-1169" / "chrome-linux" / "chrome"
    )
    assert not retired_cache.exists()


def test_browser_playwright_cache_removes_retired_usr_cache_when_tmp_valid(
    monkeypatch, tmp_path
):
    _patch_playwright_cache_root(monkeypatch, tmp_path)
    primary_cache = tmp_path / "tmp" / "playwright"
    retired_cache = tmp_path / "usr" / "plugins" / "_browser" / "playwright"
    _write_playwright_binary(primary_cache)
    _write_playwright_binary(retired_cache)

    result = browser_hooks_module.cleanup_playwright_cache()

    assert result["errors"] == []
    assert result["migrated"] == ""
    assert str(retired_cache) in result["removed"]
    assert get_playwright_binary() == (
        primary_cache / "chromium-1169" / "chrome-linux" / "chrome"
    )
    assert not retired_cache.exists()


def test_browser_playwright_cache_missing_dirs_do_not_raise(monkeypatch, tmp_path):
    _patch_playwright_cache_root(monkeypatch, tmp_path)

    result = browser_hooks_module.cleanup_playwright_cache()

    assert result["errors"] == []
    assert result["migrated"] == ""
    assert result["removed"] == []
    assert not (tmp_path / "tmp" / "playwright").exists()
    assert browser_playwright_module.get_playwright_cache_dirs() == [
        tmp_path / "tmp" / "playwright",
        tmp_path / "usr" / "plugins" / "_browser" / "playwright",
        tmp_path / "usr" / "browser" / "playwright",
    ]
    assert get_playwright_binary() is None


def test_browser_extension_storage_uses_plugin_user_path(monkeypatch, tmp_path):
    monkeypatch.setattr(
        browser_extension_manager_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )

    assert get_extensions_root() == tmp_path / "usr" / "_browser" / "extensions"


def test_browser_extension_manager_uninstalls_only_managed_extensions(monkeypatch, tmp_path):
    monkeypatch.setattr(
        browser_extension_manager_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )
    managed_extension = get_extensions_root() / "chrome-web-store" / ("a" * 32)
    external_extension = tmp_path / "external-extension"
    for extension_dir, name in (
        (managed_extension, "Managed Extension"),
        (external_extension, "External Extension"),
    ):
        extension_dir.mkdir(parents=True)
        (extension_dir / "manifest.json").write_text(
            json.dumps({"name": name, "version": "1.0.0"}),
            encoding="utf-8",
        )

    saved_configs = []
    monkeypatch.setattr(
        browser_extension_manager_module,
        "get_browser_config",
        lambda: {
            "extension_paths": [str(managed_extension), str(external_extension)],
        },
    )
    monkeypatch.setattr(
        browser_extension_manager_module.plugins,
        "save_plugin_config",
        lambda _plugin, _project, _agent, config: saved_configs.append(config.copy()),
    )

    entries = browser_extension_manager_module.list_browser_extensions()
    managed_entry = next(item for item in entries if item["path"] == str(managed_extension))
    external_entry = next(item for item in entries if item["path"] == str(external_extension))

    assert managed_entry["can_delete"] is True
    assert managed_entry["managed"] is True
    assert external_entry["can_delete"] is False

    result = uninstall_browser_extension(str(managed_extension))

    assert result["name"] == "Managed Extension"
    assert result["extension_paths"] == [str(external_extension)]
    assert not managed_extension.exists()
    assert external_extension.exists()
    assert saved_configs[-1]["extension_paths"] == [str(external_extension)]

    with pytest.raises(ValueError, match="Only Browser-managed"):
        uninstall_browser_extension(str(external_extension))
    assert external_extension.exists()


def test_browser_extension_manager_exposes_openable_manifest_ui(monkeypatch, tmp_path):
    monkeypatch.setattr(
        browser_extension_manager_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )
    extension_dir = get_extensions_root() / "local-options"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Openable Extension",
                "version": "1.0.0",
                "options_ui": {"page": "options/index.html"},
                "action": {"default_popup": "popup.html"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        browser_extension_manager_module,
        "get_browser_config",
        lambda: {"extension_paths": [str(extension_dir)]},
    )

    entry = browser_extension_manager_module.list_browser_extensions()[0]
    expected_id = browser_extension_manager_module._extension_id_from_path(extension_dir)

    assert entry["id"] == expected_id
    assert entry["has_ui"] is True
    assert entry["open_label"] == "Options"
    assert entry["open_url"] == f"chrome-extension://{expected_id}/options/index.html"
    assert entry["ui"]["targets"][1]["url"] == f"chrome-extension://{expected_id}/popup.html"


def test_browser_extension_manager_parses_web_store_urls():
    extension_id = "a" * 32

    assert parse_chrome_web_store_extension_id(extension_id) == extension_id
    assert (
        parse_chrome_web_store_extension_id(
            f"https://chromewebstore.google.com/detail/example/{extension_id}"
        )
        == extension_id
    )
    assert (
        parse_chrome_web_store_extension_id(
            f"https://chrome.google.com/webstore/detail/example/{extension_id}?hl=en"
        )
        == extension_id
    )


def test_browser_extension_manager_extracts_crx3_zip_payload():
    payload = b"PK\x03\x04zip-payload"
    header = b"metadata"
    crx = b"Cr24" + (3).to_bytes(4, "little") + len(header).to_bytes(4, "little") + header + payload

    assert _crx_zip_payload(crx) == payload


def test_browser_extension_manager_uses_modern_chrome_prodversion(monkeypatch):
    extension_id = "a" * 32

    assert _normalize_chrome_prodversion("Google Chrome 147.0.7727.55") == "147.0.7727.55"
    assert _normalize_chrome_prodversion("Chromium 124") == "124.0.0.0"

    monkeypatch.setenv("A0_BROWSER_EXTENSION_PRODVERSION", "147.0.7727.55")
    assert _detect_chrome_prodversion() == "147.0.7727.55"

    url = _build_web_store_download_url(extension_id, prodversion=_detect_chrome_prodversion())
    assert "prod=chromecrx" in url
    assert "prodversion=147.0.7727.55" in url
    assert "prodversion=120.0.0.0" not in url


def test_browser_extension_menu_exposes_agent_and_url_paths():
    html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html").read_text(
        encoding="utf-8"
    )
    skill = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "skills"
        / "browser-extension-control"
        / "SKILL.md"
    )

    assert "Create New Extension with A0" in html
    assert "+ Create New with A0" not in html
    assert "Input a Chrome Web Store URL" in html
    assert "My Browser Extensions" not in html
    assert "Browser LLM Preset" in html
    assert "Chrome Extensions" in html
    assert "Installed extensions" in html
    assert "deleteExtension(extension)" not in html
    assert "No extensions installed yet." not in html
    assert "Browser Extension Settings" not in html
    assert "<span>Settings</span>" in html
    assert "extensionHasOpenUi(extension)" in html
    assert "openExtensionUi(extension)" in html
    assert "<span>Open</span>" in html
    assert "hasExtensionInstallUrl()" in html
    assert "malicious or buggy extensions" in html
    assert skill.exists()


def test_browser_viewer_allows_slow_extension_startup():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )

    assert "const BROWSER_SUBSCRIBE_TIMEOUT_MS = 60000;" in js
    assert "const BROWSER_FIRST_INSTALL_TIMEOUT_MS = 300000;" in js
    assert "? BROWSER_FIRST_INSTALL_TIMEOUT_MS" in js
    assert ": BROWSER_SUBSCRIBE_TIMEOUT_MS" in js
    assert "Installing Chromium for the first Browser run" in js


def test_browser_viewer_creates_chat_when_no_context_is_selected():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )

    assert "async ensureContextId()" in js
    assert "async createChatContextForBrowser()" in js
    assert 'callJsonApi("/chat_create"' in js
    assert 'import { getContext, setContext } from "/index.js";' in js
    assert "setContext(contextId)" in js
    assert "chatsStore.setSelected?.(contextId)" in js
    assert "this.contextId = existingContextId;" in js
    assert "this.contextId = contextId;" in js
    assert "let targetContextId = requestedContextId" in js
    assert "|| this.resolveContextId();" in js
    assert "targetContextId = await this.ensureContextId();" in js
    assert "contextId: targetContextId" in js
    assert "No active chat context is selected." not in js


def test_browser_canvas_startup_waits_for_raw_viewport_settle():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )

    assert "const CANVAS_VIEWPORT_SETTLE_MS = 520;" in js
    assert "const SURFACE_VIEWPORT_STABLE_FRAMES = 4;" in js
    assert "const SURFACE_VIEWPORT_MAX_WAIT_MS = 1200;" in js
    assert "surfaceViewportMeasurement()" in js
    assert "rawWidth" in js
    assert "rawHeight" in js
    assert "const key = `${viewport.rawWidth}x${viewport.rawHeight}`;" in js
    assert "Date.now() - this._surfaceOpenedAt >= CANVAS_VIEWPORT_SETTLE_MS" in js
    assert "while (Date.now() - startedAt <= SURFACE_VIEWPORT_MAX_WAIT_MS)" in js
    assert "this._openPromise && this._openSignature === openSignature" in js
    assert "isCurrentSurfaceOpen(surfaceSequence)" in js
    assert "isCanvasSurfaceVisible(element)" in js
    assert "scheduleViewportSyncForSurface" in js
    assert "const targetChanged = Boolean(" in js
    assert "if (this.frameSrc && !targetChanged)" in js
    assert "this.cancelFrameRender();" in js
    assert "this.resetRenderedFrame();" in js


def test_browser_surface_handoffs_keep_existing_frame_until_replacement_arrives():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )
    prepare_start = js.index("prepareSurfaceOpen(nextMode")
    prepare_block = js[prepare_start: js.index("resetViewportTracking()", prepare_start)]
    viewport_start = js.index("resetRenderedFrameIfViewportChanged(viewport =")
    viewport_block = js[viewport_start: js.index("async waitForSurfaceViewport", viewport_start)]
    clear_start = js.index("clearRenderedFrameIfViewportChanged()")
    clear_block = js[clear_start: js.index("beginCommand()", clear_start)]

    assert "modeChanged" not in prepare_block
    assert "if (this.frameSrc && !targetChanged)" in prepare_block
    assert "this.resetRenderedFrame();" in prepare_block
    assert "this.cancelFrameRender();" in viewport_block
    assert "this.resetRenderedFrame();" not in viewport_block
    assert "this.cancelFrameRender();" in clear_block
    assert "this.resetRenderedFrame();" not in clear_block


def test_browser_canvas_surface_open_waits_for_visible_panel():
    js = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "right_canvas_register_surfaces"
        / "register-browser.js"
    ).read_text(encoding="utf-8")

    assert "waitForVisibleCanvasPanel" in js
    assert "isVisibleCanvasPanel(panel)" in js
    assert 'panel.closest(".browser-canvas-surface")' in js
    assert 'panel.querySelector(".browser-stage")' in js
    assert "getBoundingClientRect" in js
    assert "stableCount >= 2" in js
    assert "forceCanvasWidthNudgeAfterBrowserMount" not in js


def test_browser_canvas_nudges_width_after_first_accepted_frame():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )

    assert "_canvasSurfaceReadySequence" in js
    assert "_canvasFirstFrameAcceptedSequence" in js
    assert "_canvasFirstFrameNudgeSequence" in js
    assert "scheduleCanvasWidthNudgeAfterFirstFrame()" in js
    assert "this._canvasSurfaceReadySequence = surfaceSequence;" in js
    assert "const surfaceSequence = this._surfaceOpenSequence;" in js
    assert "this._canvasFirstFrameAcceptedSequence = surfaceSequence;" in js
    assert "forceRightCanvasWidthNudge()" in js
    assert "await nextAnimationFrame();" in js
    assert "globalThis.Alpine" not in js
    assert 'import { store as rightCanvasStore } from "/components/canvas/right-canvas-store.js";' in js
    assert "const canvas = rightCanvasStore;" in js
    assert 'canvas.activeSurfaceId !== "browser"' in js
    assert "canvas.setWidth?.(nudgedWidth, { persist: false })" in js
    assert "this.queueViewportSync(true)" in js
    frame_assignment_index = js.index("this.frameSrc = frameSrc;")
    frame_nudge_schedule_index = js.index(
        "this.scheduleCanvasWidthNudgeAfterFirstFrame();",
        frame_assignment_index,
    )
    assert frame_assignment_index < frame_nudge_schedule_index


def test_browser_canvas_restarts_stream_after_page_navigation():
    js = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )

    assert "async restartCanvasStreamAfterPageChange()" in js
    assert '["navigate", "back", "forward", "reload"].includes(commandName)' in js
    assert "await this.restartCanvasStreamAfterPageChange();" in js
    assert "await this.waitForSurfaceViewport({ sequence: surfaceSequence });" in js
    assert "await this.syncViewport(true, { restartStream: true });" in js
    reconnect_index = js.index("contextId: this.activeBrowserContextId")
    restart_index = js.index("await this.restartCanvasStreamAfterPageChange();")
    assert reconnect_index < restart_index


def test_browser_entry_points_prefer_canvas_and_modal_dock_handoff():
    browser_button_path = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "chat-input-bottom-actions-start"
        / "browser-button.html"
    )
    tool_handler = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "get_tool_message_handler"
        / "browser-tool-handler.js"
    ).read_text(encoding="utf-8")
    after_loop_handler = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "set_messages_after_loop"
        / "auto-open-browser-results.js"
    ).read_text(encoding="utf-8")
    register_js = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "surfaces_register"
        / "register-browser.js"
    ).read_text(encoding="utf-8")
    browser_store = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )
    canvas_store = (PROJECT_ROOT / "webui" / "components" / "canvas" / "right-canvas-store.js").read_text(
        encoding="utf-8"
    )
    modals_js = (PROJECT_ROOT / "webui" / "js" / "modals.js").read_text(encoding="utf-8")
    surfaces_js = (PROJECT_ROOT / "webui" / "js" / "surfaces.js").read_text(encoding="utf-8")

    assert not browser_button_path.exists()
    assert 'defaultOpenMode: "modal"' not in register_js
    assert "beginDockHandoff()" in register_js
    assert "beginSurfaceHandoff" in register_js
    assert "finishDockHandoff()" in register_js
    assert "cancelDockHandoff()" in register_js
    assert "defaultOpenMode" not in canvas_store
    assert "await surface.beginDockHandoff?.(payload)" in canvas_store
    assert "await this.closeDockSourceModal(payload, modalPath)" in canvas_store
    assert "delete openPayload.closeSourceModal" in canvas_store
    assert "await surface.finishDockHandoff?.({ ...openPayload, opened })" in canvas_store
    assert "await surface.cancelDockHandoff?.(payload)" in canvas_store
    assert "async closeDockSourceModal" in canvas_store

    assert "dock(metadata.surfaceId" in surfaces_js
    assert "button.disabled = true" in surfaces_js
    assert "dockSurface(metadata.surfaceId" not in modals_js

    assert "beginSurfaceHandoff()" in browser_store
    assert "finishSurfaceHandoff()" in browser_store
    assert "cancelSurfaceHandoff()" in browser_store
    assert "releaseSurfaceBindings()" in browser_store
    assert "this.releaseSurfaceBindings();" in browser_store

    assert "async function openBrowserSurface" in tool_handler
    assert 'await openSurface("browser", payload);' in tool_handler
    assert "rightCanvasStore" not in tool_handler
    assert "window.ensureModalOpen" not in tool_handler
    assert "window.openModal" not in tool_handler
    assert "function syncOpenBrowserCanvas" in tool_handler
    assert "async function syncOpenBrowserCanvas" in after_loop_handler
    assert "syncBrowserResultsIntoOpenCanvas" in after_loop_handler
    assert '${contextId || ""}' in tool_handler
    assert "contextId || \"\"" in after_loop_handler
    assert '"context_id"' in after_loop_handler
    assert '"contextId"' in after_loop_handler
    assert "rightCanvasStore" not in after_loop_handler
    assert "window.ensureModalOpen" not in after_loop_handler
    assert "window.openModal" not in after_loop_handler

    for js in (tool_handler, after_loop_handler):
        assert "openBrowserModal" not in js
        assert "isBrowserCanvasAlreadyOpen" in js
        assert '[data-surface-id="browser"].is-active .browser-panel' in js
        assert "autoOpenBrowserCanvas" not in js
        assert "autoOpenedBrowsers" not in js
        assert "syncedBrowserCanvases" in js
        assert "const FOCUS_ACTIONS = new Set" in js
        assert "FOCUS_ACTIONS.has(action)" in js

    assert 'id: "browser"' in surfaces_js
    assert "/plugins/_browser/webui/main.html" in surfaces_js

    for js in (tool_handler, after_loop_handler, register_js, browser_store, modals_js, surfaces_js):
        assert "globalThis.Alpine" not in js
        assert "Alpine?.store" not in js
        assert "Alpine.store" not in js


def test_browser_and_desktop_surface_buttons_remember_latest_window_mode():
    canvas_store = (PROJECT_ROOT / "webui" / "components" / "canvas" / "right-canvas-store.js").read_text(
        encoding="utf-8"
    )
    canvas_html = (PROJECT_ROOT / "webui" / "components" / "canvas" / "right-canvas.html").read_text(
        encoding="utf-8"
    )
    modals_js = (PROJECT_ROOT / "webui" / "js" / "modals.js").read_text(encoding="utf-8")
    modals_css = (PROJECT_ROOT / "webui" / "css" / "modals.css").read_text(encoding="utf-8")
    surfaces_js = (PROJECT_ROOT / "webui" / "js" / "surfaces.js").read_text(encoding="utf-8")
    surfaces_css = (PROJECT_ROOT / "webui" / "css" / "surfaces.css").read_text(encoding="utf-8")
    close_block = canvas_store[
        canvas_store.index("async close()"):
        canvas_store.index("async dockSurface")
    ]
    undock_block = canvas_store[
        canvas_store.index("async undockSurface"):
        canvas_store.index("async openModalSurface")
    ]
    open_modal_block = canvas_store[
        canvas_store.index("async openModalSurface"):
        canvas_store.index("async undockActiveSurface")
    ]
    surface_button_block = surfaces_js[
        surfaces_js.index("function createModalSurfaceButton"):
        surfaces_js.index("function configureModalSurfaceSwitcher")
    ]

    assert "surfaceModes: {}" in canvas_store
    assert "mountedSurfaces: {}" in canvas_store
    assert "recordSurfaceMode(surfaceId" in canvas_store
    assert "latestSurfaceMode(surfaceId)" in canvas_store
    assert "markSurfaceMounted(targetId)" in canvas_store
    assert "isSurfaceRendered(id)" in canvas_store
    assert "isSurfaceVisible(id)" in canvas_store
    assert "async openLatest(surfaceId" in canvas_store
    assert "async openModalSurface(surfaceId" in canvas_store
    assert "this.recordSurfaceMode(targetId, SURFACE_MODE_DOCKED" in canvas_store
    assert "this.recordSurfaceMode(targetId, SURFACE_MODE_FLOATING)" in canvas_store
    assert "surfaceModes: this.surfaceModes" in canvas_store
    assert "normalizeSurfaceMode(mode)" in canvas_store
    assert "migratePersistedSurfaceState" in canvas_store
    assert "this.mountedSurfaces = {}" not in close_block
    assert "surface?.close" not in close_block
    assert "this.mountedSurfaces = {}" not in undock_block
    assert "failed to close while undocking" not in undock_block
    assert "this.mountedSurfaces = {}" not in open_modal_block
    assert "failed to close before modal open" not in open_modal_block

    assert '@click="$store.rightCanvas.openLatest(surface.id)"' in canvas_html
    assert '@click="$store.rightCanvas.open(surface.id)"' in canvas_html

    assert "recordMode(metadata.surfaceId, SURFACE_MODE_FLOATING)" in surfaces_js
    assert "configureModalSurfaceSwitcher" in surfaces_js
    assert "surface-switcher" in surfaces_js
    assert "surface-button" in surfaces_js
    assert "SINGLE_VISIBLE_MODAL_SURFACE_PATHS" not in modals_js
    assert "modal-surface-parked" in surfaces_js
    assert "parkSiblingSurfaceModals(activeModal)" in surfaces_js
    assert "activateModal(modal)" in modals_js
    assert "closeSurfaceGroupModals" not in modals_js
    assert "closeSurfaceGroupModals" in surfaces_js
    assert "const closed = await closeSurfaceGroupModals()" in surfaces_js
    assert "globalThis.closeSurfaceGroupModals = closeSurfaceGroupModals" in surfaces_js
    assert "button.title = title" not in modals_js
    assert "button.title = metadata.title" not in modals_js
    assert "rightCanvasStore.panelSurfaces" not in modals_js
    assert 'await recordMode(normalizedId, SURFACE_MODE_FLOATING)' in surfaces_js
    assert "const openPromise = ensureModalOpen(targetModalPath)" in surface_button_block
    assert "await closeModal(modal.path)" not in surface_button_block
    assert "modalRequiresExplicitClose" in modals_js
    assert "modalSurfaceMetadata" not in modals_js
    assert "modal-content-loaded" in modals_js
    assert '"plugins/_browser/webui/main.html"' not in modals_js
    assert '"plugins/_office/webui/main.html"' not in modals_js
    assert "&& !modalRequiresExplicitClose(newModal)" in modals_js
    assert "if (modalRequiresExplicitClose(modalStack[modalStack.length - 1])) return;" in modals_js
    assert ".modal-surface-switcher" not in modals_css
    assert ".surface-switcher" in surfaces_css
    assert ".surface-button" in surfaces_css
    assert ".modal-surface-button.is-active" in surfaces_css
    assert ".modal-surface-image" in surfaces_css
    assert ".modal.modal-surface-parked" in surfaces_css
    assert "grid-auto-flow: column" in surfaces_css
    assert 'id: "browser"' in surfaces_js
    assert 'id: "desktop"' in surfaces_js
    assert "/plugins/_browser/webui/main.html" in surfaces_js
    assert "/plugins/_desktop/webui/main.html" in surfaces_js


def test_browser_tool_does_not_auto_open_canvas_policy_is_documented():
    prompt = (
        PROJECT_ROOT / "plugins" / "_browser" / "prompts" / "agent.system.tool.browser.md"
    ).read_text(encoding="utf-8")
    config = (PROJECT_ROOT / "plugins" / "_browser" / "default_config.yaml").read_text(
        encoding="utf-8"
    )
    config_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "config.html").read_text(
        encoding="utf-8"
    )

    assert "must not open a Browser surface automatically" in prompt
    assert "Use the tool headlessly unless the user opens the Browser surface" in prompt
    assert "optional visible WebUI viewer" in prompt
    assert "screenshot" in prompt
    assert "vision_load" in prompt
    assert "select_option" in prompt
    assert "set_checked" in prompt
    assert "upload_file" in prompt
    assert "browser-form-workflows" in prompt
    assert "does not automatically load screenshots" in prompt
    assert "chrome://inspect/#remote-debugging" in prompt
    assert "already open" in config
    assert "already-open Browser surface" in config_html
    assert "chrome://inspect/#remote-debugging" in config_html


def test_browser_forms_skill_is_plugin_owned_and_discoverable():
    skill_path = PROJECT_ROOT / "plugins" / "_browser" / "skills" / "browser-form-workflows" / "SKILL.md"
    assert skill_path.exists()
    skill = skill_path.read_text(encoding="utf-8")
    assert skill.startswith("---\n")
    frontmatter = skill.split("---", 2)[1]
    assert "name: browser-form-workflows" in frontmatter
    assert "description:" in frontmatter
    assert "select_option" in skill
    assert "set_checked" in skill
    assert "upload_file" in skill
    assert "browser:screenshot" in skill
    assert "vision_load" in skill


def test_browser_canvas_uses_plain_panel_without_debug_probe():
    panel_html = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "right-canvas-panels"
        / "browser-panel.html"
    ).read_text(encoding="utf-8")
    browser_store = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js").read_text(
        encoding="utf-8"
    )
    register_js = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "right_canvas_register_surfaces"
        / "register-browser.js"
    ).read_text(encoding="utf-8")
    canvas_store = (PROJECT_ROOT / "webui" / "components" / "canvas" / "right-canvas-store.js").read_text(
        encoding="utf-8"
    )
    modals_js = (PROJECT_ROOT / "webui" / "js" / "modals.js").read_text(encoding="utf-8")

    assert 'x-component path="/plugins/_browser/webui/browser-panel.html" mode="canvas"' in panel_html
    assert "browserCanvasRemountKey" not in panel_html
    assert "remountBrowserCanvasOnce" not in panel_html
    assert "data-remount-slot" not in panel_html

    for js in (browser_store, register_js, canvas_store, modals_js):
        assert "__a0BrowserDebug" not in js
        assert "browserDebug" not in js
        assert "emitBrowserDebug" not in js
        assert ".debug(" not in js


def test_browser_ui_spinners_have_browser_local_animation():
    main_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html").read_text(
        encoding="utf-8"
    )
    config_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "config.html").read_text(
        encoding="utf-8"
    )

    assert ":class=\"{ spinning: $store.browserPage.extensionActionLoading }\"" in main_html
    assert "@keyframes browser-spin" in main_html
    assert "@keyframes browser-config-spin" in config_html


def test_browser_extension_settings_stay_user_facing():
    config_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "config.html").read_text(
        encoding="utf-8"
    )
    config_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-config-store.js"
    ).read_text(encoding="utf-8")

    assert "Choose which installed Chrome extensions Browser loads." in config_html
    assert "Installed extensions" in config_html
    assert "extensionDeleteTitle(extension)" in config_html
    assert "deleteExtension(extension)" in config_html
    assert "Delete extension" in config_store
    assert "<textarea" not in config_html
    assert "Enabled extension directories" not in config_html
    assert "Chrome Web Store URL installs" not in config_html
    assert "Browser caches Playwright Chromium" not in config_html


def test_browser_viewer_uses_tabs_for_session_switching():
    main_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html").read_text(
        encoding="utf-8"
    )
    browser_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js"
    ).read_text(encoding="utf-8")

    assert 'class="browser-session-tabs" role="tablist"' in main_html
    assert 'class="browser-tab"' in main_html
    assert 'class="browser-new-tab"' in main_html
    assert ':key="$store.browserPage.browserTabKey(browser)"' in main_html
    assert "browser.context_id" in main_html
    assert ':title="$store.browserPage.browserTabTooltip(browser)"' in main_html
    assert "browser-tab-context" not in main_html
    assert 'handleSelectedContextChange($store.chats?.selected)' in main_html
    assert "activeBrowserContextId" in browser_store
    assert "sameBrowserTab" in browser_store
    assert "applyBrowserListing" in browser_store
    assert "syncViewerToSelectedContext(selectedContextId)" in browser_store
    assert "async syncViewerToSelectedContext" in browser_store
    assert "isVisibleBrowserSurface()" in browser_store
    assert "firstBrowserInContext(selectedContextId)" in browser_store
    assert "requestedContextId && requestedContextId !== inFlightContextId" in browser_store
    assert "create_browser: Boolean(options.createBrowser || options.create_browser)" in browser_store
    assert "browserTabTooltip(browser)" in browser_store
    assert "browserChatTitle(browser = {})" in browser_store
    assert "contextId.slice" not in browser_store
    assert '"browser_viewer_sessions"' in browser_store
    assert "$store.browserPage.openNewBrowser()" in main_html
    assert "browser-select" not in main_html
    assert "browser-live-dot" not in main_html
    assert "async openNewBrowser()" in browser_store
    assert "browserTabTitle(browser)" in browser_store
    assert "Scan with A0" in browser_store
    assert "Review with A0" not in browser_store
    assert "Using ${this.mainModelSummary}" in browser_store


def test_browser_tabs_close_without_confirmation_or_busy_lock():
    main_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html").read_text(
        encoding="utf-8"
    )
    browser_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js"
    ).read_text(encoding="utf-8")
    close_start = main_html.index('class="browser-tab-close"')
    close_end = main_html.index("</button>", close_start)
    close_markup = main_html[close_start:close_end]

    assert '@click.stop="$store.browserPage.closeBrowser(browser.id, browser.context_id)"' in main_html
    assert "@pointerdown.stop" in close_markup
    assert "$confirmClick" not in main_html
    assert "isBusy()" not in close_markup
    assert ':disabled="$store.browserPage.isClosingBrowser(browser.id, browser.context_id)"' in close_markup
    assert "--browser-tab-close-size: 32px;" in main_html
    assert "async closeBrowser(id, contextId = \"\")" in browser_store
    assert "isClosingBrowser(id, contextId = \"\")" in browser_store
    assert "_closingBrowserIds" in browser_store
    assert "_commandInFlightCount" in browser_store


def test_browser_viewer_uses_cdp_screencast_transport():
    ws_browser = (PROJECT_ROOT / "plugins" / "_browser" / "api" / "ws_browser.py").read_text(
        encoding="utf-8"
    )
    main_html = (PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html").read_text(
        encoding="utf-8"
    )
    runtime = (
        PROJECT_ROOT / "plugins" / "_browser" / "helpers" / "runtime.py"
    ).read_text(encoding="utf-8")
    browser_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js"
    ).read_text(encoding="utf-8")
    browser_tool_handler = (
        PROJECT_ROOT / "plugins" / "_browser" / "extensions" / "webui" / "get_tool_message_handler" / "browser-tool-handler.js"
    ).read_text(encoding="utf-8")

    assert 'runtime.call("screenshot"' in ws_browser
    assert "SCREENCAST_QUALITY = 92" in ws_browser
    assert "initial_viewport = self._viewport_from_data(data)" in ws_browser
    assert '"set_viewport"' in ws_browser
    assert "start_screencast" in ws_browser
    assert "pop_screencast_frame" in ws_browser
    assert "stop_screencast" in ws_browser
    assert '"Page.startScreencast"' in runtime
    assert '"Page.screencastFrame"' in runtime
    assert '"Page.screencastFrameAck"' in runtime
    assert '"Page.stopScreencast"' in runtime
    assert '"Emulation.setDeviceMetricsOverride"' in runtime
    assert '"Emulation.setVisibleSize"' in runtime
    assert "asyncio.Queue(maxsize=1)" in runtime
    assert "await self._stop_screencasts_for_browser(resolved_id)" in runtime
    assert "queueFrameRender" in browser_store
    assert "requestAnimationFrame" in browser_store
    assert "viewport_width: initialViewport?.width" in browser_store
    assert "viewport_height: initialViewport?.height" in browser_store
    assert "restart_stream: restartStream" in browser_store
    assert 'restart_screencast=bool(data.get("restart_stream"))' in ws_browser
    assert "restart_screencast: bool = False" in runtime
    assert "should_remount_viewport = changed or restart_screencast" in runtime
    assert "VIEWPORT_REMOUNT_PAUSE_SECONDS = 0.05" in runtime
    assert "await self._apply_cdp_viewport_with_remount" in runtime
    assert "await self._apply_viewport_with_remount(page, viewport)" in runtime
    assert "await self._remount_viewport(page, viewport)" in runtime
    assert "await asyncio.sleep(VIEWPORT_REMOUNT_PAUSE_SECONDS)" in runtime
    assert "def _nudged_viewport(viewport: dict[str, int])" in runtime
    assert 'await this.syncViewport(true, { restartStream: this._mode === "canvas" });' in browser_store
    assert "this.frameState = data.state || null" not in browser_store
    assert "function loadFrameDimensions(src)" in browser_store
    assert "frameMatchesViewport(dimensions = null, viewport = null)" in browser_store
    assert "shouldAcceptMismatchedFrame(dimensions = null)" in browser_store
    assert "requestViewportSyncAfterRejectedFrame()" in browser_store
    assert "this.applySnapshot(data.snapshot);" in browser_store
    assert "else if (!data.state)" in browser_store
    assert '"snapshot": snapshot' in ws_browser
    assert 'const BROWSER_SNAPSHOT_META_KEY = "browser_snapshot";' in browser_tool_handler
    assert "staticScreenshotUri(kvps)" in browser_tool_handler
    assert "delete displayKvps[BROWSER_SNAPSHOT_META_KEY];" in browser_tool_handler
    assert "startBrowserScreenshotPreview(button, image, resolveBrowserPayload)" in browser_tool_handler
    assert "FRAME_FALLBACK_SCREENSHOT_SECONDS" not in ws_browser
    assert '"frame_source": "state"' in ws_browser
    assert '"frame_source"] = "screencast"' in ws_browser
    assert "fallback_screenshot" not in ws_browser
    assert "canvas_wheel_screenshot" not in ws_browser
    assert "surface_mode: this._mode" not in browser_store
    assert "overflow: hidden;" in main_html
    assert "object-fit: fill;" in main_html
    assert "image-rendering: auto;" in main_html


def test_browser_navigation_errors_stay_inside_native_browser_page():
    runtime = (
        PROJECT_ROOT / "plugins" / "_browser" / "helpers" / "runtime.py"
    ).read_text(encoding="utf-8")

    assert "Error as PlaywrightError" in runtime
    assert "except PlaywrightError as exc:" in runtime
    assert "Browser navigation showed a native error page" in runtime
    assert "await self._settle(page)" in runtime
    assert "except (PlaywrightError, PlaywrightTimeoutError):" in runtime


def test_browser_annotate_mode_ui_and_prompt_hooks():
    panel_html = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html"
    ).read_text(encoding="utf-8")
    browser_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js"
    ).read_text(encoding="utf-8")

    assert "Annotate" in panel_html
    assert "Annotating" in panel_html
    assert "browser-annotation-layer" in panel_html
    assert "browser-annotation-tray" in panel_html
    assert "annotationTrayStyle()" in panel_html
    assert "startAnnotationTrayDrag($event)" in panel_html
    assert "Draft to chat" in panel_html
    assert "Send now" in panel_html
    assert "@pointerdown.stop.prevent=\"$store.browserPage.startAnnotationSelection($event)\"" in panel_html
    assert "@keydown.window=\"$store.browserPage.handleKeydown($event)\"" in panel_html
    assert "annotationComments: []" in browser_store
    assert "annotationTrayPosition: null" in browser_store
    assert "clampAnnotationTrayPosition" in browser_store
    assert '"browser_viewer_annotation"' in browser_store
    assert 'event?.key === "." && (event.metaKey || event.ctrlKey)' in browser_store
    assert "Browser annotations" in browser_store
    assert "Comment:" in browser_store
    assert "Coordinates:" in browser_store
    assert "Selector:" in browser_store
    assert "DOM:" in browser_store
    assert "value=\\\"[redacted]\\\"" in browser_store


def test_browser_visual_mode_bridges_clipboard_shortcuts():
    browser_store = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-store.js"
    ).read_text(encoding="utf-8")
    runtime = (
        PROJECT_ROOT / "plugins" / "_browser" / "helpers" / "runtime.py"
    ).read_text(encoding="utf-8")
    ws_browser = (
        PROJECT_ROOT / "plugins" / "_browser" / "api" / "ws_browser.py"
    ).read_text(encoding="utf-8")

    assert 'import { copyToClipboard } from "/components/messages/action-buttons/simple-action-buttons.js";' in browser_store
    assert "BROWSER_VISUAL_SHORTCUT_KEYS" in browser_store
    assert "handleVisualBrowserShortcut(event)" in browser_store
    assert "visualBrowserStageForEvent(event)" in browser_store
    assert "isLocalEditableTarget(event?.target)" in browser_store
    assert 'return { action: "paste" };' in browser_store
    assert 'return { action: "copy" };' in browser_store
    assert 'return { action: "cut" };' in browser_store
    assert 'return { key: "Control+A" };' in browser_store
    assert 'return { key: shift ? "Control+Shift+Z" : "Control+Z" };' in browser_store
    assert 'input_type: "clipboard"' in browser_store
    assert "pasteHostClipboardToBrowser()" in browser_store
    assert "copyBrowserClipboardToHost" in browser_store
    assert "Browser paste needs clipboard permission in this tab." in browser_store

    assert "CLIPBOARD_BRIDGE_SCRIPT" in runtime
    assert "async def clipboard" in runtime
    assert "insertFromPaste" in runtime
    assert "deleteByCut" in runtime
    assert "keyboard.insert_text" in runtime
    assert 'input_type == "clipboard"' in ws_browser
    assert 'runtime.call(\n                    "clipboard"' in ws_browser


def test_browser_runtime_and_content_helper_expose_annotation_target():
    runtime = (
        PROJECT_ROOT / "plugins" / "_browser" / "helpers" / "runtime.py"
    ).read_text(encoding="utf-8")
    helper = (
        PROJECT_ROOT / "plugins" / "_browser" / "assets" / "browser-page-content.js"
    ).read_text(encoding="utf-8")

    assert "async def annotation_target" in runtime
    assert "globalThis.__spaceBrowserPageContent__.annotate(payload || null)" in runtime
    assert "function annotate(payload = null)" in helper
    assert "annotate," in helper
    assert "boundingBoxFor," in helper
    assert "pointFor," in helper
    assert "select(referenceId, valueOrValues)" in helper
    assert "setChecked(referenceId, checked)" in helper
    assert "fileInputFor," in helper
    assert "sanitizeAnnotationDom" in helper
    assert "password" in helper


def test_browser_content_helper_keeps_label_wrapped_controls_referenceable():
    helper = (
        PROJECT_ROOT / "plugins" / "_browser" / "assets" / "browser-page-content.js"
    ).read_text(encoding="utf-8")

    assert 'const VERSION = "12"' in helper
    assert "function patchOpenShadowDom" in helper
    assert "Element.prototype.attachShadow = patched" in helper
    assert "const REQUIRED_API_NAMES = Object.freeze([" in helper
    assert "requiredApis: REQUIRED_API_NAMES.slice()" in helper
    assert "ready()" in helper
    for api_name in ("click", "scroll", "submit", "type", "typeSubmit"):
        assert f'"{api_name}"' in helper
    assert "function renderControlLabelReferences" in helper
    assert "getLabelElementText(labelElement, element)" in helper
    assert "return renderControlLabelReferences(node, context);" in helper
    assert "return renderControlLabelReferences(element, context);" in helper
    assert "function isGlobalOrDelegatedEventBinding" in helper
    assert 'parts.includes("window")' in helper
    assert 'parts.includes("outside")' in helper


def test_browser_panel_exposes_agent_friendly_address_input():
    panel = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-panel.html"
    ).read_text(encoding="utf-8")

    assert 'class="browser-address-form" aria-label="Browser navigation"' in panel
    assert 'class="browser-address" aria-label="Browser address" name="browser_address"' in panel


def test_browser_runtime_requires_current_content_helper_for_modifier_clicks():
    runtime = (
        PROJECT_ROOT / "plugins" / "_browser" / "helpers" / "runtime.py"
    ).read_text(encoding="utf-8")

    assert "__spaceBrowserPageContent__?.ready?.()" in runtime


@pytest.mark.anyio
async def test_browser_screencast_acknowledges_and_drops_stale_frames():
    first_image = SMALL_JPEG_10X10

    class FakeSession:
        def __init__(self):
            self.handlers = {}
            self.sent = []
            self.detached = False

        def on(self, event, handler):
            self.handlers[event] = handler

        async def send(self, method, params=None):
            self.sent.append((method, params or {}))

        async def detach(self):
            self.detached = True

    session = FakeSession()
    screencast = _BrowserScreencast(
        stream_id="stream",
        browser_id=7,
        session=session,
        mime="image/jpeg",
    )

    await screencast.start(quality=92, every_nth_frame=1, viewport={"width": 1118, "height": 662})
    session.handlers["Page.screencastFrame"](
        {"data": first_image, "metadata": {"deviceWidth": 10}, "sessionId": 1}
    )
    session.handlers["Page.screencastFrame"](
        {"data": "second", "metadata": {"deviceWidth": 200}, "sessionId": 2}
    )
    await asyncio.sleep(0)

    frame = await screencast.next_frame(timeout=0.1)

    assert frame["browser_id"] == 7
    assert frame["image"] == "second"
    assert frame["metadata"]["deviceWidth"] == 200
    assert frame["metadata"]["expectedWidth"] == 1118
    assert frame["metadata"]["expectedHeight"] == 662
    metrics_calls = [
        params
        for method, params in session.sent
        if method == "Emulation.setDeviceMetricsOverride"
    ]
    visible_calls = [
        params
        for method, params in session.sent
        if method == "Emulation.setVisibleSize"
    ]
    assert metrics_calls[:3] == [
        {
            "width": 1118,
            "height": 662,
            "deviceScaleFactor": 1,
            "mobile": False,
            "dontSetVisibleSize": True,
        },
        {
            "width": 1119,
            "height": 662,
            "deviceScaleFactor": 1,
            "mobile": False,
            "dontSetVisibleSize": True,
        },
        {
            "width": 1118,
            "height": 662,
            "deviceScaleFactor": 1,
            "mobile": False,
            "dontSetVisibleSize": True,
        },
    ]
    assert visible_calls[:3] == [
        {"width": 1118, "height": 662},
        {"width": 1119, "height": 662},
        {"width": 1118, "height": 662},
    ]
    start_index = next(
        index
        for index, (method, _params) in enumerate(session.sent)
        if method == "Page.startScreencast"
    )
    cdp_viewport_indices = [
        index
        for index, (method, _params) in enumerate(session.sent)
        if method.startswith("Emulation.")
    ]
    assert max(cdp_viewport_indices) < start_index
    assert ("Page.screencastFrameAck", {"sessionId": 1}) in session.sent
    assert ("Page.screencastFrameAck", {"sessionId": 2}) in session.sent

    await screencast.stop()

    assert ("Page.stopScreencast", {}) in session.sent
    assert session.detached is True


@pytest.mark.anyio
async def test_browser_screencast_passes_wrong_viewport_frames_to_frontend_validator():
    class FakeSession:
        def __init__(self):
            self.handlers = {}
            self.sent = []

        def on(self, event, handler):
            self.handlers[event] = handler

        async def send(self, method, params=None):
            self.sent.append((method, params or {}))

        async def detach(self):
            pass

    session = FakeSession()
    screencast = _BrowserScreencast(
        stream_id="stream",
        browser_id=7,
        session=session,
        mime="image/jpeg",
    )

    await screencast.start(quality=92, every_nth_frame=1, viewport={"width": 1118, "height": 662})
    for session_id in range(1, 14):
        session.handlers["Page.screencastFrame"](
            {"data": SMALL_JPEG_10X10, "metadata": {}, "sessionId": session_id}
        )
    await asyncio.sleep(0)

    frame = await screencast.pop_frame()

    assert frame is not None
    assert frame["image"] == SMALL_JPEG_10X10
    assert frame["metadata"]["jpegWidth"] == 10
    assert frame["metadata"]["jpegHeight"] == 10
    assert frame["metadata"]["expectedWidth"] == 1118
    assert frame["metadata"]["expectedHeight"] == 662
    assert ("Page.screencastFrameAck", {"sessionId": 13}) in session.sent

    await screencast.stop()


def test_browser_docker_installs_full_chromium_to_tmp_cache():
    script = (
        PROJECT_ROOT / "docker" / "run" / "fs" / "ins" / "install_playwright.sh"
    ).read_text(encoding="utf-8")

    assert "PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright" in script
    assert "playwright install chromium" in script
    assert "--only-shell" not in script


def test_browser_startup_migration_runs_playwright_cache_cleanup():
    extension = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "python"
        / "startup_migration"
        / "_20_browser_playwright_cache.py"
    ).read_text(encoding="utf-8")

    assert "class BrowserPlaywrightCacheMigration(Extension)" in extension
    assert "hooks.cleanup_playwright_cache()" in extension
    assert "PrintStyle.warning" in extension


def test_browser_runtime_removes_stale_profile_singletons(monkeypatch, tmp_path):
    monkeypatch.setattr(
        browser_runtime_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )
    core = _BrowserRuntimeCore("stale-profile")
    core.profile_dir.mkdir(parents=True)

    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        (core.profile_dir / name).symlink_to("missing-host-999999")

    core._release_orphaned_profile_singleton()

    assert not any(
        (core.profile_dir / name).exists() or (core.profile_dir / name).is_symlink()
        for name in ("SingletonLock", "SingletonCookie", "SingletonSocket")
    )


@pytest.mark.anyio
async def test_browser_runtime_restarts_when_cached_context_is_stale():
    starts = []
    stopped = []

    class StaleContext:
        @property
        def pages(self):
            raise RuntimeError("Target page, context or browser has been closed")

    class LiveContext:
        pages = []

    class FakePlaywright:
        async def stop(self):
            stopped.append(True)

    core = _BrowserRuntimeCore("ctx")
    core.context = StaleContext()
    core.playwright = FakePlaywright()
    core.pages[4] = browser_runtime_module.BrowserPage(id=4, page=object())
    core.last_interacted_browser_id = 4

    async def fake_start():
        starts.append(True)
        core.context = LiveContext()

    core._start = fake_start

    await core.ensure_started()

    assert starts == [True]
    assert stopped == [True]
    assert isinstance(core.context, LiveContext)
    assert core.pages == {}
    assert core.last_interacted_browser_id is None


def test_browser_runtime_context_close_event_clears_cached_state():
    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[4] = browser_runtime_module.BrowserPage(id=4, page=object())
    core.last_interacted_browser_id = 4

    core._on_context_closed()

    assert core.context is None
    assert core.pages == {}
    assert core.last_interacted_browser_id is None


def test_browser_save_plugin_config_restarts_runtimes_on_change(monkeypatch, tmp_path):
    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()
    restarted = []

    monkeypatch.setattr(
        browser_hooks_module,
        "_load_saved_browser_config",
        lambda project_name="", agent_profile="": {
            "extension_paths": [],
        },
    )
    monkeypatch.setattr(
        browser_hooks_module,
        "close_all_runtimes_sync",
        lambda: restarted.append(True),
    )

    result = browser_hooks_module.save_plugin_config(
        {
            "extension_paths": [str(extension_dir)],
        },
        project_name="",
        agent_profile="",
    )

    assert result["extension_paths"] == [str(extension_dir)]
    assert result["model_preset"] == ""
    assert restarted == [True]


def test_browser_save_plugin_config_does_not_restart_runtimes_for_preset_only(monkeypatch):
    restarted = []

    monkeypatch.setattr(
        browser_hooks_module,
        "_load_saved_browser_config",
        lambda project_name="", agent_profile="": {
            "extension_paths": [],
            "model_preset": "",
        },
    )
    monkeypatch.setattr(
        browser_hooks_module,
        "close_all_runtimes_sync",
        lambda: restarted.append(True),
    )

    result = browser_hooks_module.save_plugin_config(
        {
            "extension_paths": [],
            "model_preset": "Research",
        },
        project_name="",
        agent_profile="",
    )

    assert result["model_preset"] == "Research"
    assert restarted == []


@pytest.mark.anyio
async def test_browser_tool_dispatches_direct_actions(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args):
            calls.append((method, args))
            if method == "content":
                return {"document": "[link 1] Example"}
            return {"ok": True, "method": method, "args": args}

    async def fake_get_runtime(context_id, create=True, agent=None):
        del create, agent
        assert context_id == "ctx"
        return FakeRuntime()

    monkeypatch.setattr(browser_tool_module, "get_runtime", fake_get_runtime)
    agent = SimpleNamespace(context=SimpleNamespace(id="ctx"))
    tool = browser_tool_module.Browser(
        agent=agent,
        name="browser",
        method=None,
        args={},
        message="",
        loop_data=None,
    )

    response = await tool.execute(action="content", browser_id=1)

    assert response.message == "[link 1] Example"
    assert calls == [("content", (1, None))]


@pytest.mark.anyio
async def test_browser_tool_dispatches_v1_agent_actions(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            return {"ok": True, "method": method, "args": args, "kwargs": kwargs}

    async def fake_get_runtime(context_id, create=True, agent=None):
        del create, agent
        assert context_id == "ctx"
        return FakeRuntime()

    monkeypatch.setattr(browser_tool_module, "get_runtime", fake_get_runtime)
    agent = SimpleNamespace(context=SimpleNamespace(id="ctx"))

    async def execute(**kwargs):
        tool = browser_tool_module.Browser(
            agent=agent,
            name="browser",
            method=kwargs.pop("_method", None),
            args={},
            message="",
            loop_data=None,
        )
        response = await tool.execute(**kwargs)
        assert response.break_loop is False

    await execute(action="screenshot", browser_id=1, quality=91, full_page=True, path="/tmp/a.jpg")
    await execute(action="hover", browser_id=1, ref=2, offset_x=3, offset_y=4)
    await execute(action="double_click", browser_id=1, x=10, y=20, button="left", modifiers=["Shift"])
    await execute(action="right_click", browser_id=1, ref=3, modifiers="Control")
    await execute(action="drag", browser_id=1, ref=4, target_ref=5, target_offset_x=6, target_offset_y=7)
    await execute(action="wheel", browser_id=1, x=8, y=9, delta_x=1, delta_y=2)
    await execute(action="keyboard", browser_id=1, key="Enter")
    await execute(_method="clipboard", action="paste", browser_id=1, text="hello")
    await execute(action="copy", browser_id=1)
    await execute(action="set_viewport", browser_id=1, width=1280, height=720)
    await execute(action="select_option", browser_id=1, ref=6, value="CA")
    await execute(action="set_checked", browser_id=1, ref=7, checked=False)
    await execute(action="upload_file", browser_id=1, ref=8, paths=["/tmp/a.txt"])
    await execute(action="key_chord", browser_id=1, keys="CTRL+A")
    await execute(action="click", browser_id=1, x=10, y=20)
    await execute(action="type", browser_id=1, text="agent-zero.ai")

    assert calls == [
        ("screenshot_file", (1,), {"quality": 91, "full_page": True, "path": "/tmp/a.jpg"}),
        ("hover", (1,), {"ref": 2, "x": 0.0, "y": 0.0, "offset_x": 3, "offset_y": 4}),
        (
            "double_click",
            (1,),
            {
                "ref": None,
                "x": 10,
                "y": 20,
                "button": "left",
                "modifiers": ["Shift"],
                "offset_x": 0.0,
                "offset_y": 0.0,
            },
        ),
        (
            "right_click",
            (1,),
            {
                "ref": 3,
                "x": 0.0,
                "y": 0.0,
                "modifiers": ["Control"],
                "offset_x": 0.0,
                "offset_y": 0.0,
            },
        ),
        (
            "drag",
            (1,),
            {
                "ref": 4,
                "target_ref": 5,
                "x": 0.0,
                "y": 0.0,
                "to_x": 0.0,
                "to_y": 0.0,
                "offset_x": 0.0,
                "offset_y": 0.0,
                "target_offset_x": 6,
                "target_offset_y": 7,
            },
        ),
        ("wheel", (1, 8, 9, 1, 2), {}),
        ("keyboard", (1,), {"key": "Enter", "text": ""}),
        ("clipboard", (1,), {"action": "paste", "text": "hello"}),
        ("clipboard", (1,), {"action": "copy", "text": ""}),
        ("set_viewport", (1, 1280, 720), {}),
        ("select_option", (1, 6), {"value": "CA", "values": None}),
        ("set_checked", (1, 7), {"checked": False}),
        ("upload_file", (1, 8), {"path": "", "paths": ["/tmp/a.txt"]}),
        ("key_chord", (1, ["Control", "A"]), {}),
        ("mouse", (1, "click", 10, 20), {"button": "left", "modifiers": None}),
        ("keyboard", (1,), {"key": "", "text": "agent-zero.ai"}),
    ]


@pytest.mark.anyio
async def test_browser_tool_resolves_selector_for_reference_actions(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            if method == "content":
                return {"input.browser-address": "[input text 31] Browser address"}
            return {"ok": True, "method": method, "args": args, "kwargs": kwargs}

    async def fake_get_runtime(context_id, create=True, agent=None):
        del create, agent
        assert context_id == "ctx"
        return FakeRuntime()

    monkeypatch.setattr(browser_tool_module, "get_runtime", fake_get_runtime)
    tool = browser_tool_module.Browser(
        agent=SimpleNamespace(context=SimpleNamespace(id="ctx")),
        name="browser",
        method=None,
        args={},
        message="",
        loop_data=None,
    )

    response = await tool.execute(
        action="type_submit",
        browser_id=1,
        selector="input.browser-address",
        text="agent-zero.ai",
    )

    assert response.break_loop is False
    assert calls == [
        ("content", (1, {"selector": "input.browser-address"}), {}),
        ("type_submit", (1, "31", "agent-zero.ai"), {}),
    ]


@pytest.mark.anyio
async def test_browser_runtime_multi_accepts_human_shaped_input_calls():
    calls = []
    core = _BrowserRuntimeCore("ctx")

    async def fake_mouse(browser_id, event_type, x, y, *, button="left", modifiers=None):
        calls.append(("mouse", browser_id, event_type, x, y, button, modifiers))
        return {"ok": True}

    async def fake_keyboard(browser_id, *, key="", text=""):
        calls.append(("keyboard", browser_id, key, text))
        return {"ok": True}

    async def fake_key_chord(browser_id, keys):
        calls.append(("key_chord", browser_id, keys))
        return {"ok": True}

    core.mouse = fake_mouse
    core.keyboard = fake_keyboard
    core.key_chord = fake_key_chord

    assert await core._dispatch_call({"action": "click", "browser_id": 1, "x": 10, "y": 20}) == {"ok": True}
    assert await core._dispatch_call({"action": "type", "browser_id": 1, "text": "agent-zero.ai"}) == {"ok": True}
    assert await core._dispatch_call({"action": "key_chord", "browser_id": 1, "keys": "CTRL+A"}) == {"ok": True}

    assert calls == [
        ("mouse", 1, "click", 10.0, 20.0, "left", None),
        ("keyboard", 1, "", "agent-zero.ai"),
        ("key_chord", 1, ["Control", "A"]),
    ]


@pytest.mark.anyio
async def test_browser_tool_records_static_history_screenshot(monkeypatch, tmp_path):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            if method == "open":
                return {
                    "id": 1,
                    "state": {
                        "id": 1,
                        "context_id": "browser-context",
                        "currentUrl": "https://example.com/",
                        "title": "Example Domain",
                    },
                }
            if method == "screenshot_file":
                Path(kwargs["path"]).parent.mkdir(parents=True, exist_ok=True)
                Path(kwargs["path"]).write_bytes(b"jpeg")
                return {
                    "browser_id": args[0],
                    "path": kwargs["path"],
                    "a0_path": "/a0/usr/chats/chat/browser/screenshots/open.jpg",
                    "mime": "image/jpeg",
                    "state": {"id": args[0], "context_id": "browser-context"},
                }
            raise AssertionError(method)

    async def fake_get_runtime(context_id, create=True, agent=None):
        del create, agent
        assert context_id == "chat"
        return FakeRuntime()

    class FakeLog:
        id = "tool-log-id"

        def __init__(self):
            self.updates = []

        def update(self, **kwargs):
            self.updates.append(kwargs)

    monkeypatch.setattr(browser_tool_module, "get_runtime", fake_get_runtime)
    monkeypatch.setitem(
        sys.modules,
        "helpers.persist_chat",
        SimpleNamespace(
            get_chat_folder_path=lambda context_id: str(tmp_path / "usr" / "chats" / context_id)
        ),
    )

    log = FakeLog()
    tool = browser_tool_module.Browser(
        agent=SimpleNamespace(context=SimpleNamespace(id="chat")),
        name="browser",
        method=None,
        args={"action": "open", "url": "https://example.com"},
        message="",
        loop_data=None,
    )
    tool.log = log

    response = await tool.execute(action="open", url="https://example.com")

    assert response.break_loop is False
    assert calls[0] == ("open", ("https://example.com",), {})
    assert calls[1][0] == "screenshot_file"
    assert calls[1][1] == (1,)
    assert calls[1][2]["quality"] == browser_tool_module.HISTORY_SCREENSHOT_QUALITY
    assert calls[1][2]["full_page"] is False
    assert Path(calls[1][2]["path"]).parent == tmp_path / "usr" / "chats" / "chat" / "browser" / "screenshots"
    assert Path(calls[1][2]["path"]).read_bytes() == b"jpeg"
    assert log.updates[-1]["Screenshot"].startswith("img://")
    assert log.updates[-1]["browser_snapshot"]["browser_id"] == 1
    assert log.updates[-1]["browser_snapshot"]["context_id"] == "browser-context"


@pytest.mark.anyio
async def test_browser_multi_dispatch_accepts_v1_actions():
    calls = []
    core = _BrowserRuntimeCore("ctx")

    async def record(method):
        async def inner(*args, **kwargs):
            calls.append((method, args, kwargs))
            return {"method": method}
        return inner

    for method in (
        "screenshot_file",
        "hover",
        "double_click",
        "right_click",
        "drag",
        "wheel",
        "keyboard",
        "clipboard",
        "set_viewport",
        "select_option",
        "set_checked",
        "upload_file",
    ):
        setattr(core, method, await record(method))

    results = await core.multi(
        [
            {"action": "screenshot", "browser_id": 1, "quality": 5, "full_page": True},
            {"action": "hover", "browser_id": 1, "ref": 2},
            {"action": "double_click", "browser_id": 1, "x": 1, "y": 2},
            {"action": "right_click", "browser_id": 1, "ref": 3},
            {"action": "drag", "browser_id": 1, "ref": 4, "target_ref": 5},
            {"action": "wheel", "browser_id": 1, "delta_y": 100},
            {"action": "keyboard", "browser_id": 1, "key": "Enter"},
            {"action": "paste", "browser_id": 1, "text": "x"},
            {"action": "set_viewport", "browser_id": 1, "width": 640, "height": 480},
            {"action": "select_option", "browser_id": 1, "ref": 6, "values": ["a", "b"]},
            {"action": "set_checked", "browser_id": 1, "ref": 7, "checked": False},
            {"action": "upload_file", "browser_id": 1, "ref": 8, "path": "/tmp/file.txt"},
        ]
    )

    assert all(result["ok"] for result in results)
    assert [call[0] for call in calls] == [
        "screenshot_file",
        "hover",
        "double_click",
        "right_click",
        "drag",
        "wheel",
        "keyboard",
        "clipboard",
        "set_viewport",
        "select_option",
        "set_checked",
        "upload_file",
    ]


@pytest.mark.anyio
async def test_browser_viewer_subscribe_unregisters_stream(monkeypatch):
    class FakeRuntime:
        def __init__(self) -> None:
            self.opened = False

        async def call(self, method, *args):
            if method == "list":
                if self.opened:
                    return {
                        "browsers": [{"id": 1, "currentUrl": "about:blank", "title": ""}],
                        "last_interacted_browser_id": 1,
                    }
                return {"browsers": [], "last_interacted_browser_id": None}
            if method == "open":
                self.opened = True
                return {"id": 1, "state": {"id": 1, "currentUrl": "about:blank"}}
            raise AssertionError(method)

    fake_runtime = FakeRuntime()

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return fake_runtime

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(
        ws_browser_module.AgentContext,
        "get",
        staticmethod(lambda context_id: SimpleNamespace(id=context_id)),
    )

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_subscribe",
        {"context_id": "ctx", "correlationId": "c1"},
        "sid-1",
    )

    assert result["context_id"] == "ctx"
    assert result["active_browser_id"] is None
    assert fake_runtime.opened is False
    assert ("sid-1", "ctx") in ws_browser_module.WsBrowser._streams

    await handler.on_disconnect("sid-1")

    assert ("sid-1", "ctx") not in ws_browser_module.WsBrowser._streams


@pytest.mark.anyio
async def test_browser_viewer_subscribe_can_create_blank_tab_when_requested(monkeypatch):
    class FakeRuntime:
        def __init__(self) -> None:
            self.opened = False

        async def call(self, method, *args):
            if method == "list":
                if self.opened:
                    return {
                        "browsers": [{"id": 1, "currentUrl": "about:blank", "title": ""}],
                        "last_interacted_browser_id": 1,
                    }
                return {"browsers": [], "last_interacted_browser_id": None}
            if method == "open":
                self.opened = True
                return {"id": 1, "state": {"id": 1, "currentUrl": "about:blank"}}
            raise AssertionError(method)

    fake_runtime = FakeRuntime()

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is True
        return fake_runtime

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(
        ws_browser_module.AgentContext,
        "get",
        staticmethod(lambda context_id: SimpleNamespace(id=context_id)),
    )

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_subscribe",
        {"context_id": "ctx", "create_browser": True},
        "sid-create",
    )

    assert result["active_browser_id"] == 1
    assert fake_runtime.opened is True

    await handler.on_disconnect("sid-create")


@pytest.mark.anyio
async def test_browser_viewer_subscribe_returns_initial_snapshot(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            if method == "list":
                return {
                    "browsers": [{"id": 1, "context_id": "ctx", "currentUrl": "https://example.com/"}],
                    "last_interacted_browser_id": 1,
                }
            if method == "set_viewport":
                return {"state": {"id": args[0], "currentUrl": "https://example.com/"}}
            if method == "screenshot":
                return {
                    "browser_id": args[0],
                    "mime": "image/jpeg",
                    "image": "jpeg-data",
                    "state": {"id": args[0], "context_id": "ctx", "currentUrl": "https://example.com/"},
                }
            raise AssertionError(method)

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return FakeRuntime()

    async def fake_all_browser_tabs():
        return [{"id": 1, "context_id": "ctx", "currentUrl": "https://example.com/"}]

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(ws_browser_module, "list_runtime_sessions", fake_all_browser_tabs)
    monkeypatch.setattr(
        ws_browser_module.AgentContext,
        "get",
        staticmethod(lambda context_id: SimpleNamespace(id=context_id)),
    )

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_subscribe",
        {"context_id": "ctx", "browser_id": 1, "viewport_width": 900, "viewport_height": 600},
        "sid-snapshot",
    )

    assert result["active_browser_id"] == 1
    assert result["snapshot"]["image"] == "jpeg-data"
    assert ("screenshot", (1,), {"quality": ws_browser_module.SCREENCAST_QUALITY}) in calls

    await handler.on_disconnect("sid-snapshot")


@pytest.mark.anyio
async def test_browser_viewer_subscribe_without_runtime_does_not_create_runtime(monkeypatch):
    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return None

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(
        ws_browser_module.AgentContext,
        "get",
        staticmethod(lambda context_id: SimpleNamespace(id=context_id)),
    )

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_subscribe",
        {"context_id": "ctx"},
        "sid-empty",
    )

    assert result["active_browser_id"] is None
    assert result["browsers"] == []
    assert ("sid-empty", "ctx") not in ws_browser_module.WsBrowser._streams


@pytest.mark.anyio
async def test_browser_runtime_sessions_are_context_qualified(monkeypatch):
    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            assert method == "list"
            return {
                "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "https://example.com/"}],
                "last_interacted_browser_id": 1,
            }

    with browser_runtime_module._runtime_lock:
        previous_runtimes = dict(browser_runtime_module._runtimes)
        browser_runtime_module._runtimes.clear()
        browser_runtime_module._runtimes["ctx-a"] = FakeRuntime()
    try:
        sessions = await list_runtime_sessions()
    finally:
        with browser_runtime_module._runtime_lock:
            browser_runtime_module._runtimes.clear()
            browser_runtime_module._runtimes.update(previous_runtimes)

    assert sessions == [
        {
            "context_id": "ctx-a",
            "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "https://example.com/"}],
            "last_interacted_browser_id": 1,
        }
    ]


@pytest.mark.anyio
async def test_browser_runtime_refuses_new_tabs_when_context_limit_is_reached(monkeypatch):
    core = _BrowserRuntimeCore("ctx-limit")
    core.pages = {
        1: BrowserPage(1, SimpleNamespace()),
        2: BrowserPage(2, SimpleNamespace()),
    }

    async def fake_ensure_started():
        return None

    monkeypatch.setattr(core, "ensure_started", fake_ensure_started)
    monkeypatch.setattr(
        browser_runtime_module,
        "get_browser_config",
        lambda: {"max_open_tabs": 2, "default_homepage": "about:blank"},
    )

    with pytest.raises(RepairableException, match="Browser tab limit reached"):
        await core.open("https://example.com/")


@pytest.mark.anyio
async def test_browser_viewer_command_returns_tabs_from_all_contexts(monkeypatch):
    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            if method == "list":
                return {
                    "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "about:blank"}],
                    "last_interacted_browser_id": 1,
                }
            raise AssertionError(method)

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx-a"
        return FakeRuntime()

    async def fake_list_runtime_sessions():
        return [
            {
                "context_id": "ctx-a",
                "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "about:blank"}],
                "last_interacted_browser_id": 1,
            },
            {
                "context_id": "ctx-b",
                "browsers": [{"id": 1, "context_id": "ctx-b", "currentUrl": "https://example.org/"}],
                "last_interacted_browser_id": 1,
            },
        ]

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(ws_browser_module, "list_runtime_sessions", fake_list_runtime_sessions)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_command",
        {"context_id": "ctx-a", "command": "list"},
        "sid-1",
    )

    assert result["all_browsers"] is True
    assert result["active_browser_context_id"] == "ctx-a"
    assert [browser["context_id"] for browser in result["browsers"]] == ["ctx-a", "ctx-b"]


@pytest.mark.anyio
async def test_browser_viewer_sessions_lists_without_creating_runtime(monkeypatch):
    async def fake_list_runtime_sessions():
        return [
            {
                "context_id": "ctx-a",
                "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "about:blank"}],
                "last_interacted_browser_id": 1,
            }
        ]

    async def fail_get_runtime(*args, **kwargs):
        raise AssertionError("sessions refresh must not create or fetch one runtime")

    monkeypatch.setattr(ws_browser_module, "list_runtime_sessions", fake_list_runtime_sessions)
    monkeypatch.setattr(ws_browser_module, "get_runtime", fail_get_runtime)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_sessions",
        {"context_id": "ctx-b"},
        "sid-1",
    )

    assert result == {
        "context_id": "ctx-b",
        "browsers": [{"id": 1, "context_id": "ctx-a", "currentUrl": "about:blank"}],
        "all_browsers": True,
    }


@pytest.mark.anyio
async def test_browser_viewer_viewport_input_dispatches_resize(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            return {"ok": True, "method": method, "args": args}

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return FakeRuntime()

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_input",
        {
            "context_id": "ctx",
            "browser_id": 7,
            "input_type": "viewport",
            "width": 1280,
            "height": 720,
            "restart_stream": True,
        },
        "sid-1",
    )

    assert result == {
        "state": {"ok": True, "method": "set_viewport", "args": (7, 1280, 720)},
        "snapshot": None,
    }
    assert calls == [
        ("set_viewport", (7, 1280, 720), {"restart_screencast": True})
    ]


@pytest.mark.anyio
async def test_browser_runtime_remounts_same_viewport_when_restarting_screencast():
    viewport_calls = []
    stopped = []
    settled = []

    class FakePage:
        viewport_size = {"width": 1280, "height": 720}

        async def set_viewport_size(self, viewport):
            viewport_calls.append(dict(viewport))

    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[7] = browser_runtime_module.BrowserPage(id=7, page=FakePage())

    async def fake_stop_screencasts(browser_id):
        stopped.append(browser_id)

    async def fake_settle(page, short=False):
        settled.append(short)

    async def fake_state(browser_id):
        return {"id": browser_id}

    core._stop_screencasts_for_browser = fake_stop_screencasts
    core._settle = fake_settle
    core._state = fake_state

    result = await core.set_viewport(7, 1280, 720, restart_screencast=True)

    assert result == {
        "state": {"id": 7},
        "viewport": {"width": 1280, "height": 720},
    }
    assert viewport_calls == [
        {"width": 1281, "height": 720},
        {"width": 1280, "height": 720},
    ]
    assert stopped == [7]
    assert settled == [True]


@pytest.mark.anyio
async def test_browser_runtime_remounts_initial_changed_viewport():
    calls = []
    stopped = []
    settled = []

    class FakePage:
        viewport_size = {"width": 1024, "height": 768}

        async def set_viewport_size(self, viewport):
            calls.append(("viewport", dict(viewport)))

    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[7] = browser_runtime_module.BrowserPage(id=7, page=FakePage())

    async def fake_stop_screencasts(browser_id):
        stopped.append(browser_id)

    async def fake_settle(page, short=False):
        settled.append(short)

    async def fake_state(browser_id):
        return {"id": browser_id}

    core._stop_screencasts_for_browser = fake_stop_screencasts
    core._settle = fake_settle
    core._state = fake_state

    result = await core.set_viewport(7, 672, 789)

    assert result == {
        "state": {"id": 7},
        "viewport": {"width": 672, "height": 789},
    }
    assert calls == [
        ("viewport", {"width": 672, "height": 789}),
        ("viewport", {"width": 673, "height": 789}),
        ("viewport", {"width": 672, "height": 789}),
    ]
    assert stopped == [7]
    assert settled == [True]


@pytest.mark.anyio
async def test_browser_runtime_screenshot_file_writes_without_base64(monkeypatch, tmp_path):
    screenshot_calls = []

    def fake_get_abs_path(*parts):
        return str(tmp_path.joinpath(*parts))

    def fake_normalize_a0_path(path):
        return "/a0/" + str(Path(path).relative_to(tmp_path)).replace("\\", "/")

    monkeypatch.setattr(browser_runtime_module.files, "get_abs_path", fake_get_abs_path)
    monkeypatch.setattr(browser_runtime_module.files, "normalize_a0_path", fake_normalize_a0_path)

    class FakePage:
        url = "about:blank"
        viewport_size = {"width": 1024, "height": 768}

        async def screenshot(self, **kwargs):
            screenshot_calls.append(kwargs)
            Path(kwargs["path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(kwargs["path"]).write_bytes(b"image-bytes")
            return b"image-bytes"

        async def title(self):
            return "Blank"

        async def evaluate(self, script, payload=None):
            return 1

    core = _BrowserRuntimeCore("ctx/id")
    core.context = object()
    core.pages[5] = browser_runtime_module.BrowserPage(id=5, page=FakePage())

    result = await core.screenshot_file(5, quality=500)

    path = Path(result["path"])
    assert path.exists()
    assert path.parent == tmp_path / "tmp" / "browser" / "screenshots" / "ctx_id"
    assert path.name.startswith("browser-5-")
    assert path.suffix == ".jpg"
    assert result["a0_path"].startswith("/a0/tmp/browser/screenshots/ctx_id/browser-5-")
    assert result["mime"] == "image/jpeg"
    assert result["vision_load"] == {
        "tool_name": "vision_load",
        "tool_args": {"paths": [result["path"]]},
    }
    assert "image" not in result
    assert screenshot_calls[-1]["type"] == "jpeg"
    assert screenshot_calls[-1]["quality"] == 95
    assert screenshot_calls[-1]["full_page"] is False

    png_path = tmp_path / "custom.png"
    png_result = await core.screenshot_file(5, quality=1, full_page=True, path=str(png_path))

    assert png_result["path"] == str(png_path)
    assert png_result["mime"] == "image/png"
    assert screenshot_calls[-1] == {
        "path": str(png_path),
        "type": "png",
        "full_page": True,
    }


@pytest.mark.anyio
async def test_browser_runtime_ref_point_resolution_applies_offsets():
    eval_payloads = []
    moves = []

    class FakeMouse:
        async def move(self, x, y, **kwargs):
            moves.append((x, y, kwargs))

    class FakePage:
        url = "about:blank"

        def __init__(self):
            self.mouse = FakeMouse()

        async def evaluate(self, script, payload=None):
            eval_payloads.append((script, payload))
            if payload and "offsets" in payload:
                return {
                    "x": 10 + payload["offsets"]["offset_x"],
                    "y": 20 + payload["offsets"]["offset_y"],
                    "rect": {"x": 10, "y": 20, "width": 100, "height": 40},
                    "selector": "#target",
                }
            return 1

        async def title(self):
            return "Blank"

    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[7] = browser_runtime_module.BrowserPage(id=7, page=FakePage())
    core._ensure_content_helper = lambda _page: asyncio.sleep(0)

    result = await core.hover(7, ref=4, offset_x=3, offset_y=5)

    assert moves == [(13.0, 25.0, {})]
    assert result["action"]["point"]["selector"] == "#target"
    assert eval_payloads[0][1] == {
        "ref": 4,
        "offsets": {
            "offset_x": 3.0,
            "offset_y": 5.0,
            "useOffsets": True,
        },
    }


def test_browser_runtime_upload_path_normalization(monkeypatch, tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")

    monkeypatch.setattr(
        browser_runtime_module.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )

    assert _BrowserRuntimeCore._normalize_upload_paths(path=str(first)) == [str(first)]
    assert _BrowserRuntimeCore._normalize_upload_paths(paths=["second.txt"]) == [str(second)]
    assert _BrowserRuntimeCore._normalize_upload_paths(path=str(first), paths=["second.txt"]) == [
        str(second),
        str(first),
    ]


@pytest.mark.anyio
async def test_browser_runtime_clipboard_paste_uses_dom_bridge():
    eval_payloads = []
    settled = []

    class FakeKeyboard:
        def __init__(self):
            self.inserted = []

        async def insert_text(self, text):
            self.inserted.append(text)

    class FakePage:
        url = "about:blank"

        def __init__(self):
            self.keyboard = FakeKeyboard()

        async def evaluate(self, script, payload=None):
            if payload is not None:
                eval_payloads.append((script, payload))
                return {
                    "action": "paste",
                    "text": payload["text"],
                    "changed": True,
                    "default_prevented": False,
                }
            return 1

        async def title(self):
            return "Blank"

    page = FakePage()
    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[7] = browser_runtime_module.BrowserPage(id=7, page=page)

    async def fake_settle(_page, short=False):
        settled.append(short)

    core._settle = fake_settle

    result = await core.clipboard(7, action="paste", text="hello")

    assert result["state"]["id"] == 7
    assert result["clipboard"]["changed"] is True
    assert result["clipboard"]["text"] == "hello"
    assert eval_payloads[0][1] == {"action": "paste", "text": "hello"}
    assert "insertFromPaste" in eval_payloads[0][0]
    assert page.keyboard.inserted == []
    assert settled == [True]


@pytest.mark.anyio
async def test_browser_runtime_clipboard_paste_falls_back_to_keyboard_insert_text():
    class FakeKeyboard:
        def __init__(self):
            self.inserted = []

        async def insert_text(self, text):
            self.inserted.append(text)

    class FakePage:
        url = "about:blank"

        def __init__(self):
            self.keyboard = FakeKeyboard()

        async def evaluate(self, script, payload=None):
            if payload is not None:
                return {
                    "action": "paste",
                    "text": payload["text"],
                    "changed": False,
                    "default_prevented": False,
                }
            return 1

        async def title(self):
            return "Blank"

    page = FakePage()
    core = _BrowserRuntimeCore("ctx")
    core.context = object()
    core.pages[7] = browser_runtime_module.BrowserPage(id=7, page=page)
    core._settle = lambda _page, short=False: asyncio.sleep(0)

    result = await core.clipboard(7, action="paste", text="hello")

    assert result["clipboard"]["changed"] is True
    assert result["clipboard"]["method"] == "keyboard.insert_text"
    assert page.keyboard.inserted == ["hello"]


@pytest.mark.anyio
async def test_browser_viewer_wheel_input_dispatches_scroll(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            return {"ok": True, "method": method, "args": args}

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return FakeRuntime()

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_input",
        {
            "context_id": "ctx",
            "browser_id": 3,
            "input_type": "wheel",
            "x": 320,
            "y": 480,
            "delta_x": 0,
            "delta_y": 640,
        },
        "sid-1",
    )

    assert result == {
        "state": {"ok": True, "method": "wheel", "args": (3, 320.0, 480.0, 0.0, 640.0)},
        "snapshot": None,
    }
    assert calls == [("wheel", (3, 320.0, 480.0, 0.0, 640.0), {})]


@pytest.mark.anyio
async def test_browser_viewer_clipboard_input_dispatches_runtime(monkeypatch):
    calls = []
    clipboard = {"action": "paste", "text": "hello", "changed": True}

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            return {
                "state": {"id": args[0], "currentUrl": "about:blank"},
                "clipboard": clipboard,
            }

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return FakeRuntime()

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    result = await handler.process(
        "browser_viewer_input",
        {
            "context_id": "ctx",
            "browser_id": 3,
            "input_type": "clipboard",
            "action": "paste",
            "text": "hello",
        },
        "sid-1",
    )

    assert result == {
        "state": {"id": 3, "currentUrl": "about:blank"},
        "clipboard": clipboard,
        "snapshot": None,
    }
    assert calls == [
        ("clipboard", (3,), {"action": "paste", "text": "hello"})
    ]


@pytest.mark.anyio
async def test_browser_viewer_annotation_dispatches_runtime(monkeypatch):
    calls = []

    class FakeRuntime:
        async def call(self, method, *args, **kwargs):
            calls.append((method, args, kwargs))
            return {
                "kind": "element",
                "point": {"x": 320, "y": 180},
                "target": {"tagName": "BUTTON", "selector": "#save"},
            }

    async def fake_get_runtime(context_id, create=True):
        assert context_id == "ctx"
        assert create is False
        return FakeRuntime()

    monkeypatch.setattr(ws_browser_module, "get_runtime", fake_get_runtime)

    handler = ws_browser_module.WsBrowser(
        SimpleNamespace(),
        threading.RLock(),
        manager=None,
    )

    payload = {
        "kind": "element",
        "point": {"x": 320, "y": 180},
        "viewport": {"width": 1280, "height": 720},
    }
    result = await handler.process(
        "browser_viewer_annotation",
        {
            "context_id": "ctx",
            "browser_id": 4,
            "viewer_id": "viewer-1",
            "payload": payload,
        },
        "sid-1",
    )

    assert result == {
        "annotation": {
            "kind": "element",
            "point": {"x": 320, "y": 180},
            "target": {"tagName": "BUTTON", "selector": "#save"},
        },
        "context_id": "ctx",
        "browser_id": 4,
        "viewer_id": "viewer-1",
    }
    assert calls == [("annotation_target", (4, payload), {})]


def test_browser_runtime_normalizes_multi_group_ids_and_modifiers():
    core = _BrowserRuntimeCore("ctx")

    assert core._multi_group_key({"browser_id": 7}) == 7
    assert core._multi_group_key({"browser_id": "7"}) == 7
    assert core._multi_group_key({"browser_id": "browser-7"}) == 7
    assert core._multi_group_key({"browser_id": ""}) is None
    assert core._normalize_modifiers("Control") == ["Control"]
    assert core._normalize_modifiers(["Control", " Shift "]) == ["Control", "Shift"]
    assert core._normalize_modifiers([]) is None

    with pytest.raises(ValueError):
        core._normalize_modifiers("Ctrl")


def test_browser_runtime_background_focus_restores_previous_active_tab():
    core = _BrowserRuntimeCore("ctx")
    core.pages[1] = browser_runtime_module.BrowserPage(id=1, page=object())
    core.pages[2] = browser_runtime_module.BrowserPage(id=2, page=object())

    assert core._background_focus_target(previous_focus=1, fallback_id=2) == 1

    core.pages.pop(1)

    assert core._background_focus_target(previous_focus=1, fallback_id=2) == 2


def test_browser_cleanup_extensions_follow_extensible_path_layout():
    extension = __import__("helpers.extension", fromlist=["_get_extension_classes"])
    remove_classes = extension._get_extension_classes(  # type: ignore[attr-defined]
        "_functions/agent/AgentContext/remove/start"
    )
    reset_classes = extension._get_extension_classes(  # type: ignore[attr-defined]
        "_functions/agent/AgentContext/reset/start"
    )

    assert any(cls.__name__ == "CleanupBrowserRuntimeOnRemove" for cls in remove_classes)
    assert any(cls.__name__ == "CleanupBrowserRuntimeOnReset" for cls in reset_classes)


def test_legacy_browser_dependency_is_removed():
    assert not (PROJECT_ROOT / "plugins" / ("_browser" + "_agent")).exists()
    assert ("browser" + "-use") not in (PROJECT_ROOT / "requirements.txt").read_text(
        encoding="utf-8"
    )
