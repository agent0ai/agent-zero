import asyncio
import os

from python.helpers.event_bus import EventBus, EventStore


def test_event_bus_persists_and_dispatches(tmp_path):
    db_path = os.path.join(tmp_path, "events.db")
    store = EventStore(db_path)
    bus = EventBus(store)

    handled = []

    def handler(event):
        handled.append(event["type"])

    bus.subscribe("calendar.event_created", handler)
    asyncio.run(bus.emit("calendar.event_created", {"id": 123, "title": "Kickoff"}))

    events = store.list_events(limit=10)
    assert len(events) == 1
    assert events[0]["type"] == "calendar.event_created"
    assert handled == ["calendar.event_created"]


def test_event_bus_supports_async_handlers(tmp_path):
    db_path = os.path.join(tmp_path, "events.db")
    store = EventStore(db_path)
    bus = EventBus(store)

    handled = []

    async def handler(event):
        handled.append(event["payload"]["status"])

    bus.subscribe("life.event_emitted", handler)
    asyncio.run(bus.emit("life.event_emitted", {"status": "ok"}))

    assert handled == ["ok"]
