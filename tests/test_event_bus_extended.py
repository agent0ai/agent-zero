"""Extended EventBus tests: wildcard, multi-subscriber, unsubscribe, persistence."""

import asyncio

import pytest

from python.helpers.event_bus import EventBus, EventStore


@pytest.mark.unit
class TestEventStore:
    def test_add_and_list_events(self):
        store = EventStore(":memory:")
        store.add_event("test.event", {"key": "value"})
        events = store.list_events(limit=10)
        assert len(events) == 1
        assert events[0]["type"] == "test.event"
        assert events[0]["payload"] == {"key": "value"}

    def test_event_has_hash(self):
        store = EventStore(":memory:")
        event = store.add_event("x", {"a": 1})
        assert "event_hash" in event
        assert len(event["event_hash"]) == 64  # SHA-256 hex

    def test_list_events_limit(self):
        store = EventStore(":memory:")
        for i in range(5):
            store.add_event("e", {"i": i})
        assert len(store.list_events(limit=3)) == 3

    def test_list_events_ordering(self):
        store = EventStore(":memory:")
        store.add_event("first", {})
        store.add_event("second", {})
        events = store.list_events(limit=10)
        # Most recent first (DESC ordering)
        assert events[0]["type"] == "second"


@pytest.mark.unit
class TestEventBusWildcard:
    def test_wildcard_handler_receives_all(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        received = []

        def handler(event):
            received.append(event["type"])

        bus.subscribe("*", handler)
        asyncio.run(bus.emit("alpha", {}))
        asyncio.run(bus.emit("beta", {}))
        assert received == ["alpha", "beta"]

    def test_wildcard_plus_specific(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        wild = []
        specific = []

        bus.subscribe("*", lambda e: wild.append(e["type"]))
        bus.subscribe("specific", lambda e: specific.append(e["type"]))

        asyncio.run(bus.emit("specific", {}))
        asyncio.run(bus.emit("other", {}))
        assert wild == ["specific", "other"]
        assert specific == ["specific"]


@pytest.mark.unit
class TestEventBusMultipleSubscribers:
    def test_multiple_handlers(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        a, b = [], []
        bus.subscribe("evt", lambda e: a.append(1))
        bus.subscribe("evt", lambda e: b.append(2))
        asyncio.run(bus.emit("evt", {}))
        assert a == [1]
        assert b == [2]


@pytest.mark.unit
class TestEventBusUnsubscribe:
    def test_unsubscribe_handler(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        received = []

        def handler(event):
            received.append(1)

        bus.subscribe("evt", handler)
        asyncio.run(bus.emit("evt", {}))
        assert received == [1]

        bus.unsubscribe("evt", handler)
        asyncio.run(bus.emit("evt", {}))
        assert received == [1]  # no new entries

    def test_off_alias(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        received = []

        def handler(event):
            received.append(1)

        bus.on("evt", handler)
        asyncio.run(bus.emit("evt", {}))
        bus.off("evt", handler)
        asyncio.run(bus.emit("evt", {}))
        assert received == [1]


@pytest.mark.unit
class TestEventBusListEvents:
    def test_list_events_returns_subscribed_types(self):
        store = EventStore(":memory:")
        bus = EventBus(store)
        bus.subscribe("a", lambda e: None)
        bus.subscribe("b", lambda e: None)
        types = bus.list_events()
        assert "a" in types
        assert "b" in types
