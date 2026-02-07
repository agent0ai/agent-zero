import asyncio
import contextlib
import socket
from typing import Any, AsyncIterator

import pytest


@contextlib.asynccontextmanager
async def _run_asgi_app(app: Any) -> AsyncIterator[str]:
    import uvicorn

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)

    port = sock.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
        lifespan="off",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            await asyncio.sleep(0.01)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=5)
        finally:
            sock.close()


@pytest.mark.asyncio
async def test_socketio_wildcard_handler_only_runs_for_unhandled_events() -> None:
    import socketio

    handled_calls: list[tuple[str, Any]] = []
    wildcard_calls: list[str] = []

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

    @sio.on("handled", namespace="/ns")
    async def _handled(sid: str, data: Any) -> dict[str, Any]:
        handled_calls.append((sid, data))
        return {"path": "handled"}

    @sio.on("*", namespace="/ns")
    async def _wildcard(event: str, sid: str, data: Any) -> dict[str, Any]:
        wildcard_calls.append(event)
        return {"path": "wildcard", "event": event}

    app = socketio.ASGIApp(sio)

    async with _run_asgi_app(app) as base_url:
        client = socketio.AsyncClient()
        await client.connect(base_url, namespaces=["/ns"])
        try:
            res = await client.call("handled", {"x": 1}, namespace="/ns", timeout=2)
            assert res == {"path": "handled"}
            assert wildcard_calls == []

            res2 = await client.call("unhandled_event", {"x": 2}, namespace="/ns", timeout=2)
            assert res2 == {"path": "wildcard", "event": "unhandled_event"}
            assert wildcard_calls == ["unhandled_event"]
        finally:
            await client.disconnect()


@pytest.mark.asyncio
async def test_socketio_handler_return_values_ack_only_when_client_requests_ack() -> None:
    import socketio

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    sent_packets: list[Any] = []

    original_send_packet = sio._send_packet

    async def _record_send_packet(eio_sid: str, pkt: Any) -> None:
        sent_packets.append(pkt)
        await original_send_packet(eio_sid, pkt)

    sio._send_packet = _record_send_packet  # type: ignore[assignment]

    @sio.on("returns_value", namespace="/ns")
    async def _returns_value(_sid: str, _data: Any) -> dict[str, Any]:
        return {"ok": True}

    app = socketio.ASGIApp(sio)

    async with _run_asgi_app(app) as base_url:
        client = socketio.AsyncClient()
        await client.connect(base_url, namespaces=["/ns"])
        try:
            sent_packets.clear()
            await client.emit("returns_value", {"x": 1}, namespace="/ns")
            await asyncio.sleep(0.05)
            ack_packets = [p for p in sent_packets if getattr(p, "packet_type", None) in (3, 6)]
            assert ack_packets == []

            sent_packets.clear()
            res = await client.call("returns_value", {"x": 2}, namespace="/ns", timeout=2)
            assert res == {"ok": True}
            ack_packets = [p for p in sent_packets if getattr(p, "packet_type", None) in (3, 6)]
            assert len(ack_packets) >= 1
        finally:
            await client.disconnect()
