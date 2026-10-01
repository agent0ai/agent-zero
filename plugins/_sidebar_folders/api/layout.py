import threading

from helpers import kvp
from helpers.api import ApiHandler, Input, Output, Request, Response

STORE_KEY = "plugin_sidebar_folders"
KINDS = ("project", "chat", "task")
_lock = threading.RLock()


class Layout(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "get")
        if action not in ("get", "save"):
            return Response("Invalid layout action", 400)
        if action == "save":
            kind, ids = input.get("kind"), input.get("ids")
            if kind not in KINDS or not isinstance(ids, list) or len(ids) > 10000:
                return Response("Invalid sidebar order", 400)
            if any(not isinstance(item, str) or len(item) > 512 for item in ids):
                return Response("Invalid sidebar item ID", 400)
            if len(ids) != len(set(ids)):
                return Response("Sidebar item IDs must be unique", 400)

        with _lock:
            saved = kvp.get_persistent(STORE_KEY, {})
            order = {kind: saved.get(kind, []) for kind in KINDS}
            if action == "save":
                order[input["kind"]] = input["ids"]
                kvp.set_persistent(STORE_KEY, order)
        return {"ok": True, "order": order}
