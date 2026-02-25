
import pytest
from agents.agent import Agent
from python.helpers import history

class MockMessage:
    def __init__(self, ai, content):
        self.ai = ai
        self.content = content

    def output(self):
        return [{"ai": self.ai, "content": self.content}]

class MockTopic:
    def __init__(self, messages):
        self.messages = messages

    def output(self):
        result = []
        for m in self.messages:
            result.extend(m.output())
        return result

class MockHistory:
    def __init__(self):
        self.topics = []
        self.current = MockTopic([])
        self.bulks = []

    def output(self):
        result = []
        for b in self.bulks:
            result.extend(b.output())
        for t in self.topics:
            result.extend(t.output())
        result.extend(self.current.output())
        return result

    def output_text(self, human_label="user", ai_label="ai"):
        return history.output_text(self.output(), ai_label, human_label)

# Standalone MockAgent that DOES NOT inherit from Agent to avoid init issues
class MockAgent:
    def __init__(self, history_mock):
        self.history = history_mock

    # Attach the real method to this class
    concat_messages = Agent.concat_messages

@pytest.fixture
def mock_history():
    hist = MockHistory()
    # Topic 0
    t1 = MockTopic([
        MockMessage(False, "User 1"),
        MockMessage(True, "AI 1")
    ])
    # Topic 1
    t2 = MockTopic([
        MockMessage(False, "User 2"),
        MockMessage(True, "AI 2")
    ])
    # Current Topic (index -1 or 2)
    curr = MockTopic([
        MockMessage(False, "User Current"),
        MockMessage(True, "AI Current")
    ])

    hist.topics = [t1, t2]
    hist.current = curr
    return hist

@pytest.fixture
def agent(mock_history):
    return MockAgent(mock_history)

def test_concat_messages_no_args_uses_history(agent, mock_history):
    # Should output all messages
    result = agent.concat_messages(None)
    assert "User 1" in result
    assert "AI 1" in result
    assert "User 2" in result
    assert "AI 2" in result
    assert "User Current" in result
    assert "AI Current" in result

def test_concat_messages_with_list(agent):
    msgs = [{"ai": False, "content": "List User"}, {"ai": True, "content": "List AI"}]
    result = agent.concat_messages(msgs)
    assert "List User" in result
    assert "List AI" in result
    assert "User 1" not in result

def test_concat_messages_with_object(agent):
    class MockObj:
        def output_text(self, human_label, ai_label):
            return "Mock Output"

    result = agent.concat_messages(MockObj())
    assert result == "Mock Output"

def test_concat_messages_limit(agent):
    # Start index 0, limit 2 -> First 2 messages
    result = agent.concat_messages(None, limit=2)
    assert "User 1" in result
    assert "AI 1" in result
    assert "User 2" not in result

    # Last 2 messages: start_index=-2
    result_last = agent.concat_messages(None, start_index=-2)
    assert "User Current" in result_last
    assert "AI Current" in result_last
    assert "AI 2" not in result_last

def test_concat_messages_topic_index(agent):
    # Topic 0
    result = agent.concat_messages(None, topic_index=0)
    assert "User 1" in result
    assert "AI 1" in result
    assert "User 2" not in result

    # Topic 1
    result = agent.concat_messages(None, topic_index=1)
    assert "User 2" in result
    assert "AI 2" in result
    assert "User 1" not in result

    # Topic -1 (Current)
    result = agent.concat_messages(None, topic_index=-1)
    assert "User Current" in result
    assert "AI Current" in result

def test_concat_messages_start_index(agent):
    # Skip first 4 messages (User1, AI1, User2, AI2) -> expect User Current, AI Current
    # Total messages: 6.
    result = agent.concat_messages(None, start_index=4)
    assert "User Current" in result
    assert "AI Current" in result
    assert "User 2" not in result

def test_concat_messages_topic_index_out_of_bounds(agent):
    result = agent.concat_messages(None, topic_index=99)
    assert result == "" # Empty string result

def test_fallback_empty(agent):
    # Pass object with no output methods
    class Empty: pass
    result = agent.concat_messages(Empty())
    assert result == ""

def test_concat_messages_negative_start_with_limit(agent):
    # This is the problematic case: start_index=-2, limit=2
    # Should give the last 2 messages: "User Current", "AI Current"
    result = agent.concat_messages(None, start_index=-2, limit=2)

    # Assert we got the expected content
    assert "User Current" in result
    assert "AI Current" in result
    # Assert we did NOT get older messages (just to be safe)
    assert "User 2" not in result
    assert "AI 2" not in result

def test_concat_messages_negative_start_exceeds_length(agent):
    # Start index -10 (exceeds length 6), limit 10
    # Should give all 6 messages.
    result = agent.concat_messages(None, start_index=-10, limit=10)

    assert "User 1" in result
    assert "AI 1" in result
    assert "User 2" in result
    assert "AI 2" in result
    assert "User Current" in result
    assert "AI Current" in result
