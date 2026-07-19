from __future__ import annotations

from typing import Any

from helpers.extension import Extension
from helpers.ws_manager import WsResult
from plugins._editor.api.ws_editor import WsEditor


class EditorWebuiWsEvents(Extension):
    async def execute(
        self,
        instance: Any = None,
        sid: str = "",
        event_type: str = "",
        data: dict[str, Any] | None = None,
        response_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if not event_type.startswith("editor_") or instance is None or response_data is None:
            return

        handler = WsEditor(
            instance.socketio,
            instance.lock,
            manager=instance.manager,
            namespace=instance.namespace,
        )
        result = await handler.process(event_type, data or {}, sid)
        if result is None:
            return

        if isinstance(result, WsResult):
            payload = result.as_result(
                handler_id=handler.identifier,
                fallback_correlation_id=(data or {}).get("correlationId"),
            )
            if payload.get("ok"):
                response_data.update(payload.get("data") or {})
            else:
                response_data["editor_error"] = payload.get("error") or {
                    "code": "EDITOR_ERROR",
                    "error": "Editor request failed",
                }
            return

        response_data.update(result)
