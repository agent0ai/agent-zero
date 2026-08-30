from types import SimpleNamespace

import pytest

from plugins._promptinclude.extensions.python.system_prompt import _16_promptinclude
from plugins._promptinclude.helpers.scanner import scan_promptinclude_files


def test_scanner_ignores_empty_matching_files(tmp_path) -> None:
    (tmp_path / "empty.promptinclude.md").write_text(" \n", encoding="utf-8")

    assert scan_promptinclude_files(str(tmp_path)) == {
        "files": [],
        "skipped_count": 0,
    }


@pytest.mark.asyncio
async def test_promptinclude_stays_discoverable_without_matching_files(
    monkeypatch, tmp_path
) -> None:
    class Agent:
        context = SimpleNamespace()

        def read_prompt(self, name, **kwargs):
            assert name == "agent.system.promptinclude.md"
            return f"{kwargs['name_pattern']}|{kwargs['includes']}"

    async def call_direct(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(
        _16_promptinclude.plugins,
        "get_plugin_config",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        _16_promptinclude, "_resolve_workdir", lambda _agent: str(tmp_path)
    )
    monkeypatch.setattr(
        _16_promptinclude.runtime, "call_development_function", call_direct
    )

    system_prompt: list[str] = []
    await _16_promptinclude.PromptInclude(Agent()).execute(
        system_prompt=system_prompt
    )

    assert system_prompt == ["*.promptinclude.md|"]
