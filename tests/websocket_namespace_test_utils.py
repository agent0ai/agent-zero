from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

ConnectionIdentity = tuple[str, str]  # (namespace, sid)


def nsid(namespace: str, sid: str) -> ConnectionIdentity:
    return (namespace, sid)


@dataclass(frozen=True)
class SocketIOCall:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    @property
    def namespace(self) -> str | None:
        value = self.kwargs.get("namespace")
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"Expected namespace to be str, got {type(value).__name__}")
        return value


class FakeSocketIOServer:
    """
    Test double for python-socketio AsyncServer.

    Captures calls and surfaces the optional Socket.IO namespace dimension via recorded kwargs.
    """

    def __init__(self) -> None:
        self._emit_calls: list[SocketIOCall] = []
        self._disconnect_calls: list[SocketIOCall] = []

        self.emit = AsyncMock(side_effect=self._emit)
        self.disconnect = AsyncMock(side_effect=self._disconnect)

    async def _emit(self, *args: Any, **kwargs: Any) -> None:
        self._emit_calls.append(SocketIOCall(args=args, kwargs=dict(kwargs)))

    async def _disconnect(self, *args: Any, **kwargs: Any) -> None:
        self._disconnect_calls.append(SocketIOCall(args=args, kwargs=dict(kwargs)))

    @property
    def emit_calls(self) -> list[SocketIOCall]:
        return self._emit_calls

    @property
    def disconnect_calls(self) -> list[SocketIOCall]:
        return self._disconnect_calls
