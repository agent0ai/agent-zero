from python.helpers.api import ApiHandler, Request, Response
from python.helpers.event_triggers import HeartbeatTrigger, TriggerStore, TriggerType


class HeartbeatTriggerCreate(ApiHandler):
    async def process(self, input: dict, request: Request):
        trigger_type_str = input.get("type")
        if not trigger_type_str:
            return Response(response="missing 'type'", status=400, mimetype="text/plain")

        try:
            trigger_type = TriggerType(trigger_type_str)
        except ValueError:
            valid = [t.value for t in TriggerType]
            return Response(
                response=f"invalid type, must be one of {valid}",
                status=400,
                mimetype="text/plain",
            )

        config = input.get("config", {})
        items = input.get("items", [])
        enabled = input.get("enabled", True)

        trigger = HeartbeatTrigger.new(trigger_type, config, items, enabled=enabled)
        store = TriggerStore()
        store.save(trigger)

        return {"status": "created", "trigger": trigger.to_dict()}
