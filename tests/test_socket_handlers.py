"""Exercise shared operations with isolated state; no providers or installed plugins."""

import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import helpers
from helpers import socket_handlers
from helpers.socket_api import SocketError


ROOT = Path(__file__).resolve().parents[1]
try:
    from werkzeug.wrappers import Response
except ImportError:
    class Response:
        """Minimal response fixture for running these checks without Flask installed."""
        def __init__(self, response="", status=200, **kwargs):
            self.data, self.status_code = response, status
            self.is_streamed = False
            self.closed = False

        def get_data(self, as_text=False):
            return self.data

        def get_json(self):
            return json.loads(self.data)

        def close(self):
            self.closed = True


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.context = types.SimpleNamespace(id="target", paused=False, get_agent=lambda: None)
        self.context.communicate = Mock(return_value=types.SimpleNamespace(result=AsyncMock(return_value="answer")))
        self.contexts = {"target": self.context}
        contexts = self.contexts

        class ApiHandler:
            def __init__(self, app, thread_lock):
                self.app, self.thread_lock = app, thread_lock

            def use_context(self, ctxid):
                return contexts[ctxid]

        self.module("werkzeug.wrappers", Response=Response)
        self.module("helpers.api", ApiHandler=ApiHandler, Request=object, Response=Response, Input=dict, Output=dict)
        self.agent_context = Mock(get=lambda ctxid: contexts.get(ctxid))
        self.module("agent", AgentContext=self.agent_context, UserMessage=lambda *args, **kw: types.SimpleNamespace(**kw))
        self.app = object()
        self.lock = threading.RLock()

    def module(self, name, **attributes):
        module = types.ModuleType(name)
        module.__dict__.update(attributes)
        item = patch.dict(sys.modules, {name: module})
        item.start()
        self.addCleanup(item.stop)
        parent, _, leaf = name.rpartition(".")
        if parent in sys.modules:
            item = patch.object(sys.modules[parent], leaf, module, create=True)
            item.start()
            self.addCleanup(item.stop)
        return module

    def load(self, path, name=None):
        name = name or path.replace("/", ".").removesuffix(".py")
        spec = importlib.util.spec_from_file_location(name, ROOT / path)
        module = importlib.util.module_from_spec(spec)
        item = patch.dict(sys.modules, {name: module})
        item.start()
        self.addCleanup(item.stop)
        spec.loader.exec_module(module)
        return module

    def handler(self, path):
        module = self.load(path, "socket_fixture")
        cls = next(value for value in vars(module).values() if isinstance(value, type) and issubclass(value, socket_handlers.JsonApiHandler))
        return cls(self.app, self.lock)

    async def test_explicit_chat_target_and_pause_shared_operation(self):
        self.load("api/pause.py")
        handler = self.handler("socket/pause.py")
        for args in ({}, {"context": ""}, {"context": []}, {"context": "missing"}):
            with self.assertRaises(SocketError):
                await handler.process(args)
        self.assertFalse(self.context.paused)
        result = await handler.process({"context": "target", "paused": True})
        self.assertTrue(self.context.paused)
        self.assertTrue(result["pause"])

    async def test_all_arguments_app_and_lock_forwarded_without_http_request(self):
        seen = []
        class Operation:
            def __init__(self, app, lock):
                seen.extend([app, lock])
            async def process(self, args, request):
                seen.extend([args, request])
                return {"data": args}
        self.module("api.projects", Projects=Operation)
        args = {"action": "list", "extension_field": {"nested": [None, 3]}}
        result = await self.handler("socket/projects.py").process(args)
        self.assertEqual(result, {"data": args})
        self.assertEqual(seen, [self.app, self.lock, args, None])
        self.assertIs(seen[2], args)

    async def test_project_activation_requires_existing_context(self):
        invoked = AsyncMock(return_value={})
        self.module("api.projects", Projects=lambda *args: types.SimpleNamespace(process=invoked))
        handler = self.handler("socket/projects.py")
        for args in ({"action": "activate"}, {"action": "deactivate", "context_id": "missing"}):
            with self.assertRaises(SocketError):
                await handler.process(args)
        invoked.assert_not_called()

    async def test_failures_preserve_structured_conflicts(self):
        failure = {"success": False, "error": "Local edits conflict", "error_kind": "dirty_tree_conflict", "conflicting_files": ["plugin.yaml"]}
        for result in (failure, {"ok": False, "error": "bad action"}, {"error": "task missing"}):
            with self.assertRaises(SocketError) as caught:
                socket_handlers.json_result(result)
            self.assertEqual(caught.exception.code, "OPERATION_FAILED")
            self.assertEqual(caught.exception.details, result)

    async def test_http_failures_and_json_responses(self):
        for status in (400, 404, 500):
            with self.assertRaises(SocketError) as caught:
                socket_handlers.json_result(Response("operation failed", status=status))
            self.assertEqual(caught.exception.code, f"HTTP_{status}")
        self.assertEqual(socket_handlers.json_result(Response('{"data":42}', mimetype="application/json")), {"data": 42})
        with self.assertRaises(TypeError):
            socket_handlers.json_result([])

    def message_dependencies(self):
        self.module("helpers.files", get_abs_path=lambda *parts: str(Path(*parts)))
        self.extension = self.module("helpers.extension", call_extensions_async=AsyncMock())
        self.queue = self.module("helpers.message_queue", log_user_message=Mock())
        self.module("helpers.security", safe_filename=lambda name: Path(name).name)
        self.module("helpers.defer", DeferredTask=object)
        return self.load("api/message.py")

    async def test_message_socket_and_http_json_share_dispatch(self):
        module = self.message_dependencies()
        args = {"context": "target", "text": "hello", "message_id": "msg-1"}
        result = await self.handler("socket/message.py").process(args)
        self.assertEqual(result, {"message": "answer", "context": "target"})
        self.assertEqual(self.context.communicate.call_args.args[0].message, "hello")
        request = types.SimpleNamespace(content_type="application/json", get_json=lambda: args)
        http = await module.Message(self.app, self.lock).process({}, request)
        self.assertEqual(http, result)
        self.assertEqual(self.extension.call_extensions_async.await_count, 2)
        self.assertEqual(self.queue.log_user_message.call_count, 2)

    async def test_message_async_returns_acceptance(self):
        self.message_dependencies()
        self.load("api/message_async.py")
        result = await self.handler("socket/message_async.py").process({"context": "target", "text": "hello"})
        self.assertEqual(result, {"message": "Message received.", "context": "target"})
        self.context.communicate.return_value.result.assert_not_awaited()

    async def test_message_keeps_multipart_uploads(self):
        module = self.message_dependencies()
        upload = Mock(filename="note.txt")
        request = types.SimpleNamespace(content_type="multipart/form-data", form={"context": "target", "text": "attached"}, files=types.SimpleNamespace(getlist=lambda key: [upload]))
        with tempfile.TemporaryDirectory() as folder, patch.object(module.files, "get_abs_path", side_effect=lambda *parts: str(Path(folder) / "note.txt") if len(parts) > 1 else folder):
            await module.Message(self.app, self.lock).process({}, request)
            upload.save.assert_called_once_with(str(Path(folder) / "note.txt"))
        self.assertEqual(self.context.communicate.call_args.args[0].attachments, ["/a0/usr/uploads/note.txt"])

    async def test_installer_reuses_git_update_and_index_logic(self):
        self.module("werkzeug.datastructures", FileStorage=object)
        install = self.module("plugins._plugin_installer.helpers.install", get_plugin_hub_index=Mock(return_value={"index": {"plugins": {}}, "installed_plugins": []}), install_from_git=Mock(return_value={"success": True}), install_uploaded_zip=Mock(), update_from_git=Mock(return_value={"success": True}))
        self.module("helpers.git", get_version=lambda: "v3.0.0")
        compatibility = self.module("plugins._plugin_installer.helpers.compatibility", get_plugin_compatibility=Mock(return_value={"compatible": True}))
        self.load("plugins/_plugin_installer/api/plugin_install.py")
        handler = self.handler("plugins/_plugin_installer/socket/plugin_install.py")
        self.assertIn("index", await handler.process({"action": "fetch_index"}))
        self.assertTrue((await handler.process({"action": "check_compatibility", "git_url": "https://example.test/plugin"}))["compatible"])
        compatibility.get_plugin_compatibility.assert_called_once_with("https://example.test/plugin", "v3.0.0")
        compatibility.get_plugin_compatibility.return_value = {"compatible": None, "error": "Manifest unavailable"}
        advisory = await handler.process({"action": "check_compatibility", "git_url": "https://example.test/plugin"})
        self.assertIsNone(advisory["compatible"])
        self.assertEqual(advisory["error"], "Manifest unavailable")
        await handler.process({"action": "install_git", "git_url": "https://example.test/plugin", "plugin_name": "demo"})
        install.install_from_git.assert_called_once_with(url="https://example.test/plugin", token=None, plugin_name="demo", thumbnail_url="")
        await handler.process({"action": "update_plugin", "plugin_name": "demo"})
        install.update_from_git.assert_called_once_with("demo")
        for args in ({}, {"action": "install_git"}):
            with self.assertRaises(SocketError):
                await handler.process(args)

    async def test_zip_copies_source_through_upload_helper(self):
        self.module("werkzeug.datastructures", FileStorage=lambda stream, filename: types.SimpleNamespace(stream=stream, filename=filename))
        seen = []
        def install(file):
            seen.extend([file.stream.read(), file.filename])
            return {"success": True}
        self.module("plugins._plugin_installer.helpers.install", install_uploaded_zip=install)
        handler = self.handler("plugins/_plugin_installer/socket/plugin_install.py")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "plugin.zip"
            path.write_bytes(b"archive")
            await handler.process({"action": "install_zip", "zip_path": str(path)})
            self.assertEqual(path.read_bytes(), b"archive")
        self.assertEqual(seen, [b"archive", "plugin.zip"])
        for path in ("relative.zip", "/missing/archive.zip", None):
            with self.assertRaises(SocketError):
                await handler.process({"action": "install_zip", "zip_path": path})

    async def test_scan_returns_report_and_cleans_its_temporary_context(self):
        self.contexts["scan-target"] = self.context
        self.module("helpers.guids", generate_id=lambda: "scan-target")
        self.module("helpers.message_queue", log_user_message=Mock())
        persistence = self.module("helpers.persist_chat", remove_chat=Mock())
        self.module("plugins._plugin_scan.helpers.prompt", build_prompt=lambda url, checks: "scan prompt")
        self.load("plugins/_plugin_scan/api/plugin_scan_run.py")
        handler = self.handler("plugins/_plugin_scan/socket/plugin_scan_run.py")
        result = await handler.process({"git_url": "https://example.test/plugin", "checks": ["structure"]})
        self.assertEqual(result["report"], "answer")
        self.agent_context.remove.assert_called_once_with("scan-target")
        persistence.remove_chat.assert_called_once_with("scan-target")
        with self.assertRaises(SocketError):
            await handler.process({})

    async def test_scheduler_run_uses_existing_engine_and_reports_errors(self):
        scheduler = types.SimpleNamespace(
            reload=AsyncMock(), get_task_by_uuid=Mock(return_value=types.SimpleNamespace(state="idle")),
            run_task_by_uuid=AsyncMock(), serialize_task=Mock(return_value={"uuid": "task-1", "state": "running"}),
        )
        self.module("helpers.task_scheduler", TaskScheduler=types.SimpleNamespace(get=lambda: scheduler), TaskState=types.SimpleNamespace(RUNNING="running"))
        self.module("helpers.print_style", PrintStyle=Mock())
        self.module("helpers.localization", Localization=Mock())
        self.load("plugins/_scheduler/api/scheduler_task_run.py")
        handler = self.handler("plugins/_scheduler/socket/scheduler_task_run.py")
        result = await handler.process({"task_id": "task-1"})
        self.assertEqual(result["task"]["uuid"], "task-1")
        scheduler.run_task_by_uuid.assert_awaited_once_with("task-1")
        scheduler.get_task_by_uuid.return_value = None
        with self.assertRaises(SocketError) as caught:
            await handler.process({"task_id": "missing"})
        self.assertEqual(caught.exception.code, "OPERATION_FAILED")
        scheduler.run_task_by_uuid.assert_awaited_once()

    async def test_blocking_operation_does_not_block_other_operations(self):
        started, release = threading.Event(), threading.Event()
        async def blocking():
            started.set()
            if not release.wait(3):
                raise TimeoutError("test did not release worker")
            return 1
        slow = asyncio.create_task(socket_handlers._in_worker(blocking))
        self.assertTrue(await asyncio.to_thread(started.wait, 2))
        try:
            result = await asyncio.wait_for(socket_handlers._in_worker(AsyncMock(return_value=2)), 1)
            self.assertEqual(result, 2)
        finally:
            release.set()
            self.assertEqual(await slow, 1)

    async def test_cancellation_reaches_worker_coroutine(self):
        started, cancelled = threading.Event(), threading.Event()
        async def waiting():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        task = asyncio.create_task(socket_handlers._in_worker(waiting))
        self.assertTrue(await asyncio.to_thread(started.wait, 2))
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(await asyncio.to_thread(cancelled.wait, 2))


if __name__ == "__main__":
    unittest.main()
