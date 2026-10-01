from helpers.extension import Extension
from plugins._context_window.helpers import usage


class StoreContextUsage(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        payload = data if isinstance(data, dict) else {}
        if payload.get("exception") or not isinstance(payload.get("result"), list):
            usage.discard(self.agent)
            return
        usage.finalize(self.agent)
