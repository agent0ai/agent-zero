import types
from types import SimpleNamespace
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import images


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


def _install_tool_stub(monkeypatch):
    tool_stub = types.ModuleType("helpers.tool")
    tool_stub.Response = _TestResponse
    tool_stub.Tool = _TestTool
    history_stub = types.ModuleType("helpers.history")

    class _RawMessage(dict):
        def __init__(self, raw_content, preview):
            super().__init__(raw_content=raw_content, preview=preview)

    history_stub.RawMessage = _RawMessage
    monkeypatch.setitem(sys.modules, "helpers.tool", tool_stub)
    monkeypatch.setitem(sys.modules, "helpers.history", history_stub)
    monkeypatch.delitem(sys.modules, "tools.vision_load", raising=False)


def test_prepare_content_keeps_missing_local_image_refs_strict():
    missing_path = "/tmp/a0-missing-desktop-screenshot.png"

    with pytest.raises(FileNotFoundError):
        images.prepare_content(
            [{"type": "image_url", "image_url": {"url": missing_path}}]
        )


@pytest.mark.anyio
async def test_vision_load_materializes_local_image_to_chat_artifact(monkeypatch, tmp_path):
    _install_tool_stub(monkeypatch)
    import tools.vision_load as vision_load_module

    def fake_get_abs_path(*parts):
        return str(tmp_path.joinpath(*parts))

    def fake_normalize_a0_path(path):
        return "/a0/" + str(Path(path).relative_to(tmp_path)).replace("\\", "/")

    monkeypatch.setattr(vision_load_module.chat_media.files, "get_abs_path", fake_get_abs_path)
    monkeypatch.setattr(vision_load_module.chat_media.files, "normalize_a0_path", fake_normalize_a0_path)
    monkeypatch.setattr(
        vision_load_module.plugins,
        "get_plugin_config",
        lambda *args, **kwargs: {"chat_model": {"max_embeds": 10}},
    )

    async def direct_call(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        vision_load_module.runtime,
        "call_development_function",
        direct_call,
    )

    image_path = tmp_path / "sample-image.png"
    image_path.write_bytes(b"png-data")

    tool_results = []
    messages = []
    updates = []
    agent = SimpleNamespace(
        context=SimpleNamespace(id="ctx-vision"),
        agent_name="Agent 0",
        hist_add_tool_result=lambda *args, **kwargs: tool_results.append((args, kwargs)),
        hist_add_message=lambda *args, **kwargs: messages.append((args, kwargs)),
    )
    tool = vision_load_module.VisionLoad(
        agent=agent,
        name="vision_load",
        method=None,
        args={"paths": [str(image_path)]},
        message="",
        loop_data=None,
    )
    tool.log = SimpleNamespace(id="vision-log", update=lambda **kwargs: updates.append(kwargs))

    response = await tool.execute(paths=[str(image_path)])
    image_path.unlink()
    await tool.after_execution(response)

    raw_message = messages[0][1]["content"]
    stored_ref = raw_message["raw_content"][0]["image_url"]["url"]
    assert stored_ref.startswith("/a0/usr/chats/ctx-vision/images/vision-load/sample-image-")
    stored_path = tmp_path / stored_ref.removeprefix("/a0/")
    assert stored_path.read_bytes() == b"png-data"
    assert updates[-1]["result"] == "1 images loaded, 0 skipped"
