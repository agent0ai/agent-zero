import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plugins._browser_agent.helpers.browser_use_monkeypatch as browser_use_monkeypatch
import plugins._browser_agent.tools.browser_agent as browser_agent_module


def test_gemini_clean_and_conform_normalizes_known_single_action_shapes():
    raw = (
        '{"action":['
        '{"complete_task":{"title":"T","response":"R","page_summary":"S"}}'
        ']}'
    )

    cleaned = browser_use_monkeypatch.gemini_clean_and_conform(raw)

    assert cleaned is not None
    parsed = json.loads(cleaned)
    assert parsed["action"] == [
        {
            "done": {
                "success": True,
                "data": {
                    "title": "T",
                    "response": "R",
                    "page_summary": "S",
                },
            }
        },
    ]


class DummyBrowserSession:
    def __init__(self) -> None:
        self.kill_called = False
        self.close_called = False

    async def kill(self) -> None:
        self.kill_called = True

    async def close(self) -> None:
        self.close_called = True


class DummyAgent:
    def __init__(self) -> None:
        self.context = SimpleNamespace(id="ctx", task=None)


def test_browser_session_teardown_prefers_kill_for_keep_alive_sessions():
    state = browser_agent_module.State(DummyAgent())
    session = DummyBrowserSession()
    state.browser_session = session

    state.kill_task()

    assert session.kill_called is True
    assert session.close_called is False


def test_browser_cleanup_extensions_follow_new_extensible_path_layout():
    extension = importlib.import_module("helpers.extension")
    remove_classes = extension._get_extension_classes(  # type: ignore[attr-defined]
        "_functions/agent/AgentContext/remove/start"
    )
    reset_classes = extension._get_extension_classes(  # type: ignore[attr-defined]
        "_functions/agent/AgentContext/reset/start"
    )

    assert any(cls.__name__ == "CleanupBrowserStateOnRemove" for cls in remove_classes)
    assert any(cls.__name__ == "CleanupBrowserStateOnReset" for cls in reset_classes)
