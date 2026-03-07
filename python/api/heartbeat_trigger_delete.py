from python.helpers.api import ApiHandler, Request, Response
from python.helpers.event_triggers import TriggerStore


class HeartbeatTriggerDelete(ApiHandler):
    async def process(self, input: dict, request: Request):
        trigger_id = input.get("id")
        if not trigger_id:
            return Response(response="missing 'id'", status=400, mimetype="text/plain")

        store = TriggerStore()
        existing = store.get(trigger_id)
        if existing is None:
            return Response(response="trigger not found", status=404, mimetype="text/plain")

        store.delete(trigger_id)
        return {"status": "deleted", "id": trigger_id}
