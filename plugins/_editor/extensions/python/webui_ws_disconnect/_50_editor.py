from __future__ import annotations

from typing import Any

from helpers.extension import Extension
from plugins._editor.api.ws_editor import WsEditor


class EditorWebuiWsDisconnect(Extension):
    async def execute(
        self,
        instance: Any = None,
        sid: str = "",
        **kwargs: Any,
    ) -> None:
        if instance is None:
            return
        handler = WsEditor(
            instance.socketio,
            instance.lock,
            manager=instance.manager,
            namespace=instance.namespace,
        )
        await handler.on_disconnect(sid)
