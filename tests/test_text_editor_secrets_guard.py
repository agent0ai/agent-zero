import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import files as files_helper  # noqa: E402
from helpers import projects  # noqa: E402
from plugins._text_editor.tools.text_editor import TextEditor  # noqa: E402


class _ProjectContext:
    def __init__(self, project):
        self._project = project

    def get_data(self, key: str):
        if key == "project":
            return self._project
        return None


class _FakeAgent:
    def __init__(self, project):
        self.context = _ProjectContext(project)
        self.data = {}
        self._data = {}

    def read_prompt(self, *args, **kwargs):
        return f"error: {kwargs.get('error', '')}"

    def get_data(self, key):
        return self._data.get(key)

    def set_data(self, key, value):
        self._data[key] = value


def _make_tool(project):
    tool = object.__new__(TextEditor)
    tool.agent = _FakeAgent(project)
    tool.args = {}
    tool.method = None
    tool.name = "text_editor"
    tool.message = ""
    tool.loop_data = None
    return tool


@pytest.fixture
def _projects_dir(tmp_path, monkeypatch):
    parent = tmp_path / "projects"
    for name in ("ProjectA", "ProjectB"):
        (parent / name / ".a0proj").mkdir(parents=True)
        (parent / name / ".a0proj" / "secrets.env").write_text(
            "API_TOKEN=dummy-secret-value-999\n"
        )
    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: str(parent))
    monkeypatch.setattr(files_helper, "_base_dir", str(tmp_path))
    return parent


@pytest.mark.asyncio
async def test_text_editor_denies_sibling_project_secrets_read(
    _projects_dir, monkeypatch
):
    from helpers import runtime

    def _forbidden(*args, **kwargs):
        raise AssertionError("guard must run before any file access")

    monkeypatch.setattr(runtime, "call_development_function", _forbidden)
    tool = _make_tool("ProjectB")
    response = await tool.execute(
        action="read",
        path="projects/ProjectA/.a0proj/secrets.env",
    )
    assert "not allowed" in response.message
    assert "dummy-secret-value-999" not in response.message


@pytest.mark.asyncio
async def test_text_editor_denies_sibling_project_secrets_write(
    _projects_dir, monkeypatch
):
    from helpers import runtime

    def _forbidden(*args, **kwargs):
        raise AssertionError("guard must run before any file access")

    monkeypatch.setattr(runtime, "call_development_function", _forbidden)
    tool = _make_tool("ProjectB")
    response = await tool.execute(
        action="write",
        path="projects/ProjectA/.a0proj/secrets.env",
        content="API_TOKEN=pwned\n",
    )
    assert "not allowed" in response.message
    assert "pwned" not in response.message


@pytest.mark.asyncio
async def test_text_editor_allows_active_project_secrets_read(
    _projects_dir, monkeypatch
):
    from helpers import runtime
    from plugins._text_editor.helpers.file_ops import FileInfo

    async def _fake_call(fn, *args, **kwargs):
        if fn.__name__ == "read_file":
            return {
                "content": "1 API_TOKEN=dummy-secret-value-999",
                "total_lines": 1,
                "warnings": "",
                "error": "",
            }
        if fn.__name__ == "file_info":
            return FileInfo(
                exists=True,
                is_file=True,
                realpath=str(args[0]),
                expanded=str(args[0]),
                mtime=0.0,
            )
        raise AssertionError(f"unexpected call {fn.__name__}")

    monkeypatch.setattr(runtime, "call_development_function", _fake_call)
    monkeypatch.setattr(
        "helpers.plugins.get_plugin_config", lambda *args, **kwargs: {}
    )

    async def _noop_extensions(*args, **kwargs):
        return None

    # Patch through the real function's globals: sibling test files pop and
    # reimport this module under stubs, so the sys.modules entry may point
    # at a stub-built module while this class still uses the real one.
    monkeypatch.setitem(
        TextEditor.execute.__globals__, "call_extensions_async", _noop_extensions
    )
    tool = _make_tool("ProjectB")
    response = await tool.execute(
        action="read",
        path="projects/ProjectB/.a0proj/secrets.env",
    )
    assert "not allowed" not in response.message
