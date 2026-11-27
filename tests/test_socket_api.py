"""Real Unix socket and CLI checks; also runnable with stdlib unittest."""

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import helpers
from helpers import socket_api, socket_cli


ROOT = Path(__file__).resolve().parents[1]
ECHO = """from helpers.socket_api import SocketHandler
class Echo(SocketHandler):
    async def process(self, input):
        return input
"""


@unittest.skipUnless(os.name == "posix", "Unix sockets require POSIX")
class SocketTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.loop_errors = []
        asyncio.get_running_loop().set_exception_handler(lambda loop, context: self.loop_errors.append(context))
        temporary = tempfile.TemporaryDirectory(prefix="a0-socket-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "run/a0.sock"
        self.app = types.SimpleNamespace(started=asyncio.Event(), release=asyncio.Event(), cancelled=asyncio.Event())

        # Substitute deployment roots, while exercising the actual framework class loader.
        files = types.ModuleType("helpers.files")
        files.USER_DIR = "usr"
        files.get_abs_path = lambda *parts: str(self.root.joinpath(*parts))
        plugins = types.ModuleType("helpers.plugins")
        plugins.find_plugin_dir = Mock(side_effect=lambda name: {
            "demo": str(self.root / "plugins/demo"),
            "custom": str(self.root / "usr/plugins/custom"),
        }.get(name))
        self.plugin_lookup = plugins.find_plugin_dir
        patches = [
            patch.dict(sys.modules, {"helpers.files": files, "helpers.plugins": plugins}),
            patch.object(helpers, "files", files, create=True),
            patch.object(helpers, "plugins", plugins, create=True),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        spec = importlib.util.spec_from_file_location("socket_test_modules", ROOT / "helpers/modules.py")
        modules = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modules)
        for item in [patch.dict(sys.modules, {"helpers.modules": modules}), patch.object(helpers, "modules", modules, create=True)]:
            item.start()
            self.addCleanup(item.stop)

        self.write("socket/ping.py", (ROOT / "socket/ping.py").read_text())
        self.write("socket/echo.py", ECHO)
        self.write("socket/slow.py", """from helpers.socket_api import SocketHandler
class Slow(SocketHandler):
    async def process(self, input):
        self.app.started.set()
        try:
            await self.app.release.wait()
        finally:
            self.app.cancelled.set()
        return input
""")
        self.server = socket_api.SocketServer(self.app, threading.RLock(), path=self.path)
        await self.server.start()
        self.addAsyncCleanup(self.server.close)

    async def asyncTearDown(self):
        await self.server.close()
        await asyncio.sleep(0)
        self.assertEqual(self.loop_errors, [], "Unexpected transport callback failure")

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    async def request(self, command="ping", arguments=None):
        return await asyncio.to_thread(socket_cli.call, command, arguments if arguments is not None else {}, path=self.path)

    async def raw_request(self, raw):
        reader, writer = await asyncio.open_unix_connection(str(self.path))
        try:
            writer.write(raw)
            writer.write_eof()
            response = await asyncio.wait_for(reader.readline(), 3)
            self.assertLessEqual(len(response), socket_api.MAX_MESSAGE_BYTES)
            self.assertEqual(await asyncio.wait_for(reader.read(), 3), b"")
            return json.loads(response)
        finally:
            writer.close()
            await writer.wait_closed()

    async def cli(self, *args, stdin=None):
        child = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "helpers.socket_cli", "--socket", str(self.path), *args,
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, err = await asyncio.wait_for(child.communicate(stdin), 5)
        return child.returncode, json.loads(out), err

    async def test_ping_and_all_arguments_preserved(self):
        self.assertEqual(await self.request(), {"ok": True, "result": {"message": "pong"}})
        args = {"text": "line 1\nline 2 — 你好", "limit": 2, "flag": True, "nested": {"items": [1, None]}}
        self.assertEqual(await self.request("echo", args), {"ok": True, "result": args})

    async def test_core_plugin_user_and_nested_routes(self):
        for name in ("socket/v1/nested.py", "plugins/demo/socket/nested/echo.py", "usr/plugins/custom/socket/echo.py", "usr/socket/custom_echo.py"):
            self.write(name, ECHO)
        for command in ("v1/nested", "plugins/demo/nested/echo", "plugins/custom/echo", "custom_echo"):
            with self.subTest(command=command):
                self.assertEqual((await self.request(command, {"route": command}))["result"], {"route": command})
        self.plugin_lookup.assert_any_call("demo")
        self.plugin_lookup.assert_any_call("custom")

    async def test_core_precedence_and_no_stale_route_cache(self):
        self.write("usr/socket/ping.py", ECHO)
        self.assertEqual((await self.request("ping", {"message": "wrong"}))["result"]["message"], "pong")
        self.assertEqual((await self.request("added"))["error"]["code"], "NOT_FOUND")
        path = self.write("socket/added.py", ECHO)
        self.assertTrue((await self.request("added"))["ok"])
        path.unlink()
        self.assertEqual((await self.request("added"))["error"]["code"], "NOT_FOUND")

    async def test_only_socket_handlers_are_callable(self):
        self.write("api/http_only.py", ECHO)
        self.write("socket/not_handler.py", "class NotHandler: pass\n")
        for command in ("missing", "http_only", "not_handler", "plugins/missing/test"):
            self.assertEqual((await self.request(command))["error"]["code"], "NOT_FOUND")

    async def test_rejects_path_traversal_and_suffixes(self):
        for command in ("../api/secret", "/etc/passwd", "plugins/../echo", "plugins/demo/../echo", "echo.py", "echo//x", "echo\\x", "%2e%2e/echo", "", "echo\x00"):
            with self.subTest(command=command):
                self.assertEqual((await self.request(command))["error"]["code"], "INVALID_COMMAND")

    async def test_rejects_symlink_escape_in_each_root(self):
        target = self.write("outside.py", "raise AssertionError('escaped handler was imported')\n")
        for location, command in (("socket/escape.py", "escape"), ("usr/socket/user_escape.py", "user_escape"), ("plugins/demo/socket/escape.py", "plugins/demo/escape")):
            link = self.root / location
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
            self.assertEqual((await self.request(command))["error"]["code"], "INVALID_COMMAND")

    async def test_validates_envelope_and_json(self):
        for raw in (b"[]\n", b"null\n", b"{bad}\n", b'{"command":"echo","args":{"x":NaN}}\n', b"\xff\n", '{"command":"ping"}'.encode("utf-16") + b"\n", b'{"command":"ping"}', b'{"command":"ping","unexpected":1}\n'):
            with self.subTest(raw=raw):
                self.assertEqual((await self.raw_request(raw))["error"]["code"], "INVALID_REQUEST")
        response = await self.raw_request(b'{"command":"ping","args":[]}\n')
        self.assertEqual(response["error"]["code"], "INVALID_ARGUMENT")

    async def test_only_one_request_is_executed_per_connection(self):
        response = await self.raw_request(b'{"command":"ping"}\n{"command":"slow"}\n')
        self.assertTrue(response["ok"])
        self.assertFalse(self.app.started.is_set())

    async def test_bounded_request_and_response(self):
        await self.server.close()
        with patch.object(socket_api, "MAX_MESSAGE_BYTES", 2048):
            await self.server.start()
            response = await self.raw_request(b"x" * 2049 + b"\n")
            self.assertEqual(response["error"]["code"], "REQUEST_TOO_LARGE")
            self.write("socket/huge.py", """from helpers.socket_api import SocketHandler
class Huge(SocketHandler):
    async def process(self, input):
        return {"text": "x" * 2048}
""")
            self.assertEqual((await self.request("huge"))["error"]["code"], "RESPONSE_TOO_LARGE")

    async def test_expected_errors_and_sanitized_unexpected_errors(self):
        self.write("socket/expected.py", """from helpers.socket_api import SocketHandler, SocketError
class Expected(SocketHandler):
    async def process(self, input):
        raise SocketError("INVALID_ARGUMENT", "text is required")
""")
        self.assertEqual((await self.request("expected"))["error"], {"code": "INVALID_ARGUMENT", "message": "text is required"})
        self.write("socket/conflict.py", """from helpers.socket_api import SocketHandler, SocketError
class Conflict(SocketHandler):
    async def process(self, input):
        raise SocketError("OPERATION_FAILED", "conflict", details={"error_kind": "dirty_tree_conflict", "conflicting_files": ["plugin.yaml"]})
""")
        status, response, _ = await self.cli("conflict")
        self.assertEqual(status, 1)
        self.assertEqual(response["error"]["details"]["conflicting_files"], ["plugin.yaml"])
        for body in ('raise RuntimeError("private-token")', 'return "text"', 'return {"n": float("nan")}', 'return {"bad": object()}'):
            self.write("socket/broken.py", "from helpers.socket_api import SocketHandler\nclass Broken(SocketHandler):\n    async def process(self, input):\n        " + body + "\n")
            with self.assertLogs(socket_api.logger, level="ERROR"):
                response = await self.request("broken")
            self.assertEqual(response, socket_api.error_response("INTERNAL_ERROR", "Socket handler failed."))
            self.assertNotIn("private-token", json.dumps(response))

    async def test_slow_handler_does_not_block_other_requests(self):
        slow = asyncio.create_task(self.request("slow", {"done": True}))
        await asyncio.wait_for(self.app.started.wait(), 2)
        try:
            self.assertTrue((await asyncio.wait_for(self.request(), 2))["ok"])
        finally:
            self.app.release.set()
        self.assertEqual((await slow)["result"], {"done": True})

    async def test_read_and_handler_timeouts(self):
        with patch.object(socket_api, "REQUEST_TIMEOUT", 0.05), patch.object(socket_api, "IO_TIMEOUT", 0.05):
            reader, writer = await asyncio.open_unix_connection(str(self.path))
            try:
                result = json.loads(await asyncio.wait_for(reader.readline(), 2))
                self.assertEqual(result["error"]["code"], "TIMEOUT")
            finally:
                writer.close()
                await writer.wait_closed()
            self.assertEqual((await self.request("slow"))["error"]["code"], "TIMEOUT")
            self.assertTrue(self.app.cancelled.is_set())

    async def test_operation_has_no_default_deadline(self):
        with patch.object(socket_api, "IO_TIMEOUT", 0.01):
            slow = asyncio.create_task(self.request("slow"))
            await asyncio.wait_for(self.app.started.wait(), 2)
            await asyncio.sleep(0.04)
            self.assertFalse(slow.done())
            self.app.release.set()
            self.assertTrue((await slow)["ok"])

    async def test_concurrent_large_payloads(self):
        arguments = {"text": "x" * (2 * 1024 * 1024)}
        responses = await asyncio.gather(*(self.cli("echo", "-", stdin=json.dumps(arguments).encode()) for _ in range(8)))
        self.assertTrue(all((status, response, err) == (0, {"ok": True, "result": arguments}, b"") for status, response, err in responses))

    async def test_client_timeout_does_not_retry_or_cancel_operation(self):
        with self.assertRaises(TimeoutError):
            await asyncio.to_thread(socket_cli.call, "slow", {}, path=self.path, timeout=0.05)
        self.assertTrue(self.app.started.is_set())
        self.assertFalse(self.app.cancelled.is_set())
        self.app.release.set()
        await asyncio.wait_for(self.app.cancelled.wait(), 2)

    async def test_permissions_and_duplicate_start(self):
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        inode = self.path.stat().st_ino
        other = socket_api.SocketServer(path=self.path)
        with self.assertRaises(BlockingIOError):
            await other.start()
        self.assertEqual(self.path.stat().st_ino, inode)
        self.assertTrue((await self.request())["ok"])

    async def test_different_user_cannot_connect(self):
        if os.geteuid() != 0:
            self.skipTest("Requires root to drop the client uid")
        child = await asyncio.create_subprocess_exec(sys.executable, "-c", (
            "import os,socket,sys; os.setgroups([]); os.setgid(65534); os.setuid(65534); "
            "s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1])"
        ), str(self.path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await child.communicate()
        self.assertNotEqual(child.returncode, 0)
        self.assertIn(b"PermissionError", err)

    async def test_shutdown_cancels_handlers_and_allows_restart(self):
        reader, writer = await asyncio.open_unix_connection(str(self.path))
        writer.write(b'{"command":"slow"}\n')
        await asyncio.wait_for(self.app.started.wait(), 2)
        await asyncio.wait_for(self.server.close(), 2)
        self.assertTrue(self.app.cancelled.is_set())
        self.assertEqual(await reader.read(), b"")
        writer.close()
        await writer.wait_closed()
        self.assertFalse(self.path.exists())
        await self.server.start()
        self.assertTrue((await self.request())["ok"])

    async def test_shutdown_closes_clients_even_before_handler_task_starts(self):
        writer = Mock(is_closing=Mock(return_value=False))
        self.server._accept(Mock(), writer)
        await self.server.close()
        writer.transport.abort.assert_called()

    async def test_stalled_response_write_aborts_client(self):
        reader = Mock(readline=AsyncMock(return_value=b'{"command":"ping"}\n'))
        writer = Mock(drain=AsyncMock(side_effect=TimeoutError), wait_closed=AsyncMock())
        await self.server._handle_client(reader, writer)
        writer.transport.abort.assert_called()
        writer.close.assert_called()

    async def test_stale_socket_recovery(self):
        await self.server.close()
        with socket.socket(socket.AF_UNIX) as stale:
            stale.bind(str(self.path))
        await self.server.start()
        self.assertTrue((await self.request())["ok"])

    async def test_does_not_replace_other_active_listener(self):
        await self.server.close()
        with socket.socket(socket.AF_UNIX) as active:
            active.bind(str(self.path))
            active.listen()
            inode = self.path.stat().st_ino
            with self.assertRaises(FileExistsError):
                await self.server.start()
            self.assertEqual(self.path.stat().st_ino, inode)

    async def test_refuses_files_symlinks_and_insecure_directory(self):
        await self.server.close()
        self.path.write_text("preserve")
        with self.assertRaises(FileExistsError):
            await self.server.start()
        self.assertEqual(self.path.read_text(), "preserve")
        self.path.unlink()
        target = self.write("target", "preserve")
        self.path.symlink_to(target)
        with self.assertRaises(FileExistsError):
            await self.server.start()
        self.assertTrue(self.path.is_symlink())
        self.path.unlink()
        self.path.parent.chmod(0o755)
        with self.assertRaises(PermissionError):
            await self.server.start()

    async def test_refuses_lock_symlinks(self):
        await self.server.close()
        lock = Path(str(self.path) + ".lock")
        lock.unlink()
        target = self.write("target", "preserve")
        lock.symlink_to(target)
        with self.assertRaises(OSError):
            await self.server.start()
        self.assertEqual(target.read_text(), "preserve")

    async def test_cleanup_preserves_replacement_file(self):
        self.path.unlink()
        self.path.write_text("replacement")
        await self.server.close()
        self.assertEqual(self.path.read_text(), "replacement")

    async def test_cli_success_failure_and_stdin(self):
        status, response, err = await self.cli("ping")
        self.assertEqual((status, response["result"], err), (0, {"message": "pong"}, b""))
        args = {"text": "quote ' and newline\n", "other": [1, False]}
        status, response, err = await self.cli("echo", "-", stdin=json.dumps(args).encode())
        self.assertEqual((status, response["result"], err), (0, args, b""))
        status, response, _ = await self.cli("missing")
        self.assertEqual((status, response["error"]["code"]), (1, "NOT_FOUND"))
        for raw in ("[]", "{invalid", '{"x":NaN}'):
            status, response, _ = await self.cli("echo", raw)
            self.assertEqual((status, response["error"]["code"]), (1, "INVALID_ARGUMENT"))

    async def test_cli_connection_failure(self):
        await self.server.close()
        status, response, err = await self.cli("ping")
        self.assertEqual((status, response["error"]["code"]), (1, "CONNECTION_ERROR"))
        self.assertIn(b"connection failed", err)

    async def test_client_rejects_invalid_responses(self):
        await self.server.close()
        for payload in (b'{}\n', b'{"ok":true,"result":[]}\n', b'{"ok":false,"error":"oops"}\n', b'{"ok":true,"result":{}}'):
            async def reply(reader, writer):
                await reader.readline()
                writer.write(payload)
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            server = await asyncio.start_unix_server(reply, path=str(self.path))
            try:
                with self.assertRaises(ValueError):
                    await self.request()
            finally:
                server.close()
                await server.wait_closed()
                if self.path.exists():
                    self.path.unlink()

    async def test_limits_are_configurable_at_process_start(self):
        child = await asyncio.create_subprocess_exec(
            sys.executable, "-c", "from helpers.socket_api import *; print(MAX_MESSAGE_BYTES, IO_TIMEOUT, REQUEST_TIMEOUT)",
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "A0_SOCKET_MAX_MESSAGE_BYTES": "2097152", "A0_SOCKET_IO_TIMEOUT": "120", "A0_SOCKET_REQUEST_TIMEOUT": "600"},
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, err = await child.communicate()
        self.assertEqual((child.returncode, out.strip(), err), (0, b"2097152 120.0 600.0", b""))
        for timeout in (-1, 0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                socket_cli.call("ping", {}, path=self.path, timeout=timeout)

    async def test_socket_lifespan_and_environment_path(self):
        await self.server.close()
        with patch.dict(os.environ, {"A0_SOCKET_PATH": str(self.path)}):
            self.assertEqual(socket_api.get_socket_path(), self.path)
            async with socket_api.socket_lifespan(self.app, threading.RLock()):
                self.assertTrue((await self.request())["ok"])
            self.assertFalse(self.path.exists())
            with self.assertRaisesRegex(RuntimeError, "application failed"):
                async with socket_api.socket_lifespan(self.app, threading.RLock()):
                    raise RuntimeError("application failed")
            self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
