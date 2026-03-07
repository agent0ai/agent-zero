from python.helpers.api import ApiHandler, Request, Response
from python.helpers.event_triggers import TriggerStore, TriggerType


class HeartbeatTriggerUpdate(ApiHandler):
    async def process(self, input: dict, request: Request):
        trigger_id = input.get("id")
        if not trigger_id:
            return Response(response="missing 'id'", status=400, mimetype="text/plain")

        store = TriggerStore()
        trigger = store.get(trigger_id)
        if trigger is None:
            return Response(response="trigger not found", status=404, mimetype="text/plain")

        if "type" in input:
            try:
                trigger.type = TriggerType(input["type"])
            except ValueError:
                valid = [t.value for t in TriggerType]
                return Response(
                    response=f"invalid type, must be one of {valid}",
                    status=400,
                    mimetype="text/plain",
                )

        if "config" in input:
            trigger.config = input["config"]
        if "items" in input:
            trigger.items = input["items"]
        if "enabled" in input:
            trigger.enabled = bool(input["enabled"])

        store.save(trigger)
        return {"status": "updated", "trigger": trigger.to_dict()}
