"""Authenticated Files connection operations supplied by enabled plugins."""
import asyncio

from helpers.api import ApiHandler, Request
from helpers import file_connections as connections


class FileBrowserConnections(ApiHandler):
    async def process(self, input: dict, request: Request):
        try:
            return await asyncio.to_thread(dispatch, input)
        except (ValueError, PermissionError, FileNotFoundError) as error:
            return {"ok": False, "error": str(error)}
        except Exception:
            return {"ok": False, "error": "Connection operation failed. Check server access, credentials, and permissions."}


def dispatch(data):
    action = data.get("action")
    if action == "list":
        return connections.listing_config()
    if action == "save-connection":
        return {"connection": connections.save_connection(data.get("connection", {}))}
    if action == "remove-connection":
        connections.remove_connection(data.get("provider"), data.get("id"))
    elif action == "test":
        value, item = connections.get_connection(data.get("provider"), data.get("id"))
        connections.require(item, "browse")
        with value.open(item, connections.data_dir(value)) as fs:
            fs.list("")
    elif action in ("delete", "rename", "mkdir"):
        connections.mutate(action, data.get("path"), data.get("destination", ""))
    elif action == "editor":
        with connections.LOCK:
            return connections.editor(data.get("operation"), data.get("payload", {}))
    else:
        raise ValueError("Unknown connection action.")
    return {"ok": True}
