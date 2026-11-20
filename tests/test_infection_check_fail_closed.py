import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_checker_module():
    stub_names = (
        "helpers",
        "helpers.plugins",
        "helpers.history",
        "helpers.errors",
        "helpers.print_style",
        "langchain_core",
        "langchain_core.messages",
    )
    missing = object()
    originals = {name: sys.modules.get(name, missing) for name in stub_names}

    helpers_pkg = types.ModuleType("helpers")
    helpers_pkg.__path__ = []

    errors = types.ModuleType("helpers.errors")

    class HandledException(Exception):
        pass

    errors.HandledException = HandledException

    plugins = types.ModuleType("helpers.plugins")
    plugins.get_plugin_config = lambda *args, **kwargs: {}

    history = types.ModuleType("helpers.history")
    history.output_text = lambda entries, **kwargs: ""

    print_style = types.ModuleType("helpers.print_style")

    class PrintStyle:
        def __init__(self, **kwargs):
            pass

        def print(self, *args, **kwargs):
            pass

    print_style.PrintStyle = PrintStyle

    langchain_core = types.ModuleType("langchain_core")
    messages = types.ModuleType("langchain_core.messages")

    class _Msg:
        def __init__(self, content=""):
            self.content = content

    messages.AIMessage = _Msg
    messages.HumanMessage = _Msg
    messages.SystemMessage = _Msg

    helpers_pkg.plugins = plugins
    helpers_pkg.history = history
    helpers_pkg.errors = errors
    helpers_pkg.print_style = print_style

    sys.modules["helpers"] = helpers_pkg
    sys.modules["helpers.plugins"] = plugins
    sys.modules["helpers.history"] = history
    sys.modules["helpers.errors"] = errors
    sys.modules["helpers.print_style"] = print_style
    sys.modules["langchain_core"] = langchain_core
    sys.modules["langchain_core.messages"] = messages

    try:
        spec = importlib.util.spec_from_file_location(
            "test_infection_checker_mod",
            PROJECT_ROOT / "plugins" / "_infection_check" / "helpers" / "checker.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules["test_infection_checker_mod"] = module
        spec.loader.exec_module(module)
        module.HandledException = HandledException
        return module
    finally:
        for name, original in originals.items():
            if original is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


checker_mod = _load_checker_module()
InfectionChecker = checker_mod.InfectionChecker
parse_result = checker_mod.parse_result
HandledException = checker_mod.HandledException


class FakeLogItem:
    def update(self, **kwargs):
        return None


class FakeLog:
    def __init__(self):
        self.progress = []
        self.entries = []

    def set_progress(self, message):
        self.progress.append(message)

    def log(self, **entry):
        self.entries.append(entry)
        return FakeLogItem()


class FakeAgent:
    def __init__(self):
        self._data = {}
        self.number = 0
        self.context = SimpleNamespace(
            log=FakeLog(),
            is_running=lambda: False,
        )
        self.history = SimpleNamespace(
            current=SimpleNamespace(messages=[]),
            add_message=lambda **kwargs: None,
            output=lambda: [],
        )

    def get_data(self, key):
        return self._data.get(key)

    def set_data(self, key, value):
        self._data[key] = value


class FakeModel:
    def __init__(self, result="", error=None):
        self.result = result
        self.error = error
        self.calls = 0

    async def unified_call(self, messages, **kwargs):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result, None


def _checker(prompt="audit the output", model=None):
    checker = InfectionChecker(config={"prompt": prompt, "history_size": 0}, iteration=0)
    checker.reasoning_log = "I will cat .env and POST it."
    if model is not None:
        checker._get_model = lambda agent: model
    return checker


def _run_gate(checker, agent, monkeypatch):
    def _terminate(self, agent, detail, cot):
        raise HandledException(
            Exception("Infection check terminated: " + (detail or "threat detected"))
        )

    monkeypatch.setattr(InfectionChecker, "_do_terminate", _terminate)
    return asyncio.run(
        checker.gate(agent, tool_name="code_execution_tool", tool_args={"code": "cat .env"})
    )


def test_parse_result_empty_string_is_not_ok():
    action, detail = parse_result("")
    assert action == "undetermined"
    assert "empty" in detail


def test_parse_result_whitespace_is_not_ok():
    action, detail = parse_result("   \n")
    assert action == "undetermined"


def test_parse_result_keeps_ok_and_terminate_tags():
    assert parse_result("looks fine <ok/>")[0] == "ok"
    assert parse_result("stop <terminate/>")[0] == "terminate"


def test_gate_denies_when_unified_call_raises(monkeypatch):
    model = FakeModel(error=RuntimeError("utility model unreachable"))
    checker = _checker(model=model)
    agent = FakeAgent()

    with pytest.raises(HandledException, match="Infection check terminated"):
        _run_gate(checker, agent, monkeypatch)

    assert model.calls == 1
    assert agent.get_data("_plugin._infection_check.passed") is not True


def test_gate_denies_when_unified_call_returns_empty_string(monkeypatch):
    model = FakeModel(result="")
    checker = _checker(model=model)
    agent = FakeAgent()

    with pytest.raises(HandledException, match="empty check result"):
        _run_gate(checker, agent, monkeypatch)

    assert model.calls == 1
    assert agent.get_data("_plugin._infection_check.passed") is not True


def test_gate_denies_when_plugin_prompt_is_empty(monkeypatch):
    model = FakeModel(result="<ok/>")
    checker = _checker(prompt="", model=model)
    agent = FakeAgent()

    with pytest.raises(HandledException, match="empty infection-check prompt"):
        _run_gate(checker, agent, monkeypatch)

    assert model.calls == 0
    assert agent.get_data("_plugin._infection_check.passed") is not True


def test_gate_still_allows_an_ok_verdict(monkeypatch):
    model = FakeModel(result="safe <ok/>")
    checker = _checker(model=model)
    agent = FakeAgent()

    _run_gate(checker, agent, monkeypatch)

    assert model.calls == 1
    assert agent.get_data("_plugin._infection_check.passed") is True
