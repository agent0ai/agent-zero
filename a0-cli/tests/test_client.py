"""Tests for the Agent Zero client library."""

from a0.client.api import (
    AgentZeroClient,
    Attachment,
    LogData,
    LogItem,
    LogResponse,
    MessageResponse,
)
from a0.client.poller import Poller, PollEvent, PollState


class TestModels:
    """Test Pydantic model validation."""

    def test_message_response(self):
        r = MessageResponse(context_id="ctx_123", response="Hello!")
        assert r.context_id == "ctx_123"
        assert r.response == "Hello!"

    def test_log_item_defaults(self):
        log = LogItem(no=0, type="agent")
        assert log.heading == ""
        assert log.content == ""
        assert log.kvps == {}
        assert log.agentno == 0

    def test_log_item_full(self):
        log = LogItem(
            no=1,
            id="log_001",
            type="tool",
            heading="Running code",
            content="print('hello')",
            kvps={"tool_name": "code_execution", "runtime": "python"},
            timestamp=1700000000.0,
            agentno=0,
        )
        assert log.kvps["tool_name"] == "code_execution"

    def test_log_response(self):
        r = LogResponse(
            context_id="ctx_1",
            log=LogData(guid="g1", total_items=5, returned_items=5, items=[]),
        )
        assert r.log.guid == "g1"
        assert r.log.total_items == 5

    def test_log_data_defaults(self):
        d = LogData()
        assert d.items == []
        assert d.progress_active is False

    def test_attachment(self):
        a = Attachment(filename="test.txt", base64="dGVzdA==")
        assert a.filename == "test.txt"


class TestPollState:
    """Test poll state tracking."""

    def test_initial_state(self):
        state = PollState(context_id="ctx_1")
        assert state.last_total == 0
        assert state.log_guid == ""

    def test_poll_event_defaults(self):
        event = PollEvent()
        assert event.logs == []
        assert event.context_reset is False


class TestClientInit:
    """Test client initialization."""

    def test_default_url(self):
        client = AgentZeroClient()
        assert client.base_url == "http://localhost:55080"

    def test_custom_url(self):
        client = AgentZeroClient(base_url="http://example.com:9090/")
        assert client.base_url == "http://example.com:9090"

    def test_headers_without_api_key(self):
        client = AgentZeroClient()
        headers = client._headers()
        assert "X-API-KEY" not in headers

    def test_headers_with_api_key(self):
        client = AgentZeroClient(api_key="test-key-123")
        headers = client._headers()
        assert headers["X-API-KEY"] == "test-key-123"
