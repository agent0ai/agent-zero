import json

import pytest

from plugins._browser.helpers.runtime import _BrowserRuntimeCore
from plugins._browser.tools.browser import Browser


def test_format_result_minifies_tool_json() -> None:
    result = {"browsers": [{"id": "b1", "title": "Example"}]}

    formatted = Browser._format_result("list", result)

    assert "\n" not in formatted
    assert json.loads(formatted) == result


def test_format_result_keeps_content_document_plain() -> None:
    formatted = Browser._format_result("content", {"document": "<html></html>"})

    assert formatted == "<html></html>"


@pytest.mark.asyncio
async def test_evaluate_uses_script_arg(monkeypatch) -> None:
    core = _BrowserRuntimeCore("ctx")
    seen: list[str] = []

    async def fake_evaluate(bid, script):
        seen.append(script)
        return 7

    monkeypatch.setattr(core, "evaluate", fake_evaluate)

    result = await core._dispatch_call({"action": "evaluate", "script": "1+1"})

    assert result == 7
    assert seen == ["1+1"]
