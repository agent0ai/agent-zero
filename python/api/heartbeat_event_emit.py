from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.event_bus import SYSTEM_EVENTS, EventBus, EventStore


class HeartbeatEventEmit(ApiHandler):
    async def process(self, input: dict, request: Request):
        event_type = input.get("event_type")
        if not event_type:
            return Response(response="missing 'event_type'", status=400, mimetype="text/plain")

        payload = input.get("payload", {})

        db_path = files.get_abs_path("data/events.db")
        store = EventStore(db_path)
        bus = EventBus(store)
        event = await bus.emit(event_type, payload)

        return {
            "status": "emitted",
            "event": event,
            "known_event": event_type in SYSTEM_EVENTS,
        }
