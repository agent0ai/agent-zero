import asyncio
import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

agent_stub = types.ModuleType("agent")
agent_stub.LoopData = object
original_agent_module = sys.modules.get("agent")
sys.modules["agent"] = agent_stub

try:
    retry_module = importlib.import_module(
        "plugins._error_retry.extensions.python._functions.agent.Agent."
        "handle_exception.end._80_retry_critical_exception"
    )
    counter_module = importlib.import_module(
        "plugins._error_retry.extensions.python._functions.agent.Agent."
        "monologue.start._10_reset_critical_exception_counter"
    )
finally:
    if original_agent_module is None:
        sys.modules.pop("agent", None)
    else:
        sys.modules["agent"] = original_agent_module

DATA_NAME_COUNTER = counter_module.DATA_NAME_COUNTER


class FakeLog:
    def __init__(self):
        self.entries = []

    def log(self, **entry):
        self.entries.append(entry)


class FakeAgent:
    def __init__(self, counter=0):
        self._data = {DATA_NAME_COUNTER: counter}
        self.context = SimpleNamespace(log=FakeLog())
        self.history = SimpleNamespace(remove_all_embeds=lambda: 0)
        self.interventions = 0
        self.warnings = []

    def get_data(self, key):
        return self._data.get(key)

    def set_data(self, key, value):
        self._data[key] = value

    async def handle_intervention(self):
        self.interventions += 1

    def read_prompt(self, prompt, **kwargs):
        return f"{prompt}: {kwargs['error_message']}"

    def hist_add_warning(self, **warning):
        self.warnings.append(warning)


async def _no_sleep(_delay):
    return None


def _set_retry_config(monkeypatch, retries):
    monkeypatch.setattr(
        retry_module.plugins,
        "get_plugin_config",
        lambda *args, **kwargs: {"retries": retries},
    )
    monkeypatch.setattr(retry_module.asyncio, "sleep", _no_sleep)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, 1),
        ("", 1),
        (False, 1),
        ("3", 3),
        (2.9, 2),
        (-4, 0),
    ],
)
def test_normalize_max_retries(value, expected):
    assert retry_module.normalize_max_retries(value) == expected


def test_error_retry_uses_configured_retry_limit(monkeypatch):
    _set_retry_config(monkeypatch, 2)
    agent = FakeAgent(counter=1)
    data = {"exception": RuntimeError("boom")}

    asyncio.run(retry_module.RetryCriticalException(agent=agent).execute(data))

    assert agent.get_data(DATA_NAME_COUNTER) == 2
    assert data["exception"] is None
    assert agent.interventions == 1
    assert len(agent.context.log.entries) == 1
    assert len(agent.warnings) == 1


def test_zero_configured_retries_disables_retry(monkeypatch):
    _set_retry_config(monkeypatch, 0)
    agent = FakeAgent(counter=0)
    exception = RuntimeError("boom")
    data = {"exception": exception}

    asyncio.run(retry_module.RetryCriticalException(agent=agent).execute(data))

    assert agent.get_data(DATA_NAME_COUNTER) == 0
    assert data["exception"] is exception
    assert agent.interventions == 0
    assert agent.context.log.entries == []
