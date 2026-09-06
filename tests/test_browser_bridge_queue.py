import asyncio
import json

import pytest

from helpers import message_queue
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextAccess, BrowserBridgeContextRoute
from plugins._a0_connector.helpers.browser_bridge_messages import BrowserBridgeMessageDispatcher
from plugins._a0_connector.helpers.browser_bridge_queue import BrowserBridgeQueueController, BrowserBridgeQueueError
from test_browser_bridge_application import Source
from browser_bridge_test_support import MemoryKeyValue
from test_browser_bridge_runtime_foundation import _principal


class Context:
    def __init__(self):
        self.data, self.output = {}, {}

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value

    def set_output_data(self, key, value):
        self.output[key] = value


class Harness:
    def __init__(self):
        self.current = True
        self.route = BrowserBridgeContextRoute(_principal(), "sid-A", "generation-A")
        self.access = BrowserBridgeContextAccess(data_source=Source(), route_authorizer=lambda route: self.current and route is self.route)
        self.access.advertise_contexts(self.route)
        self.queue_store, self.message_store = MemoryKeyValue(), MemoryKeyValue()
        self.context = Context()
        self.effects, self.emitted = [], []
        self.messages = BrowserBridgeMessageDispatcher(
            access=self.access, server_instance_id=lambda: "server-A", load=self.message_store.load,
            save=self.message_store.save, deliver=lambda *args: self.effects.append(args))
        self.controller = BrowserBridgeQueueController(
            access=self.access, messages=self.messages, manager=self,
            server_instance_id=lambda: "server-A", context_get=lambda context: self.context,
            queue_service=message_queue, load=self.queue_store.load, save=self.queue_store.save,
            mark_dirty=lambda context: None)

    async def emit_to(self, *args, **kwargs):
        self.emitted.append((args, kwargs))

    async def add(self, **changes):
        return await self.controller.dispatch("connector_message_queue_add", self.route, {
            "contract_version": 1, "context_id": "context-A", "client_message_id": "message-A",
            "text": "private queue text", **changes})

    async def action(self, action, item_id):
        return await self.controller.dispatch("connector_message_queue_" + action, self.route, {
            "contract_version": 1, "context_id": "context-A", "item_id": item_id})


def test_real_core_queue_replays_send_once_and_uses_exact_private_projection():
    async def scenario():
        h = Harness()
        message_queue.add(h.context, "unrelated secret", ["/private/path"], item_id="foreign")
        first = await h.add()
        assert (await h.add())["item_id"] == first["item_id"]
        assert len(message_queue.get_queue(h.context)) == 2
        assert len(first["message_queue"]) == 1
        with pytest.raises(BrowserBridgeQueueError, match="QUEUE_ITEM_NOT_FOUND"):
            await h.action("remove", "foreign")
        with pytest.raises(BrowserBridgeQueueError, match="IDEMPOTENCY_CONFLICT"):
            await h.add(text="changed")
        assert (await h.action("send", first["item_id"]))["status"] == "sent"
        assert (await h.action("send", first["item_id"]))["status"] == "sent"
        assert len(h.effects) == 1
        assert (await h.add())["status"] == "sent"
        assert [item["id"] for item in message_queue.get_queue(h.context)] == ["foreign"]
        assert "private queue text" not in json.dumps(h.queue_store.value)
        assert "context-A" not in json.dumps(h.queue_store.value)
        assert "unrelated secret" not in json.dumps(h.emitted, default=str)
        assert all(kwargs["expected_principal"] is h.route.principal for _, kwargs in h.emitted)
    asyncio.run(scenario())


def test_queue_stale_unadvertised_and_attachment_requests_have_no_effect():
    async def scenario():
        h = Harness()
        with pytest.raises(BrowserBridgeQueueError, match="INVALID_STATE"):
            await h.add(attachments=["/private/path"])
        with pytest.raises(BrowserBridgeQueueError, match="SCOPE_DENIED"):
            await h.add(context_id="other")
        h.current = False
        with pytest.raises(BrowserBridgeQueueError, match="SCOPE_DENIED"):
            await h.add()
        assert not message_queue.get_queue(h.context)
        assert h.queue_store.value == {}
    asyncio.run(scenario())


def test_uncertain_queue_effect_keeps_hash_reservation_and_never_reexecutes():
    async def scenario():
        h = Harness()
        first = await h.add()
        def partial(*args):
            h.effects.append(args)
            raise RuntimeError("private transport exception")
        h.messages._deliver = partial
        for _ in range(2):
            with pytest.raises(BrowserBridgeQueueError, match="OUTCOME_UNKNOWN"):
                await h.action("send", first["item_id"])
        assert len(h.effects) == 1
        assert not message_queue.get_queue(h.context)
        assert "private transport exception" not in json.dumps(h.queue_store.value)
        h = Harness()
        original_get = h.controller.journal.get
        reads = [0]
        def failed_projection(key):
            reads[0] += 1
            if reads[0] > 1:
                raise BrowserBridgeQueueError("QUEUE_STORE_UNAVAILABLE")
            return original_get(key)
        h.controller.journal.get = failed_projection
        with pytest.raises(BrowserBridgeQueueError, match="OUTCOME_UNKNOWN"):
            await h.add()
        h.controller.journal.get = original_get
        assert (await h.add())["status"] == "queued"
        assert len(message_queue.get_queue(h.context)) == 1
    asyncio.run(scenario())


def test_indexed_queue_retains_old_receipts_without_lifetime_lockout(monkeypatch, tmp_path):
    from helpers import kvp
    from plugins._a0_connector.helpers import browser_bridge_queue as module
    from plugins._a0_connector.helpers.browser_bridge_journal import BrowserBridgeJournal

    monkeypatch.setattr(kvp, "_persistent_dir", lambda: str(tmp_path))

    async def scenario():
        h = Harness()
        first = await h.add()
        record = h.queue_store.value[module._STORE_KEY + ".records." + first["item_id"]]["record"]
        legacy = {"schema_version": 1, "records": {first["item_id"]: record}}
        legacy["records"].update({f"{i:064x}": dict(record) for i in range(2047)})
        kvp.set_persistent(module._STORE_KEY, legacy)

        def reconnect():
            h.controller.journal = BrowserBridgeJournal(
                module._STORE_KEY, module._validate_record,
                lambda: BrowserBridgeQueueError("QUEUE_STORE_UNAVAILABLE"))

        reconnect()
        fresh = await h.add(client_message_id="fresh")
        await h.action("remove", fresh["item_id"])
        await h.action("remove", first["item_id"])
        reconnect()
        assert (await h.add())["status"] == "removed"
        assert (await h.add(client_message_id="fresh"))["status"] == "removed"
        assert not message_queue.get_queue(h.context)
        assert kvp.get_persistent(module._STORE_KEY) == {**legacy, "schema_version": 2}
        with pytest.raises(BrowserBridgeQueueError, match="IDEMPOTENCY_CONFLICT"):
            await h.add(text="changed")
        for i in range(32):
            await h.add(client_message_id=f"live-{i}")
        with pytest.raises(BrowserBridgeQueueError, match="QUEUE_LIMIT"):
            await h.add(client_message_id="over-live-limit")
        assert len(h.controller.project(h.route, "context-A")["message_queue"]) == 32
    asyncio.run(scenario())
