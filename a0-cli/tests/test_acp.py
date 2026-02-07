"""Tests for the ACP protocol adapter."""

import pytest

from a0.acp.server import ACPServer, ACPSession


class TestACPInitialize:
    """Test ACP initialization handshake."""

    @pytest.fixture
    def server(self):
        return ACPServer(agent_url="http://localhost:55080")

    @pytest.mark.asyncio
    async def test_initialize_returns_capabilities(self, server):
        result = await server._handle_initialize(
            {"protocolVersion": 1, "clientCapabilities": {}}
        )
        assert result["protocolVersion"] == 1
        assert "agentCapabilities" in result
        assert result["agentInfo"]["name"] == "agent-zero"

    @pytest.mark.asyncio
    async def test_version_negotiation_higher(self, server):
        result = await server._handle_initialize(
            {"protocolVersion": 99, "clientCapabilities": {}}
        )
        assert result["protocolVersion"] == ACPServer.PROTOCOL_VERSION

    @pytest.mark.asyncio
    async def test_version_negotiation_lower(self, server):
        result = await server._handle_initialize(
            {"protocolVersion": 0, "clientCapabilities": {}}
        )
        assert result["protocolVersion"] == 0


class TestACPSession:
    """Test ACP session model."""

    def test_session_creation(self):
        session = ACPSession(
            session_id="sess_123",
            context_id="ctx_abc",
            cwd="/home/user",
        )
        assert session.session_id == "sess_123"
        assert session.mcp_servers == []

    def test_tool_id_counter(self):
        session = ACPSession(
            session_id="s1", context_id="c1", cwd="."
        )
        assert session.next_tool_id() == "call_0001"
        assert session.next_tool_id() == "call_0002"


class TestPromptConversion:
    """Test ACP content block conversion."""

    @pytest.fixture
    def server(self):
        return ACPServer()

    def test_text_only(self, server):
        blocks = [{"type": "text", "text": "Hello world"}]
        text, attachments = server._convert_prompt(blocks)
        assert text == "Hello world"
        assert attachments == []

    def test_multiple_text(self, server):
        blocks = [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]
        text, _ = server._convert_prompt(blocks)
        assert "Part 1" in text
        assert "Part 2" in text

    def test_resource_text(self, server):
        blocks = [
            {
                "type": "resource",
                "resource": {
                    "uri": "file:///main.py",
                    "text": "print('hi')",
                },
            }
        ]
        text, attachments = server._convert_prompt(blocks)
        assert "main.py" in text
        assert "print('hi')" in text
        assert attachments == []

    def test_resource_blob(self, server):
        blocks = [
            {
                "type": "resource",
                "resource": {
                    "uri": "file:///image.png",
                    "blob": "iVBORw0KGgo=",
                },
            }
        ]
        text, attachments = server._convert_prompt(blocks)
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "image.png"

    def test_image_block(self, server):
        blocks = [{"type": "image", "data": "base64data=="}]
        text, attachments = server._convert_prompt(blocks)
        assert len(attachments) == 1
        assert attachments[0]["base64"] == "base64data=="
