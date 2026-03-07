"""Tests for ChannelFactory registry."""

import pytest

import python.helpers.channels  # noqa: F401
from python.helpers.channel_factory import ChannelFactory


@pytest.mark.unit
class TestChannelFactory:
    def test_available_returns_16_channels(self):
        channels = ChannelFactory.available()
        assert len(channels) == 16
        # Verify alphabetical ordering
        assert channels == sorted(channels)

    def test_available_contains_known_channels(self):
        channels = ChannelFactory.available()
        for name in ("telegram", "discord", "slack", "whatsapp", "email", "signal"):
            assert name in channels

    def test_get_adapter_class_returns_class(self):
        cls = ChannelFactory.get_adapter_class("telegram")
        assert cls is not None
        assert isinstance(cls, type)

    def test_get_adapter_class_unknown_returns_none(self):
        assert ChannelFactory.get_adapter_class("nonexistent") is None

    def test_create_returns_adapter_instance(self):
        adapter = ChannelFactory.create("telegram", config={"token": "test"})
        assert adapter is not None
        assert hasattr(adapter, "config")
        assert adapter.config == {"token": "test"}

    def test_create_unknown_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown channel"):
            ChannelFactory.create("nonexistent_channel")

    def test_create_with_empty_config(self):
        adapter = ChannelFactory.create("discord")
        assert adapter.config == {}

    def test_register_decorator(self):
        @ChannelFactory.register("test_dummy_channel")
        class DummyAdapter:
            def __init__(self, config):
                self.config = config

        assert "test_dummy_channel" in ChannelFactory.available()
        inst = ChannelFactory.create("test_dummy_channel", config={"x": 1})
        assert inst.config == {"x": 1}

        # Cleanup
        del ChannelFactory._registry["test_dummy_channel"]
