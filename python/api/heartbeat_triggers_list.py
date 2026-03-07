from python.helpers.api import ApiHandler, Request
from python.helpers.event_triggers import TriggerStore


class HeartbeatTriggersList(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request):
        store = TriggerStore()
        triggers = store.list_all()
        return {"triggers": [t.to_dict() for t in triggers]}
