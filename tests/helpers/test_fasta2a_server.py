"""Comprehensive unit tests for python/helpers/fasta2a_server.py — A2A protocol server."""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset DynamicA2AProxy singleton between tests to avoid cross-test pollution."""
    import python.helpers.fasta2a_server as fas

    old = fas.DynamicA2AProxy._instance
    fas.DynamicA2AProxy._instance = None
    yield
    fas.DynamicA2AProxy._instance = old


@pytest.fixture
def mock_settings():
    """Settings dict with mcp_server_token and a2a_server_enabled."""
    return {
        "mcp_server_token": "test-token-12345",
        "a2a_server_enabled": True,
    }


# --- is_available / get_proxy ---


class TestIsAvailableAndGetProxy:
    def test_get_proxy_returns_singleton(self):
        with patch("python.helpers.fasta2a_server.settings") as mock_settings_mod:
            mock_settings_mod.get_settings.return_value = {"mcp_server_token": "", "a2a_server_enabled": True}
            with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            with patch("python.helpers.fasta2a_server.PrintStyle"):
                                from python.helpers.fasta2a_server import get_proxy, DynamicA2AProxy

                                p1 = get_proxy()
                                p2 = get_proxy()
                                assert p1 is p2
                                assert isinstance(p1, DynamicA2AProxy)

    def test_is_available_false_when_fasta2a_not_installed(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", False):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = {"mcp_server_token": "", "a2a_server_enabled": True}
                import python.helpers.fasta2a_server as fas

                fas.DynamicA2AProxy._instance = None
                result = fas.is_available()
                assert result is False


# --- AgentZeroWorker._convert_message ---


class TestAgentZeroWorkerConvertMessage:
    def test_convert_message_text_only(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        broker = MagicMock()
                        storage = MagicMock()
                        worker = AgentZeroWorker(broker=broker, storage=storage)

                        a2a_msg = {
                            "parts": [{"kind": "text", "text": "Hello world"}],
                            "metadata": {},
                        }
                        result = worker._convert_message(a2a_msg)
                        assert result.message == "Hello world"
                        assert result.attachments == []

    def test_convert_message_multiple_text_parts(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        a2a_msg = {
                            "parts": [
                                {"kind": "text", "text": "Part 1"},
                                {"kind": "text", "text": "Part 2"},
                            ],
                        }
                        result = worker._convert_message(a2a_msg)
                        assert result.message == "Part 1\nPart 2"

    def test_convert_message_with_file_attachments(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        a2a_msg = {
                            "parts": [
                                {"kind": "text", "text": "See file"},
                                {"kind": "file", "file": {"uri": "file:///path/to/doc.pdf"}},
                            ],
                        }
                        result = worker._convert_message(a2a_msg)
                        assert result.message == "See file"
                        assert result.attachments == ["file:///path/to/doc.pdf"]

    def test_convert_message_ignores_non_text_non_file_parts(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        a2a_msg = {"parts": [{"kind": "other", "data": "x"}]}
                        result = worker._convert_message(a2a_msg)
                        assert result.message == ""
                        assert result.attachments == []

    def test_convert_message_empty_parts(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        a2a_msg = {}
                        result = worker._convert_message(a2a_msg)
                        assert result.message == ""
                        assert result.attachments == []


# --- AgentZeroWorker.run_task / cancel_task ---


class TestAgentZeroWorkerRunTask:
    @pytest.mark.asyncio
    async def test_run_task_updates_storage_on_success(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        mock_storage = AsyncMock()
                        mock_storage.update_task = AsyncMock()

                        mock_cfg = MagicMock()
                        mock_context = MagicMock()
                        mock_context.id = "ctx-1"
                        mock_context.log = MagicMock()
                        mock_task = AsyncMock()
                        mock_task.result = AsyncMock(return_value="Response text")
                        mock_context.communicate = MagicMock(return_value=mock_task)

                        with patch("python.helpers.fasta2a_server.initialize_agent", return_value=mock_cfg):
                            with patch("python.helpers.fasta2a_server.AgentContext", return_value=mock_context):
                                with patch("python.helpers.fasta2a_server.AgentContextType"):
                                    with patch("python.helpers.fasta2a_server.projects"):
                                        with patch("python.helpers.fasta2a_server.remove_chat"):
                                            with patch("python.helpers.fasta2a_server.AgentContext.remove"):
                                                with patch("python.helpers.fasta2a_server.PrintStyle"):
                                                    worker = AgentZeroWorker(broker=MagicMock(), storage=mock_storage)
                                                    params = {
                                                        "id": "task-1",
                                                        "message": {"parts": [{"kind": "text", "text": "Hi"}]},
                                                    }
                                                    await worker.run_task(params)

                        mock_storage.update_task.assert_awaited()
                        call_kw = mock_storage.update_task.call_args[1]
                        assert call_kw["task_id"] == "task-1"
                        assert call_kw["state"] == "completed"
                        assert "new_messages" in call_kw

    @pytest.mark.asyncio
    async def test_run_task_updates_storage_on_failure(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        mock_storage = AsyncMock()
                        mock_storage.update_task = AsyncMock()

                        with patch("python.helpers.fasta2a_server.initialize_agent", side_effect=RuntimeError("Boom")):
                            with patch("python.helpers.fasta2a_server.AgentContext"):
                                with patch("python.helpers.fasta2a_server.projects"):
                                    with patch("python.helpers.fasta2a_server.remove_chat"):
                                        with patch("python.helpers.fasta2a_server.AgentContext.remove"):
                                            with patch("python.helpers.fasta2a_server.PrintStyle"):
                                                worker = AgentZeroWorker(broker=MagicMock(), storage=mock_storage)
                                                params = {"id": "task-2", "message": {"parts": []}}
                                                await worker.run_task(params)

                        mock_storage.update_task.assert_awaited_with(
                            task_id="task-2",
                            state="failed",
                        )

    @pytest.mark.asyncio
    async def test_cancel_task_updates_storage(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        mock_storage = AsyncMock()
                        mock_storage.update_task = AsyncMock()

                        with patch("python.helpers.fasta2a_server.PrintStyle"):
                            worker = AgentZeroWorker(broker=MagicMock(), storage=mock_storage)
                            await worker.cancel_task({"id": "task-3"})

                        mock_storage.update_task.assert_awaited_with(task_id="task-3", state="canceled")


# --- DynamicA2AProxy __call__ — ASGI behavior ---


class TestDynamicA2AProxyCall:
    @pytest.mark.asyncio
    async def test_returns_503_when_fasta2a_not_available(self, mock_settings):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", False):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = mock_settings
                import python.helpers.fasta2a_server as fas

                proxy = fas.DynamicA2AProxy._instance or fas.DynamicA2AProxy()
                fas.DynamicA2AProxy._instance = proxy

                send_calls = []

                async def send(msg):
                    send_calls.append(msg)

                scope = {"type": "http", "path": "/", "method": "GET"}
                receive = AsyncMock(return_value={"type": "http.disconnect"})

                await proxy(scope, receive, send)

                assert any(c.get("status") == 503 for c in send_calls if isinstance(c, dict))
                assert "503" in str(send_calls)

    @pytest.mark.asyncio
    async def test_returns_403_when_a2a_disabled(self, mock_settings):
        disabled_settings = {"mcp_server_token": "tok", "a2a_server_enabled": False}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = disabled_settings
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = MagicMock()
                            proxy._startup_done = True

                            send_calls = []

                            async def send(msg):
                                send_calls.append(msg)

                            scope = {"type": "http", "path": "/", "method": "GET"}
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            await proxy(scope, receive, send)

                            assert any(c.get("status") == 403 for c in send_calls if isinstance(c, dict))

    @pytest.mark.asyncio
    async def test_returns_401_when_token_invalid_in_path(self, mock_settings):
        cfg = {"mcp_server_token": "correct-token", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = MagicMock()
                            proxy._startup_done = True

                            send_calls = []

                            async def send(msg):
                                send_calls.append(msg)

                            scope = {"type": "http", "path": "/t-wrong-token/", "method": "GET"}
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            with patch("python.helpers.settings.get_settings", return_value=cfg):
                                await proxy(scope, receive, send)

                            assert any(c.get("status") == 401 for c in send_calls if isinstance(c, dict))

    @pytest.mark.asyncio
    async def test_accepts_valid_token_in_path(self, mock_settings):
        cfg = {"mcp_server_token": "valid-token-123", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                mock_app = AsyncMock()
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = mock_app
                            proxy._startup_done = True

                            scope = {"type": "http", "path": "/t-valid-token-123/.well-known/agent.json", "method": "GET"}
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            with patch("python.helpers.settings.get_settings", return_value=cfg):
                                await proxy(scope, receive, AsyncMock())

                            mock_app.assert_awaited_once()
                            call_scope = mock_app.call_args[0][0]
                            assert call_scope["path"] == "/.well-known/agent.json"

    @pytest.mark.asyncio
    async def test_extracts_project_from_path_and_delegates(self, mock_settings):
        cfg = {"mcp_server_token": "tok", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                mock_app = AsyncMock()
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            with patch("python.helpers.fasta2a_server.PrintStyle"):
                                import python.helpers.fasta2a_server as fas

                                proxy = fas.DynamicA2AProxy()
                                proxy.app = mock_app
                                proxy._startup_done = True

                                body_sent = json.dumps({
                                    "params": {"message": {"parts": [], "metadata": {}}},
                                }).encode("utf-8")
                                first = True

                                async def receive():
                                    nonlocal first
                                    if first:
                                        first = False
                                        return {"type": "http.request", "body": body_sent, "more_body": False}
                                    return {"type": "http.disconnect"}

                                scope = {
                                    "type": "http",
                                    "path": "/t-tok/p-myproject/tasks/send",
                                    "method": "POST",
                                }
                                with patch("python.helpers.settings.get_settings", return_value=cfg):
                                    await proxy(scope, receive, AsyncMock())

                                mock_app.assert_awaited_once()
                                call_scope = mock_app.call_args[0][0]
                                assert call_scope["path"] == "/tasks/send"

    @pytest.mark.asyncio
    async def test_strips_a2a_prefix_from_path(self, mock_settings):
        cfg = {"mcp_server_token": "tok", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                mock_app = AsyncMock()
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = mock_app
                            proxy._startup_done = True

                            scope = {"type": "http", "path": "/a2a/t-tok/foo", "method": "GET"}
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            with patch("python.helpers.settings.get_settings", return_value=cfg):
                                await proxy(scope, receive, AsyncMock())

                            call_scope = mock_app.call_args[0][0]
                            assert call_scope["path"] == "/foo"

    @pytest.mark.asyncio
    async def test_returns_401_when_bearer_auth_invalid(self, mock_settings):
        cfg = {"mcp_server_token": "expected-token", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = MagicMock()
                            proxy._startup_done = True

                            send_calls = []

                            async def send(msg):
                                send_calls.append(msg)

                            scope = {
                                "type": "http",
                                "path": "/",
                                "method": "GET",
                                "headers": [[b"authorization", b"Bearer wrong-token"]],
                                "query_string": b"",
                            }
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            with patch("python.helpers.settings.get_settings", return_value=cfg):
                                await proxy(scope, receive, send)

                            assert any(c.get("status") == 401 for c in send_calls if isinstance(c, dict))

    @pytest.mark.asyncio
    async def test_accepts_bearer_auth(self, mock_settings):
        cfg = {"mcp_server_token": "secret-token", "a2a_server_enabled": True}

        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = cfg
                mock_app = AsyncMock()
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            import python.helpers.fasta2a_server as fas

                            proxy = fas.DynamicA2AProxy()
                            proxy.app = mock_app
                            proxy._startup_done = True

                            scope = {
                                "type": "http",
                                "path": "/",
                                "method": "GET",
                                "headers": [[b"authorization", b"Bearer secret-token"]],
                                "query_string": b"",
                            }
                            receive = AsyncMock(return_value={"type": "http.disconnect"})

                            with patch("python.helpers.settings.get_settings", return_value=cfg):
                                await proxy(scope, receive, AsyncMock())

                            mock_app.assert_awaited_once()


# --- reconfigure ---


class TestDynamicA2AProxyReconfigure:
    def test_reconfigure_sets_token_and_flag(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.settings") as m:
                m.get_settings.return_value = {"mcp_server_token": "", "a2a_server_enabled": True}
                with patch("python.helpers.fasta2a_server.FastA2A"):
                    with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                        with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                            with patch("python.helpers.fasta2a_server.PrintStyle"):
                                import python.helpers.fasta2a_server as fas

                                proxy = fas.DynamicA2AProxy()
                                proxy._startup_done = True
                                proxy.reconfigure("new-token")
                                assert proxy.token == "new-token"
                                assert proxy._reconfigure_needed is True
                                assert proxy._startup_done is False


# --- build_message_history / build_artifacts ---


class TestAgentZeroWorkerBuildMethods:
    def test_build_message_history_returns_empty(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        assert worker.build_message_history([1, 2, 3]) == []

    def test_build_artifacts_returns_empty(self):
        with patch("python.helpers.fasta2a_server.FASTA2A_AVAILABLE", True):
            with patch("python.helpers.fasta2a_server.Worker"):
                with patch("python.helpers.fasta2a_server.InMemoryBroker"):
                    with patch("python.helpers.fasta2a_server.InMemoryStorage"):
                        from python.helpers.fasta2a_server import AgentZeroWorker

                        worker = AgentZeroWorker(broker=MagicMock(), storage=MagicMock())
                        assert worker.build_artifacts([]) == []
