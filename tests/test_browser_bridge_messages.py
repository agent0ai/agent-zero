from dataclasses import replace
from types import SimpleNamespace
import json

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextRoute
from plugins._a0_connector.helpers.browser_bridge_messages import BrowserBridgeMessageDispatcher, BrowserBridgeMessageError
from browser_bridge_test_support import MemoryKeyValue


def _route():
    principal = WsPrincipal(
        principal_type="browser_bridge", principal_id="bridge-1", subject_id="single-user",
        scopes=frozenset({"context.message"}), handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector", inbound_events=frozenset({"connector_send_message"}),
        outbound_events=frozenset(), key_generation=1,
    )
    return BrowserBridgeContextRoute(principal, "sid-1", "load-1")


def _message(**changes):
    return {"contract_version": 1, "context_id": "ctx-1", "client_message_id": "message-1", "text": "private user conversation", **changes}


def test_message_reservation_survives_reconstruction_without_repeating_effect():
    route = _route()
    stored = MemoryKeyValue()
    effects = []
    access = SimpleNamespace(authorize_message_target=lambda _route, **_kwargs: None)

    def dispatcher():
        return BrowserBridgeMessageDispatcher(
            access=access, server_instance_id=lambda: "server-1",
            load=stored.load, save=stored.save,
            deliver=lambda *args: effects.append(args),
        )

    first = dispatcher().send(route, _message())
    second = dispatcher().send(replace(route, connector_sid="fresh-sid", load_generation_id="fresh-load"), _message())
    assert first == second and first["status"] == "accepted"
    assert len(effects) == 1
    assert "private user conversation" not in json.dumps(stored.value)
    assert "ctx-1" not in json.dumps(stored.value)
    with pytest.raises(BrowserBridgeMessageError, match="IDEMPOTENCY_CONFLICT"):
        dispatcher().send(route, _message(text="changed text"))


def test_uncertain_delivery_or_acceptance_write_never_replays_reserved_message():
    for fail_delivery in (True, False):
        stored = MemoryKeyValue()
        effects = []

        def save(key, value):
            if value.get("record", {}).get("state") == "accepted":
                raise OSError("owner secret path")
            stored.save(key, value)

        def deliver(*args):
            effects.append(args)
            if fail_delivery:
                raise RuntimeError("raw server error")

        dispatcher = BrowserBridgeMessageDispatcher(
            access=SimpleNamespace(authorize_message_target=lambda *_args, **_kwargs: None),
            server_instance_id=lambda: "server-1", load=stored.load, save=save, deliver=deliver,
        )
        for _ in range(2):
            with pytest.raises(BrowserBridgeMessageError) as error:
                dispatcher.send(_route(), _message())
            assert error.value.code == "OUTCOME_UNKNOWN" and error.value.outcome == "unknown"
            assert "secret" not in str(error.value) and "raw" not in str(error.value)
        assert len(effects) == 1


def test_message_authority_is_rechecked_after_durable_reservation():
    current = [True]
    effects = []
    stored = MemoryKeyValue()

    def authorize(*_args, **_kwargs):
        if not current[0]:
            raise PermissionError()

    def save(key, value):
        stored.save(key, value)
        if value.get("record", {}).get("state") == "reserved":
            current[0] = False

    dispatcher = BrowserBridgeMessageDispatcher(
        access=SimpleNamespace(authorize_message_target=authorize), server_instance_id=lambda: "server-1",
        load=stored.load, save=save, deliver=lambda *args: effects.append(args),
    )
    with pytest.raises(BrowserBridgeMessageError, match="SCOPE_DENIED"):
        dispatcher.send(_route(), _message())
    assert effects == []
    with pytest.raises(BrowserBridgeMessageError, match="INVALID_STATE"):
        dispatcher.send(_route(), _message(attachments=["/private/file"]))


def test_indexed_receipts_preserve_full_legacy_journal_and_fail_closed(monkeypatch, tmp_path):
    from helpers import kvp
    from plugins._a0_connector.helpers import browser_bridge_messages as module

    monkeypatch.setattr(kvp, "_persistent_dir", lambda: str(tmp_path))
    access = SimpleNamespace(authorize_message_target=lambda *_args, **_kwargs: None)
    stored, effects = MemoryKeyValue(), []
    seed = BrowserBridgeMessageDispatcher(
        access=access, server_instance_id=lambda: "server-1",
        load=stored.load, save=stored.save,
        deliver=lambda *args: effects.append(args))
    seed.send(_route(), _message())
    key, value = next((key, value) for key, value in stored.value.items() if ".records." in key)
    record = value["record"]
    legacy = {"schema_version": 1, "records": {key.rsplit(".", 1)[1]: record}}
    legacy["records"].update({f"{i:064x}": dict(record) for i in range(2047)})
    kvp.set_persistent(module._STORE_KEY, legacy)

    def dispatcher():
        return BrowserBridgeMessageDispatcher(
            access=access, server_instance_id=lambda: "server-1",
            deliver=lambda *args: effects.append(args))

    assert dispatcher().send(_route(), _message())["status"] == "accepted"
    dispatcher().send(_route(), _message(client_message_id="new-message"))
    dispatcher().send(_route(), _message(client_message_id="new-message"))
    assert len(effects) == 2
    assert kvp.get_persistent(module._STORE_KEY) == {**legacy, "schema_version": 2}
    with pytest.raises(BrowserBridgeMessageError, match="IDEMPOTENCY_CONFLICT"):
        dispatcher().send(_route(), _message(text="changed"))
    keys = kvp.find_persistent(module._STORE_KEY + ".records.*")
    assert len(keys) == 1
    value = kvp.get_persistent(keys[0])
    value["record"]["state"] = "reserved"
    kvp.set_persistent(keys[0], value)
    with pytest.raises(BrowserBridgeMessageError, match="OUTCOME_UNKNOWN"):
        dispatcher().send(_route(), _message(client_message_id="new-message"))
    kvp.set_persistent(keys[0], None)  # Corruption must not fall back to absent.
    with pytest.raises(BrowserBridgeMessageError, match="MESSAGE_STORE_UNAVAILABLE"):
        dispatcher().send(_route(), _message(client_message_id="new-message"))
    kvp.set_persistent(module._STORE_KEY, {})
    with pytest.raises(BrowserBridgeMessageError, match="MESSAGE_STORE_UNAVAILABLE"):
        dispatcher().send(_route(), _message(client_message_id="corrupt-legacy"))
    kvp.set_persistent(module._STORE_KEY, legacy)
    monkeypatch.setattr(kvp, "set_persistent", lambda *_args: (_ for _ in ()).throw(OSError()))
    with pytest.raises(BrowserBridgeMessageError, match="MESSAGE_STORE_UNAVAILABLE"):
        dispatcher().send(_route(), _message(client_message_id="failed-write"))
    assert len(effects) == 2
