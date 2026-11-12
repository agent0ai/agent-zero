"""Pre-operation reconnect waits never send or retry browser operations."""
import asyncio
from types import SimpleNamespace

import pytest

from plugins._browser.helpers import extension_runtime as runtime_module
from plugins._browser.helpers import config, bridge_foundation


def setup(monkeypatch, *, ready_at=15.0, change=None):
    now = [0.0]
    calls = []
    agent = SimpleNamespace(context=SimpleNamespace(id="context-1"))
    selected = {"runtime_backend": "host_required", "host_browser_selection": "extension:bridge-1"}
    runtime = object.__new__(runtime_module.ExtensionBrowserRuntime)
    runtime.context_id, runtime.bridge_id = "context-1", "bridge-1"
    def factory(actual_agent, bridge):
        assert actual_agent is agent and bridge == "bridge-1"
        calls.append(now[0])
        return runtime if now[0] >= ready_at else None
    async def advance(seconds):
        now[0] += seconds
        if change is not None:
            change(selected)
    monkeypatch.setattr(runtime_module, "_runtime_factory", factory)
    monkeypatch.setattr(runtime_module, "_runtime_factory_owner", object())
    monkeypatch.setattr(config, "get_browser_config", lambda **kw: selected)
    monkeypatch.setattr(bridge_foundation, "get_browser_bridge_gate", lambda: SimpleNamespace(state="available"))
    monkeypatch.setattr(runtime_module.asyncio, "sleep", advance)
    monkeypatch.setattr(runtime_module.asyncio, "get_running_loop", lambda: SimpleNamespace(time=lambda: now[0]))
    return agent, runtime, now, calls


def test_reconnect_wait_resolves_only_after_existing_owner_becomes_ready(monkeypatch):
    agent, runtime, now, calls = setup(monkeypatch)
    assert asyncio.run(runtime_module.wait_selected_extension_runtime(agent, "bridge-1")) is runtime
    assert now[0] == 15.0 and calls[0] == 0 and calls[-1] == 15.0
    assert not hasattr(runtime, "_broker")  # Acquisition never performs any work.


@pytest.mark.parametrize("change", ["selection", "owner", "cancel", "timeout"])
def test_reconnect_wait_is_bounded_cancellable_and_never_adopts_replacement(monkeypatch, change):
    def alter(selected):
        if change == "selection":
            selected["host_browser_selection"] = "extension:another-bridge"
        elif change == "owner":
            monkeypatch.setattr(runtime_module, "_runtime_factory_owner", object())
        elif change == "cancel":
            raise asyncio.CancelledError()
    agent, runtime, now, calls = setup(monkeypatch, ready_at=30.0, change=alter)
    if change == "cancel":
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(runtime_module.wait_selected_extension_runtime(agent, "bridge-1"))
    else:
        assert asyncio.run(runtime_module.wait_selected_extension_runtime(agent, "bridge-1")) is None
    assert now[0] == (25.0 if change == "timeout" else 0.25)
    assert len(calls) == (101 if change == "timeout" else 1)


def test_absent_factory_does_not_wait_or_infer_installation(monkeypatch):
    monkeypatch.setattr(runtime_module, "_runtime_factory", None)
    assert asyncio.run(runtime_module.wait_selected_extension_runtime(None, "bridge-1")) is None
