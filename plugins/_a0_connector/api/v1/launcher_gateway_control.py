"""POST /api/plugins/_a0_connector/v1/launcher_gateway_control."""
from __future__ import annotations

import asyncio
import uuid

from helpers.api import Request, Response
from helpers.ws_manager import ConnectionNotFoundError, get_shared_ws_manager

import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.ws_runtime import (
    active_launcher_gateway_sid,
    clear_pending_gateway_control,
    launcher_gateway_status,
    store_pending_gateway_control,
)


_CONTROL_EVENT = "connector_gateway_control"
_CONTROL_TIMEOUT_SECONDS = 8.0
_SCOPE_KEYS = ("files", "file_write", "code_execution", "browser", "computer_use")


class LauncherGatewayControl(connector_base.ProtectedConnectorApiHandler):
    """Apply an acknowledged control change to the active Launcher gateway."""

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "") or "").strip().lower()
        payload: dict = {"action": action}
        if action == "set_master":
            if not isinstance(input.get("enabled"), bool):
                return Response("enabled must be a boolean", status=400)
            payload["enabled"] = input["enabled"]
        elif action == "replace_scopes":
            scopes = input.get("scopes")
            if not isinstance(scopes, dict) or any(
                not isinstance(scopes.get(key), bool) for key in _SCOPE_KEYS
            ):
                return Response(
                    "scopes must contain boolean files, file_write, code_execution, browser, and computer_use values",
                    status=400,
                )
            normalized = {key: scopes[key] for key in _SCOPE_KEYS}
            if not normalized["files"]:
                normalized["file_write"] = False
            if not normalized["file_write"]:
                normalized["code_execution"] = False
            payload["scopes"] = normalized
        elif action != "emergency_disconnect":
            return Response("Unknown gateway control action", status=400)

        status = launcher_gateway_status()
        if status.get("multiple_hosts"):
            return Response("Multiple Launcher hosts are connected", status=409)
        sid = active_launcher_gateway_sid()
        if not sid:
            return Response("No Launcher host gateway is connected", status=409)

        request_id = str(uuid.uuid4())
        payload["request_id"] = request_id
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict] = loop.create_future()
        store_pending_gateway_control(
            request_id,
            sid=sid,
            future=future,
            loop=loop,
        )
        try:
            await get_shared_ws_manager().emit_to(
                "/ws",
                sid,
                _CONTROL_EVENT,
                payload,
                handler_id=f"{self.__class__.__module__}.{self.__class__.__name__}",
            )
            result = await asyncio.wait_for(future, timeout=_CONTROL_TIMEOUT_SECONDS)
        except ConnectionNotFoundError:
            return Response("Launcher host gateway disconnected", status=409)
        except asyncio.TimeoutError:
            return Response("Launcher host gateway did not acknowledge the change", status=504)
        finally:
            clear_pending_gateway_control(request_id)

        if not result.get("ok", False):
            return Response(
                str(result.get("error") or "Launcher host gateway rejected the change"),
                status=409,
            )
        return {
            "ok": True,
            "result": result,
            "status": launcher_gateway_status(),
        }
