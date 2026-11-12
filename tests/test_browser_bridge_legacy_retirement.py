from __future__ import annotations

import copy
import asyncio
import importlib.util
from pathlib import Path
import shutil
import sys
import time
import types

import pytest
from flask import Flask

from plugins._a0_connector.helpers import browser_bridge_legacy_retirement as retirement


def adapter(tmp_path, monkeypatch):
    root = tmp_path / "chrome_extension"
    shutil.copytree(Path(__file__).parent / "fixtures/browser_bridge_cutover_v1/legacy_exact", root)
    constants = types.ModuleType("usr.plugins.chrome_extension.helpers.constants")
    constants.CTX_BROWSER_SESSION_ID = "chrome_browser_session_id"
    constants.CTX_CHROME_CAPABILITIES = "chrome_extension_capabilities"
    constants.CTX_SOURCE = "source"
    constants.SOURCE_NAME = "chrome_extension"
    monkeypatch.setitem(sys.modules, constants.__name__, constants)
    path = root / "helpers/session_store.py"
    spec = importlib.util.spec_from_file_location("legacy_retirement_fixture", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return retirement.PrototypeRegistryAdapter(module, root), module


def test_exact_prototype_drains_without_replay_or_browser_effects(tmp_path, monkeypatch):
    driver, module = adapter(tmp_path, monkeypatch)
    session = module.BrowserSession("session-private")
    module._sessions[session.browser_session_id] = session
    queued = module.BridgeCommand("queued", session.browser_session_id, "click", payload={"secret": "do-not-copy"})
    unknown = module.BridgeCommand("unknown", session.browser_session_id, "type", status="dispatched", attempts=1, created_at=time.time()-60, timeout_seconds=1)
    done = module.BridgeCommand("done", session.browser_session_id, "capture_visible_tab", status="completed", attempts=1, result={"image_data_url": "data:image/png;base64,secret"})
    session.commands = {item.command_id: item for item in (queued, unknown, done)}
    session.queue = list(session.commands)
    stored, effects = {}, []
    owner = retirement.LegacyRetirement(load=lambda: copy.deepcopy(stored.get("value")), save=lambda value: stored.update(value=copy.deepcopy(value)), adapter=lambda: driver, disable=lambda: effects.append("disable"))
    owner.guard_installed = True
    result = asyncio.run(owner.retire())
    assert result["state"] == "legacy_disabled"
    assert result["counts"] == {"completed": 1, "canceled_not_applied": 1, "outcome_unknown": 1}
    assert result["browser_tabs_changed"] is False and result["activation_ready"] is False
    assert effects == ["disable"] and module._sessions == {}
    assert queued.payload == {} and done.result == {}
    assert "secret" not in str(stored) and "session-private" not in str(stored)
    with pytest.raises(retirement.LegacyRetirementDenied):
        module.enqueue_command("session-private", "click")
    assert asyncio.run(owner.retire()) == result
    assert effects == ["disable"]


def test_exact_terminal_result_is_accepted_once_and_payload_discarded(tmp_path, monkeypatch):
    driver, module = adapter(tmp_path, monkeypatch)
    session = module.BrowserSession("session")
    command = module.BridgeCommand("command", "session", "click", status="dispatched", attempts=1)
    session.commands["command"] = command
    module._sessions["session"] = session
    assert driver.begin() == 1
    with pytest.raises(retirement.LegacyRetirementDenied):
        driver.accept_result("foreign", "command", status="completed")
    assert driver.accept_result("session", "command", status="completed", result={"image_data_url": "secret"}) == {"status": "completed"}
    with pytest.raises(retirement.LegacyRetirementDenied):
        driver.accept_result("session", "command", status="completed")
    assert driver.finish()["completed"] == 1
    assert command.result == {}


def test_flask_guard_is_idle_by_default_and_corrupt_journal_blocks_legacy_only(monkeypatch):
    stored = {}
    owner = retirement.LegacyRetirement(load=lambda: stored.get("value"), save=lambda value: None)
    monkeypatch.setattr(retirement, "_owner", owner)
    app = Flask(__name__)
    retirement.install_legacy_retirement_guard(app)
    retirement.install_legacy_retirement_guard(app)
    app.add_url_rule("/<path:path>", "fixture", lambda path: "untouched")
    client = app.test_client()
    assert client.get("/api/plugins/chrome_extension/session_upsert").status_code == 200
    assert owner.active_requests == 0
    stored["value"] = {"secret": "not-an-accepted-journal"}
    for prefix in ("/api/plugins/", "/plugins/"):
        response = client.get(prefix + "chrome_extension/command_pull")
        assert response.status_code == 410 and b"secret" not in response.data
        assert client.get(prefix + "other_plugin/command_pull").status_code == 200
    assert client.get("/api/api_message").status_code == 200
    assert client.get("/api/plugins/_a0_connector/browser_bridge_pairing").status_code == 200


def test_interrupted_or_uninstalled_guard_never_replays_or_claims_success():
    effects = []
    owner = retirement.LegacyRetirement(load=lambda: None, save=lambda value: effects.append(value), adapter=lambda: None, disable=lambda: effects.append("disable"))
    with pytest.raises(retirement.LegacyRetirementDenied):
        asyncio.run(owner.retire())
    assert effects == []
    journal = {"schema_version": 1, "migration_id": "00000000-0000-0000-0000-000000000001", "state": "draining_legacy", "started_at_ms": 1, "completed": 0, "canceled_not_applied": 0, "outcome_unknown": 2}
    owner.load = lambda: journal
    owner.guard_installed = True
    assert asyncio.run(owner.retire())["state"] == "blocked"
    assert effects == []
