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
async def test_unknown_namespace_connect_error_can_be_made_deterministic() -> None:
    """
    Library-semantics test: demonstrate a deterministic connect_error payload shape for
    unknown namespaces using a server-side allowlist gatekeeper.
    """

    import socketio
    from socketio import packet

    sio = socketio.AsyncServer(
        async_mode="asgi", cors_allowed_origins="*", namespaces="*"
    )

    allowed_namespaces = {"/known", "/"}

    original_handle_connect = sio._handle_connect

    async def _gatekeeper_handle_connect(
        eio_sid: str, namespace: str | None, data: Any
    ) -> None:
        namespace = namespace or "/"
        if namespace not in allowed_namespaces:
            await sio._send_packet(
                eio_sid,
                sio.packet_class(
                    packet.CONNECT_ERROR,
                    data={
                        "message": "UNKNOWN_NAMESPACE",
                        "data": {"code": "UNKNOWN_NAMESPACE", "namespace": namespace},
                    },
                    namespace=namespace,
                ),
            )
            return

        await original_handle_connect(eio_sid, namespace, data)

    sio._handle_connect = _gatekeeper_handle_connect  # type: ignore[assignment]

    app = socketio.ASGIApp(sio)

    async with _run_asgi_app(app) as base_url:
        client = socketio.AsyncClient()
        connect_error_fut: asyncio.Future[Any] = (
            asyncio.get_running_loop().create_future()
        )

        async def _on_connect_error(data: Any) -> None:
            if not connect_error_fut.done():
                connect_error_fut.set_result(data)

        client.on("connect_error", _on_connect_error, namespace="/unknown")

        try:
            with pytest.raises(socketio.exceptions.ConnectionError):
                await client.connect(base_url, namespaces=["/unknown"])

            err = await asyncio.wait_for(connect_error_fut, timeout=2)
            assert err["message"] == "UNKNOWN_NAMESPACE"
            assert err["data"] == {"code": "UNKNOWN_NAMESPACE", "namespace": "/unknown"}
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
