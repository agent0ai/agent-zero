from __future__ import annotations

import asyncio
import importlib
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._browser.helpers.config import (
    ExtensionBrowserSelection,
    normalize_host_browser_selection,
    normalize_browser_config,
    parse_extension_browser_selection,
    validate_extension_browser_selection_change,
)
from plugins._browser.helpers import selector as browser_selector
from plugins._a0_connector.helpers import browser_bridge_selection

BRIDGE_ID = "b6ce74df-47e6-4a3d-b8dd-3f3fae0e79d2"


def _agent(context_id: str = "ctx-extension-foundation"):
    return SimpleNamespace(context=SimpleNamespace(id=context_id))


@contextmanager
def _load_browser_runtime_api(monkeypatch: pytest.MonkeyPatch):
    class Response:
        def __init__(self, *, response: str, status: int, mimetype: str) -> None:
            self.response = response
            self.status = status
            self.mimetype = mimetype

    api_stub = ModuleType("helpers.api")
    api_stub.Request = object
    api_stub.Response = Response
    base_stub = ModuleType("plugins._a0_connector.api.v1.base")
    base_stub.ProtectedConnectorApiHandler = object

    module_name = "plugins._a0_connector.api.v1.browser_runtime"
    previous = sys.modules.pop(module_name, None)
    try:
        with monkeypatch.context() as context:
            context.setitem(sys.modules, "helpers.api", api_stub)
            context.setitem(sys.modules, "plugins._a0_connector.api.v1.base", base_stub)
            yield importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous


def test_valid_extension_selection_is_typed_and_preserved_exactly():
    value = f"extension:{BRIDGE_ID}"

    assert (
        normalize_browser_config({"host_browser_selection": f"  {value}  "})[
            "host_browser_selection"
        ]
        == value
    )
    assert parse_extension_browser_selection(value) == ExtensionBrowserSelection(
        value=value,
        bridge_id=BRIDGE_ID,
    )
    assert parse_extension_browser_selection("chrome-cdp") is None
    assert parse_extension_browser_selection("extenſion:123") is None
    assert normalize_host_browser_selection(value) == value


def test_bridge_selection_is_derived_from_exact_context_agent_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent import AgentContext
    from plugins._browser.helpers import config as browser_config

    context = SimpleNamespace(id="context-A")
    agent = SimpleNamespace(context=context)
    context.agent0 = agent
    monkeypatch.setattr(
        AgentContext,
        "get",
        staticmethod(lambda context_id: context if context_id == context.id else None),
    )
    current = {
        "runtime_backend": "host_required",
        "host_browser_selection": "extension:bridge-A",
    }
    monkeypatch.setattr(
        browser_config,
        "get_browser_config",
        lambda *, agent: dict(current),
    )

    assert browser_bridge_selection.selected_bridge("context-A") == "bridge-A"
    assert browser_bridge_selection.selection_current("context-A", "bridge-A")
    assert not browser_bridge_selection.selection_current("context-A", "bridge-B")
    assert browser_bridge_selection.selected_bridge("context-missing") is None
    current["runtime_backend"] = "container"
    assert browser_bridge_selection.selected_bridge("context-A") is None
    current["runtime_backend"] = "host_required"
    current["host_browser_selection"] = "chrome-cdp"
    assert browser_bridge_selection.selected_bridge("context-A") is None


def test_instance_rollout_gate_is_not_persisted_in_project_browser_config() -> None:
    normalized = normalize_browser_config({"browser_bridge_rollout": "available"})

    assert "browser_bridge_rollout" not in normalized


def test_project_config_save_validation_blocks_new_extension_selection() -> None:
    with pytest.raises(ValueError, match="pairing and activation"):
        validate_extension_browser_selection_change(
            proposed_value="extension:Bridge-Case-1",
            current_value="chrome-cdp",
            proposed_runtime_backend="container",
            current_runtime_backend="container",
        )
    with pytest.raises(ValueError, match="reserved extension"):
        validate_extension_browser_selection_change(
            proposed_value="extension:",
            current_value="",
            proposed_runtime_backend="container",
            current_runtime_backend="container",
        )
    with pytest.raises(ValueError, match="reserved extension"):
        validate_extension_browser_selection_change(
            proposed_value="Extension:bad/id",
            current_value="extension:",
            proposed_runtime_backend="container",
            current_runtime_backend="container",
        )


def test_project_config_save_validation_allows_preservation_and_deactivation() -> None:
    selection = "extension:Bridge-Case-1"

    validate_extension_browser_selection_change(
        proposed_value=selection,
        current_value=selection,
        proposed_runtime_backend="container",
        current_runtime_backend="container",
    )
    validate_extension_browser_selection_change(
        proposed_value="",
        current_value=selection,
        proposed_runtime_backend="host_required",
        current_runtime_backend="host_required",
    )


def test_project_config_save_validation_blocks_backend_only_activation() -> None:
    selection = "extension:Bridge-Case-1"

    with pytest.raises(ValueError, match="pairing and activation"):
        validate_extension_browser_selection_change(
            proposed_value=selection,
            current_value=selection,
            proposed_runtime_backend="host_required",
            current_runtime_backend="container",
        )


def test_connector_api_rejects_valid_extension_before_save(monkeypatch) -> None:
    with _load_browser_runtime_api(monkeypatch) as runtime_api:
        handler = runtime_api.BrowserRuntime.__new__(runtime_api.BrowserRuntime)
        handler._project_name_for_context = lambda _context_id: ""
        handler._load_browser_config = lambda _project: {
            "runtime_backend": "container",
            "host_browser_profile_mode": "existing",
            "host_browser_selection": "",
        }
        handler._save_browser_config = lambda *_args: pytest.fail(
            "unavailable extension selection was saved"
        )
        selection = "extension:Bridge-Case-1"

        response = asyncio.run(
            handler.process(
                {
                    "action": "set",
                    "runtime_backend": "host_required",
                    "host_browser_selection": selection,
                },
                request=None,
            )
        )

    assert response.status == 400
    assert "browser_extension_bridge_unavailable" in response.response


def test_connector_api_rejects_malformed_extension_before_save(monkeypatch) -> None:
    with _load_browser_runtime_api(monkeypatch) as runtime_api:
        handler = runtime_api.BrowserRuntime.__new__(runtime_api.BrowserRuntime)
        handler._project_name_for_context = lambda _context_id: ""
        handler._load_browser_config = lambda _project: {
            "runtime_backend": "container",
            "host_browser_profile_mode": "existing",
            "host_browser_selection": "",
        }
        handler._save_browser_config = lambda *_args: pytest.fail(
            "malformed extension selection was saved"
        )

        response = asyncio.run(
            handler.process(
                {
                    "action": "set",
                    "runtime_backend": "host_required",
                    "host_browser_selection": "extension:bad/id",
                },
                request=None,
            )
        )

    assert response.status == 400
    assert "invalid_extension_browser_selection" in response.response


def test_connector_api_rejects_backend_only_activation_of_stored_extension(
    monkeypatch,
) -> None:
    with _load_browser_runtime_api(monkeypatch) as runtime_api:
        handler = runtime_api.BrowserRuntime.__new__(runtime_api.BrowserRuntime)
        handler._project_name_for_context = lambda _context_id: ""
        handler._load_browser_config = lambda _project: {
            "runtime_backend": "container",
            "host_browser_profile_mode": "existing",
            "host_browser_selection": "extension:Bridge-Case-1",
        }
        handler._save_browser_config = lambda *_args: pytest.fail(
            "backend-only extension activation was saved"
        )

        response = asyncio.run(
            handler.process(
                {"action": "set", "runtime_backend": "host_required"},
                request=None,
            )
        )

    assert response.status == 400
    assert "browser_extension_bridge_unavailable" in response.response


def test_connector_api_allows_extension_deactivation_with_echoed_selection(
    monkeypatch,
) -> None:
    with _load_browser_runtime_api(monkeypatch) as runtime_api:
        handler = runtime_api.BrowserRuntime.__new__(runtime_api.BrowserRuntime)
        stored: dict[str, object] = {}
        handler._project_name_for_context = lambda _context_id: ""
        handler._load_browser_config = lambda _project: {
            "runtime_backend": "host_required",
            "host_browser_profile_mode": "existing",
            "host_browser_selection": "extension:Bridge-Case-1",
        }
        handler._save_browser_config = lambda _project, settings: stored.update(settings)

        response = asyncio.run(
            handler.process(
                {
                    "action": "set",
                    "runtime_backend": "container",
                    "host_browser_selection": "extension:Bridge-Case-1",
                },
                request=None,
            )
        )

    assert response["runtime_backend"] == "container"
    assert stored["runtime_backend"] == "container"
    assert stored["host_browser_selection"] == "extension:Bridge-Case-1"


@pytest.mark.parametrize(
    "value",
    [
        "extension",
        "extension:",
        "Extension:b6ce74df-47e6-4a3d-b8dd-3f3fae0e79d2",
        "extension: bridge-id",
        "extension:bridge/id",
        "extension:bridge:id",
        "extension:bridge\x00id",
        "extension\x00:bridge-id",
    ],
)
def test_malformed_reserved_selection_stays_reserved_and_non_routable(value: str):
    normalized = normalize_browser_config({"host_browser_selection": value})[
        "host_browser_selection"
    ]

    assert normalized == "extension:"
    with pytest.raises(ValueError):
        parse_extension_browser_selection(normalized)


@pytest.mark.parametrize(
    ("selection", "message"),
    [
        (f"extension:{BRIDGE_ID}", "has not established a verified connection"),
        ("extension:", "selection is invalid"),
    ],
)
def test_extension_selection_fails_closed_before_any_runtime_candidate(
    monkeypatch: pytest.MonkeyPatch,
    selection: str,
    message: str,
):
    monkeypatch.setattr(
        browser_selector,
        "get_browser_config",
        lambda agent=None: {
            "runtime_backend": "host_required",
            "host_browser_selection": selection,
        },
    )
    monkeypatch.setattr(
        browser_selector,
        "_select_host_browser_candidate_sid",
        lambda context_id: pytest.fail(
            "extension selection consulted a legacy candidate"
        ),
    )

    async def unexpected_container_runtime(context_id: str):
        pytest.fail("extension selection fell back to the container runtime")

    monkeypatch.setattr(
        browser_selector,
        "get_container_runtime",
        unexpected_container_runtime,
    )

    with pytest.raises(browser_selector.RepairableException, match=message) as exc_info:
        asyncio.run(browser_selector.get_tool_runtime(_agent()))

    assert "did not fall back" in str(exc_info.value)


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_browser_settings_preserve_valid_extension_identity_exactly() -> None:
    source = (
        PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-config-store.js"
    ).read_text(encoding="utf-8")
    source = re.sub(r"^import .*;\n", "", source, flags=re.M)
    source = source.replace("export const store = createStore", "const store = createStore")
    selection = "extension:Bridge-Case-1"
    numeric_selection = "extension:123"
    unicode_lookalike = "extenſion:123"
    script = (
        "const createStore = (_name, value) => value;\n"
        "const callJsonApi = async () => ({});\n"
        "const showConfirmDialog = async () => false;\n"
        + source
        + f"\nconst config = ensureConfig({{ host_browser_selection: {selection!r} }});\n"
        + f"if (config.host_browser_selection !== {selection!r}) "
        + "throw new Error('extension ID changed');\n"
        + f"if (normalizeHostBrowserSelection({numeric_selection!r}) "
        + f"!== {numeric_selection!r}) throw new Error('numeric extension ID changed');\n"
        + f"if (isCustomHostBrowserEndpoint({numeric_selection!r})) "
        + "throw new Error('extension ID treated as endpoint');\n"
        + f"if (normalizeHostBrowserSelection({unicode_lookalike!r}) "
        + f"!== {unicode_lookalike!r}) throw new Error('prefix parity changed');\n"
        + "if (normalizeHostBrowserSelection('Extension:Bridge-Case-1') "
        + "!== 'extension:') throw new Error('invalid namespace did not fail closed');\n"
    )

    subprocess.run(["node", "--input-type=module", "-e", script], check=True, text=True)


def test_container_backend_still_ignores_host_selection(
    monkeypatch: pytest.MonkeyPatch,
):
    expected_runtime = object()
    monkeypatch.setattr(
        browser_selector,
        "get_browser_config",
        lambda agent=None: {
            "runtime_backend": "container",
            "host_browser_selection": f"extension:{BRIDGE_ID}",
        },
    )

    async def container_runtime(context_id: str):
        assert context_id == "ctx-container"
        return expected_runtime

    monkeypatch.setattr(browser_selector, "get_container_runtime", container_runtime)

    assert (
        asyncio.run(browser_selector.get_tool_runtime(_agent("ctx-container")))
        is expected_runtime
    )


@pytest.mark.parametrize("selection", ["", "chrome-cdp"])
def test_empty_and_legacy_host_selection_keep_current_connector_path(
    monkeypatch: pytest.MonkeyPatch,
    selection: str,
):
    monkeypatch.setattr(
        browser_selector,
        "get_browser_config",
        lambda agent=None: {
            "runtime_backend": "host_required",
            "host_browser_selection": selection,
        },
    )
    monkeypatch.setattr(
        browser_selector,
        "_select_host_browser_candidate_sid",
        lambda context_id: "sid-legacy",
    )

    connector_runtime_module = ModuleType("plugins._browser.helpers.connector_runtime")

    class ConnectorBrowserRuntime:
        def __init__(self, context_id, agent):
            self.context_id = context_id
            self.agent = agent

    connector_runtime_module.ConnectorBrowserRuntime = ConnectorBrowserRuntime
    monkeypatch.setitem(
        sys.modules,
        "plugins._browser.helpers.connector_runtime",
        connector_runtime_module,
    )

    runtime = asyncio.run(browser_selector.get_tool_runtime(_agent("ctx-legacy")))

    assert isinstance(runtime, ConnectorBrowserRuntime)
    assert runtime.context_id == "ctx-legacy"
