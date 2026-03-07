"""Tests for NormalizedMessage, ChannelStatus, and ChannelBridge."""

import pytest

from python.helpers.channel_bridge import ChannelBridge, ChannelStatus, NormalizedMessage


@pytest.mark.unit
class TestNormalizedMessage:
    def test_default_fields(self):
        msg = NormalizedMessage()
        assert len(msg.id) > 0
        assert msg.channel == ""
        assert msg.text == ""
        assert msg.timestamp > 0
        assert msg.metadata == {}
        assert msg.raw == {}

    def test_custom_fields(self):
        msg = NormalizedMessage(
            id="abc",
            channel="slack",
            sender_id="u1",
            sender_name="Alice",
            text="hello",
            timestamp=1000.0,
            metadata={"key": "val"},
        )
        assert msg.id == "abc"
        assert msg.channel == "slack"
        assert msg.sender_name == "Alice"
        assert msg.metadata == {"key": "val"}

    def test_to_dict(self):
        msg = NormalizedMessage(id="x", channel="tg", text="hi", timestamp=42.0)
        d = msg.to_dict()
        assert d["id"] == "x"
        assert d["channel"] == "tg"
        assert d["text"] == "hi"
        assert d["timestamp"] == 42.0
        # raw should not be in to_dict output
        assert "raw" not in d

    def test_to_dict_contains_metadata(self):
        msg = NormalizedMessage(metadata={"a": 1})
        d = msg.to_dict()
        assert d["metadata"] == {"a": 1}


@pytest.mark.unit
class TestChannelStatus:
    def test_enum_values(self):
        assert ChannelStatus.DISCONNECTED.value == "disconnected"
        assert ChannelStatus.CONNECTING.value == "connecting"
        assert ChannelStatus.CONNECTED.value == "connected"
        assert ChannelStatus.ERROR.value == "error"

    def test_all_statuses_exist(self):
        names = [s.name for s in ChannelStatus]
        assert "DISCONNECTED" in names
        assert "CONNECTING" in names
        assert "CONNECTED" in names
        assert "ERROR" in names


@pytest.mark.unit
class TestChannelBridge:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ChannelBridge({})

    def test_concrete_subclass(self):
        class DummyBridge(ChannelBridge):
            async def normalize(self, raw_payload):
                return NormalizedMessage()

            async def send(self, target_id, text, **kwargs):
                return {}

            async def verify_webhook(self, headers, body):
                return True

            async def connect(self):
                pass

            async def disconnect(self):
                pass

        bridge = DummyBridge({"token": "test"})
        assert bridge.config == {"token": "test"}
        assert bridge.status == ChannelStatus.DISCONNECTED
        assert bridge.name == "dummybridge"

    def test_name_property_strips_adapter(self):
        class FooAdapter(ChannelBridge):
            async def normalize(self, raw_payload):
                return NormalizedMessage()

            async def send(self, target_id, text, **kwargs):
                return {}

            async def verify_webhook(self, headers, body):
                return True

            async def connect(self):
                pass

            async def disconnect(self):
                pass

        adapter = FooAdapter({})
        assert adapter.name == "foo"
