import asyncio
import contextlib
import socket
import sys
from pathlib import Path
from typing import Any, AsyncIterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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


def _write_handler_module(path: Path, class_name: str, event_type: str) -> None:
    path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "from typing import Any",
                "",
                "from python.helpers.websocket import WebSocketHandler",
                "",
                f"class {class_name}(WebSocketHandler):",
                "    @classmethod",
                "    def requires_auth(cls) -> bool:",
                "        return False",
                "",
                "    @classmethod",
                "    def requires_csrf(cls) -> bool:",
                "        return False",
                "",
                "    @classmethod",
                "    def get_event_types(cls) -> list[str]:",
                f"        return ['{event_type}']",
                "",
                "    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):",
                "        return {'ok': True}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_discovery_supports_folder_entries_and_ignores_deeper_nesting(
    tmp_path: Path,
) -> None:
    from python.helpers.websocket_namespace_discovery import (
        discover_websocket_namespaces,
    )

    folder = tmp_path / "orders"
    folder.mkdir()
    _write_handler_module(folder / "orders.py", "OrdersHandler", "orders_request")

    # Deeper nesting must be ignored (and must not be imported).
    nested = folder / "nested"
    nested.mkdir()
    (nested / "boom.py").write_text(
        "raise RuntimeError('should-not-import')\n", encoding="utf-8"
    )

    discoveries = discover_websocket_namespaces(
        handlers_folder=str(tmp_path), include_root_default=False
    )
    by_ns = {d.namespace: d for d in discoveries}

    assert "/orders" in by_ns
    entry = by_ns["/orders"]
    assert [cls.__name__ for cls in entry.handler_classes] == ["OrdersHandler"]


def test_discovery_folder_suffix_handler_stripped(tmp_path: Path) -> None:
    from python.helpers.websocket_namespace_discovery import (
        discover_websocket_namespaces,
    )

    folder = tmp_path / "sales_handler"
    folder.mkdir()
    _write_handler_module(folder / "main.py", "SalesHandler", "sales_request")

    discoveries = discover_websocket_namespaces(
        handlers_folder=str(tmp_path), include_root_default=False
    )
    namespaces = {d.namespace for d in discoveries}
    assert "/sales" in namespaces


def test_discovery_empty_folder_warns_and_treats_namespace_unregistered(
    tmp_path: Path, monkeypatch
) -> None:
    import socketio
    from flask import Flask

    from python.helpers.websocket_manager import WebSocketManager
    from python.helpers.websocket_namespace_discovery import (
        discover_websocket_namespaces,
    )
    from run_ui import configure_websocket_namespaces

    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "__init__.py").write_text("# init\n", encoding="utf-8")

    warnings: list[str] = []

    def _warn(message: str) -> None:
        warnings.append(message)

    monkeypatch.setattr(
        "python.helpers.print_style.PrintStyle.warning", staticmethod(_warn)
    )

    discoveries = discover_websocket_namespaces(
        handlers_folder=str(tmp_path), include_root_default=False
    )
    assert "/empty" not in {d.namespace for d in discoveries}
    assert any("empty" in msg.lower() for msg in warnings)

    # Integration check: treat as unregistered -> UNKNOWN_NAMESPACE connect_error.
    app = Flask("test_empty_folder_unregistered")
    app.secret_key = "test-secret"
    sio = socketio.AsyncServer(
        async_mode="asgi", cors_allowed_origins="*", namespaces="*"
    )
    lock = __import__("threading").RLock()
    manager = WebSocketManager(sio, lock)

    handlers_by_namespace: dict[str, list[Any]] = {}
    for discovery in discoveries:
        handlers_by_namespace[discovery.namespace] = [
            cls.get_instance(sio, lock) for cls in discovery.handler_classes
        ]

    configure_websocket_namespaces(
        webapp=app,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace=handlers_by_namespace,
    )

    asgi_app = socketio.ASGIApp(sio)

    async def _run() -> None:
        async with _run_asgi_app(asgi_app) as base_url:
            client = socketio.AsyncClient()
            connect_error_fut: asyncio.Future[Any] = (
                asyncio.get_running_loop().create_future()
            )

            async def _on_connect_error(data: Any) -> None:
                if not connect_error_fut.done():
                    connect_error_fut.set_result(data)

            client.on("connect_error", _on_connect_error, namespace="/empty")
            try:
                with pytest.raises(socketio.exceptions.ConnectionError):
                    await client.connect(base_url, namespaces=["/empty"])
                err = await asyncio.wait_for(connect_error_fut, timeout=2)
                assert err["message"] == "UNKNOWN_NAMESPACE"
                assert err["data"]["namespace"] == "/empty"
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

    asyncio.run(_run())


def test_discovery_invalid_modules_fail_fast_with_descriptive_errors(
    tmp_path: Path,
) -> None:
    from python.helpers.websocket_namespace_discovery import (
        discover_websocket_namespaces,
    )

    # 0 handlers in a *_handler.py module
    (tmp_path / "bad_handler.py").write_text(
        "class NotAHandler:\n    pass\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError) as excinfo:
        discover_websocket_namespaces(
            handlers_folder=str(tmp_path), include_root_default=False
        )
    assert "defines no WebSocketHandler subclasses" in str(excinfo.value)

    # 2+ handlers in a *_handler.py module
    tmp_path.joinpath("bad_handler.py").unlink()
    (tmp_path / "two_handler.py").write_text(
        "\n".join(
            [
                "from python.helpers.websocket import WebSocketHandler",
                "class A(WebSocketHandler):",
                "    @classmethod",
                "    def requires_auth(cls): return False",
                "    @classmethod",
                "    def requires_csrf(cls): return False",
                "    @classmethod",
                "    def get_event_types(cls): return ['two_a']",
                "    async def process_event(self, event_type, data, sid): return {'ok': True}",
                "class B(WebSocketHandler):",
                "    @classmethod",
                "    def requires_auth(cls): return False",
                "    @classmethod",
                "    def requires_csrf(cls): return False",
                "    @classmethod",
                "    def get_event_types(cls): return ['two_b']",
                "    async def process_event(self, event_type, data, sid): return {'ok': True}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError) as excinfo2:
        discover_websocket_namespaces(
            handlers_folder=str(tmp_path), include_root_default=False
        )
    message = str(excinfo2.value)
    assert "defines multiple WebSocketHandler subclasses" in message
    assert "A" in message and "B" in message
