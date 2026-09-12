import json
import subprocess
from pathlib import Path

import pytest

from plugins._browser.helpers.runtime import _BrowserRuntimeCore
from plugins._browser.tools.browser import Browser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def test_webui_beautifier_formats_objects_and_arrays() -> None:
    source = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "get_tool_message_handler"
        / "browser-tool-handler.js"
    ).read_text(encoding="utf-8")
    start = source.index("function beautifyJsonForDisplay")
    end = source.index("\n}", start) + 2
    object_literal = json.dumps({"browsers": [{"id": 1}]})
    array_literal = json.dumps([{"id": 1}, {"id": 2}])
    script = (
        source[start:end]
        + "\nconst pretty = beautifyJsonForDisplay(" + json.dumps(object_literal) + ");\n"
        + "if (!pretty.includes('\\n')) throw new Error('object JSON was not beautified');\n"
        + "if (pretty !== " + json.dumps(json.dumps({"browsers": [{"id": 1}]}, indent=2)) + ") throw new Error('object JSON content changed');\n"
        + "const arrayPretty = beautifyJsonForDisplay(" + json.dumps(array_literal) + ");\n"
        + "if (!arrayPretty.includes('\\n')) throw new Error('array JSON was not beautified');\n"
        + "if (JSON.parse(arrayPretty).length !== 2) throw new Error('array content changed');\n"
        + "const padded = beautifyJsonForDisplay('  ' + " + json.dumps(json.dumps({"a": 1})) + "  );\n"
        + "if (padded !== " + json.dumps('{\n  "a": 1\n}') + ") throw new Error('padded JSON was not trimmed');\n"
        + "if (beautifyJsonForDisplay('plain document') !== 'plain document') throw new Error('plain text changed');\n"
        + "if (beautifyJsonForDisplay('{broken') !== '{broken') throw new Error('invalid JSON changed');\n"
    )

    subprocess.run(["node", "--input-type=module", "-e", script], check=True, text=True)
