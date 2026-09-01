from __future__ import annotations

import asyncio
import uuid

from helpers.api import ApiHandler, Request, Response
from helpers.ws_manager import ConnectionNotFoundError, get_shared_ws_manager
from plugins._a0_connector.helpers.ws_runtime import (
    active_launcher_gateway_sid,
    all_host_browser_metadata,
    clear_pending_browser_op,
    store_pending_browser_op,
)


_BROWSER_OP_EVENT = "connector_browser_op"
_BROWSER_OP_TIMEOUT_SECONDS = 8.0
_BROWSER_FAMILIES = {"chrome", "opera", "edge"}


class HostBrowserSetup(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        del request
        browser_family = str(input.get("browser_family", "") or "").strip().lower()
        if browser_family not in _BROWSER_FAMILIES:
            return Response("browser_family must be chrome, opera, or edge", status=400)

        connectors = [
            item
            for item in all_host_browser_metadata()
            if "open_remote_debugging" in (item.get("features") or [])
        ]
        gateway_sid = active_launcher_gateway_sid()
        gateway = next((item for item in connectors if item.get("sid") == gateway_sid), None)
        if gateway is not None:
            sid = str(gateway["sid"])
        elif len(connectors) == 1:
            sid = str(connectors[0]["sid"])
        elif connectors:
            return Response(
                "Multiple A0 CLI hosts are connected; disconnect all but the host to configure",
                status=409,
            )
        else:
            return Response(
                "Connect or update A0 CLI before opening a host browser setup page",
                status=409,
            )

        op_id = str(uuid.uuid4())
        payload = {
            "op_id": op_id,
            "context_id": "_browser_settings",
            "action": "open_remote_debugging",
            "browser_family": browser_family,
        }
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict] = loop.create_future()
        store_pending_browser_op(op_id, sid=sid, future=future, loop=loop)
        try:
            await get_shared_ws_manager().emit_to(
                "/ws",
                sid,
                _BROWSER_OP_EVENT,
                payload,
                handler_id=f"{self.__class__.__module__}.{self.__class__.__name__}",
            )
            result = await asyncio.wait_for(future, timeout=_BROWSER_OP_TIMEOUT_SECONDS)
        except ConnectionNotFoundError:
            return Response("The connected A0 CLI host disconnected", status=409)
        except asyncio.TimeoutError:
            return Response("A0 CLI did not open the browser setup page in time", status=504)
        finally:
            clear_pending_browser_op(op_id)

        if not result.get("ok", False):
            return Response(
                str(result.get("error") or "A0 CLI could not open the browser setup page"),
                status=409,
            )
        return {"ok": True, "result": result.get("result", {})}
