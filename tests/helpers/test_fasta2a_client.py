#!/usr/bin/env python3
"""
Unit tests for python/helpers/fasta2a_client.py and FastA2A agent card testing utility.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncio
import pytest
from python.helpers import settings


# --- Unit tests for fasta2a_client module ---

def test_is_client_available():
    """is_client_available returns module's FASTA2A_CLIENT_AVAILABLE."""
    from python.helpers.fasta2a_client import is_client_available, FASTA2A_CLIENT_AVAILABLE
    assert is_client_available() is FASTA2A_CLIENT_AVAILABLE


@pytest.mark.skipif(
    not getattr(__import__("python.helpers.fasta2a_client", fromlist=["FASTA2A_CLIENT_AVAILABLE"]), "FASTA2A_CLIENT_AVAILABLE"),
    reason="FastA2A client not installed",
)
class TestAgentConnectionWhenAvailable:
    """Tests for AgentConnection when FastA2A is available."""

    @pytest.fixture
    def mock_http_client(self):
        client = MagicMock()
        client.get = AsyncMock()
        client.aclose = AsyncMock()
        return client

    @pytest.fixture
    def mock_a2a_client(self):
        client = MagicMock()
        client.send_message = AsyncMock(return_value={"result": {"context_id": "ctx-123"}})
        client.get_task = AsyncMock(return_value={
            "result": {"status": {"state": "completed"}}
        })
        return client

    def test_init_adds_http_scheme_when_missing(self):
        from python.helpers.fasta2a_client import AgentConnection
        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient"):
            mock_httpx.AsyncClient.return_value = MagicMock()
            conn = AgentConnection("agent.example.com", timeout=10)
        assert conn.agent_url == "http://agent.example.com"

    def test_init_preserves_https(self):
        from python.helpers.fasta2a_client import AgentConnection
        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient"):
            mock_httpx.AsyncClient.return_value = MagicMock()
            conn = AgentConnection("https://agent.example.com")
        assert conn.agent_url == "https://agent.example.com"

    def test_init_strips_trailing_slash(self):
        from python.helpers.fasta2a_client import AgentConnection
        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient"):
            mock_httpx.AsyncClient.return_value = MagicMock()
            conn = AgentConnection("http://agent.example.com/")
        assert conn.agent_url == "http://agent.example.com"

    def test_init_uses_token_when_provided(self):
        from python.helpers.fasta2a_client import AgentConnection
        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient"):
            mock_httpx.AsyncClient.return_value = MagicMock()
            conn = AgentConnection("http://agent.example.com", token="secret-token")
        mock_httpx.AsyncClient.assert_called_once()
        call_kwargs = mock_httpx.AsyncClient.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert "Bearer secret-token" in call_kwargs["headers"]["Authorization"]
        assert call_kwargs["headers"]["X-API-KEY"] == "secret-token"

    @pytest.mark.asyncio
    async def test_get_agent_card_success(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent", "description": "A test"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            card = await conn.get_agent_card()

        assert card["name"] == "TestAgent"
        assert card["description"] == "A test"
        mock_http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_card_tries_fallback_when_a2a_in_url(self, mock_http_client, mock_a2a_client):
        """When main URL fails and URL contains /a2a, a second request to root URL is attempted."""
        from python.helpers.fasta2a_client import AgentConnection

        mock_http_client.get.side_effect = Exception("first fail")

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com/a2a")
            with pytest.raises(RuntimeError, match="Could not retrieve agent card"):
                await conn.get_agent_card()

        assert mock_http_client.get.call_count == 2
        second_call_url = str(mock_http_client.get.call_args_list[1])
        assert "http://agent.example.com" in second_call_url
        assert "/a2a" not in second_call_url

    @pytest.mark.asyncio
    async def test_get_agent_card_raises_on_failure(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_http_client.get.side_effect = Exception("Connection refused")

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            with pytest.raises(RuntimeError, match="Could not retrieve agent card"):
                await conn.get_agent_card()

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp

        mock_a2a_client.send_message.return_value = {
            "result": {"context_id": "ctx-456", "output": "Hello"}
        }

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            result = await conn.send_message("Hello")

        assert result["result"]["output"] == "Hello"
        assert conn._context_id == "ctx-456"
        mock_a2a_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_attachments(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp
        mock_a2a_client.send_message.return_value = {"result": {}}

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            await conn.send_message("Hi", attachments=["file:///path/to/doc.pdf"])

        call_args = mock_a2a_client.send_message.call_args
        parts = call_args[1]["message"]["parts"]
        assert len(parts) == 2
        assert parts[0]["kind"] == "text"
        assert parts[1]["kind"] == "file"
        assert parts[1]["file"]["uri"] == "file:///path/to/doc.pdf"

    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp
        mock_a2a_client.get_task = AsyncMock(return_value={"result": {"status": "running"}})

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            result = await conn.get_task("task-123")

        assert result["result"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_task_raises_on_failure(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp
        mock_a2a_client.get_task = AsyncMock(side_effect=Exception("Task not found"))

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            with pytest.raises(RuntimeError, match="Failed to get task"):
                await conn.get_task("task-123")

    @pytest.mark.asyncio
    async def test_wait_for_completion_returns_when_completed(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp
        mock_a2a_client.get_task = AsyncMock(return_value={
            "result": {"status": {"state": "completed"}, "output": "done"}
        })

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            result = await conn.wait_for_completion("task-1", poll_interval=1, max_wait=5)

        assert result["result"]["status"]["state"] == "completed"

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp
        mock_a2a_client.get_task = AsyncMock(return_value={
            "result": {"status": {"state": "running"}}
        })

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            with pytest.raises(TimeoutError, match="did not complete"):
                await conn.wait_for_completion("task-1", poll_interval=1, max_wait=2)

    @pytest.mark.asyncio
    async def test_close_calls_aclose(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            conn = AgentConnection("http://agent.example.com")
            await conn.close()

        mock_http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_http_client, mock_a2a_client):
        from python.helpers.fasta2a_client import AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_resp

        with patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient") as mock_a2a_cls:
            mock_httpx.AsyncClient.return_value = mock_http_client
            mock_a2a_cls.return_value = mock_a2a_client
            async with AgentConnection("http://agent.example.com") as conn:
                assert conn.agent_url == "http://agent.example.com"

        mock_http_client.aclose.assert_called_once()


@pytest.mark.skipif(
    not getattr(__import__("python.helpers.fasta2a_client", fromlist=["FASTA2A_CLIENT_AVAILABLE"]), "FASTA2A_CLIENT_AVAILABLE"),
    reason="FastA2A client not installed",
)
class TestConnectToAgent:
    @pytest.mark.asyncio
    async def test_connect_to_agent_returns_connection(self):
        from python.helpers.fasta2a_client import connect_to_agent, AgentConnection

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "TestAgent"}
        mock_resp.raise_for_status = MagicMock()

        with patch("python.helpers.fasta2a_client.AgentConnection") as mock_cls, \
             patch("python.helpers.fasta2a_client.httpx") as mock_httpx, \
             patch("python.helpers.fasta2a_client.A2AClient"):
            mock_conn = MagicMock()
            mock_conn.get_agent_card = AsyncMock()
            mock_conn.agent_url = "http://agent.example.com"
            mock_cls.return_value = mock_conn
            conn = await connect_to_agent("http://agent.example.com")
        assert conn.agent_url == "http://agent.example.com"
        mock_conn.get_agent_card.assert_called_once()


class TestAgentConnectionWhenUnavailable:
    """Tests when FastA2A is not available."""

    def test_init_raises_when_unavailable(self):
        from python.helpers import fasta2a_client
        orig = fasta2a_client.FASTA2A_CLIENT_AVAILABLE
        try:
            fasta2a_client.FASTA2A_CLIENT_AVAILABLE = False
            with pytest.raises(RuntimeError, match="FastA2A client not available"):
                fasta2a_client.AgentConnection("http://agent.example.com")
        finally:
            fasta2a_client.FASTA2A_CLIENT_AVAILABLE = orig


# --- FastA2A agent card testing utility ---

def get_test_urls():
    """Get the URLs to test based on current settings."""
    try:
        cfg = settings.get_settings()
        token = cfg.get("mcp_server_token", "")

        if not token:
            print("❌ No mcp_server_token found in settings")
            return None

        base_url = "http://localhost:50101"

        urls = {
            "token_based": f"{base_url}/a2a/t-{token}/.well-known/agent.json",
            "bearer_auth": f"{base_url}/a2a/.well-known/agent.json",
            "api_key_header": f"{base_url}/a2a/.well-known/agent.json",
            "api_key_query": f"{base_url}/a2a/.well-known/agent.json?api_key={token}"
        }

        return {"token": token, "urls": urls}

    except Exception as e:
        print(f"❌ Error getting settings: {e}")
        return None


def print_test_commands():
    """Print curl commands to test FastA2A authentication."""
    data = get_test_urls()
    if not data:
        return

    token = data["token"]
    urls = data["urls"]

    print("🚀 FastA2A Agent Card Testing Commands")
    print("=" * 60)
    print(f"Current token: {token}")
    print()

    print("1️⃣  Token-based URL (recommended):")
    print(f"   curl -v '{urls['token_based']}'")
    print()

    print("2️⃣  Bearer authentication:")
    print(f"   curl -v -H 'Authorization: Bearer {token}' '{urls['bearer_auth']}'")
    print()

    print("3️⃣  API key header:")
    print(f"   curl -v -H 'X-API-KEY: {token}' '{urls['api_key_header']}'")
    print()

    print("4️⃣  API key query parameter:")
    print(f"   curl -v '{urls['api_key_query']}'")
    print()

    print("Expected response (if working):")
    print("   HTTP/1.1 200 OK")
    print("   Content-Type: application/json")
    print("   {")
    print('     "name": "Agent Zero",')
    print('     "version": "1.0.0",')
    print('     "skills": [...]')
    print("   }")
    print()

    print("Expected error (if auth fails):")
    print("   HTTP/1.1 401 Unauthorized")
    print("   Unauthorized")
    print()


def print_troubleshooting():
    """Print troubleshooting information."""
    print("🔧 Troubleshooting FastA2A Issues")
    print("=" * 40)
    print()
    print("1. Server not running:")
    print("   - Make sure Agent Zero is running: python run_ui.py")
    print("   - Check the correct port (default: 50101)")
    print()

    print("2. Authentication failures:")
    print("   - Verify token matches in settings")
    print("   - Check token format (should be 16 characters)")
    print("   - Try different auth methods")
    print()

    print("3. FastA2A not available:")
    print("   - Install FastA2A: pip install fasta2a")
    print("   - Check server logs for FastA2A configuration errors")
    print()

    print("4. Routing issues:")
    print("   - Verify /a2a prefix is working")
    print("   - Check DispatcherMiddleware configuration")
    print("   - Look for FastA2A startup messages in logs")
    print()


def validate_token_format():
    """Validate that the token format is correct."""
    try:
        cfg = settings.get_settings()
        token = cfg.get("mcp_server_token", "")

        print("🔍 Token Validation")
        print("=" * 25)

        if not token:
            print("❌ No token found")
            return False

        print(f"✅ Token found: {token}")
        print(f"✅ Token length: {len(token)} characters")

        if len(token) != 16:
            print("⚠️  Warning: Expected token length is 16 characters")

        # Check token characters
        if token.isalnum():
            print("✅ Token contains only alphanumeric characters")
        else:
            print("⚠️  Warning: Token contains non-alphanumeric characters")

        return True

    except Exception as e:
        print(f"❌ Error validating token: {e}")
        return False


@pytest.mark.asyncio
async def test_server_connectivity():
    """Test basic server connectivity."""
    try:
        import httpx

        print("🌐 Server Connectivity Test")
        print("=" * 30)

        async with httpx.AsyncClient() as client:
            try:
                # Test basic server
                await client.get("http://localhost:50101/", timeout=5.0)
                print("✅ Agent Zero server is running")
                return True
            except httpx.ConnectError:
                print("❌ Cannot connect to Agent Zero server")
                print("   Make sure the server is running: python run_ui.py")
                return False
            except Exception as e:
                print(f"❌ Server connectivity error: {e}")
                return False

    except ImportError:
        print("ℹ️  httpx not available, skipping connectivity test")
        print("   Install with: pip install httpx")
        return None


def main():
    """Main test function."""
    print("🧪 FastA2A Agent Card Testing Utility")
    print("=" * 45)
    print()

    # Validate token
    if not validate_token_format():
        print()
        print_troubleshooting()
        return 1

    print()

    # Test connectivity if possible
    try:
        connectivity = asyncio.run(test_server_connectivity())
        print()

        if connectivity is False:
            print_troubleshooting()
            return 1

    except Exception as e:
        print(f"Error testing connectivity: {e}")
        print()

    # Print test commands
    print_test_commands()

    print("📋 Next Steps:")
    print("1. Start Agent Zero server if not running")
    print("2. Run one of the curl commands above")
    print("3. Check for successful 200 response with agent card JSON")
    print("4. If issues occur, see troubleshooting section")

    return 0


if __name__ == "__main__":
    sys.exit(main())
