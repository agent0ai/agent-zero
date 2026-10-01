import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helpers import state_monitor_integration
from helpers.persist_chat import _collect_response_ids
from plugins._chat_branching.api import branch_chat


@pytest.mark.asyncio
async def test_branch_rebuilds_provider_and_context_state_from_trimmed_history(
    monkeypatch,
):
    history = json.dumps(
        {
            "_cls": "History",
            "counter": 2,
            "bulks": [],
            "topics": [],
            "current": {
                "summary": "",
                "messages": [
                    {
                        "id": "kept-message",
                        "content": "before",
                        "metadata": {
                            "responses": {
                                "response_id": "resp_kept",
                                "previous_response_id": "resp_previous",
                                "output_items": [{"type": "message"}],
                            }
                        },
                    },
                    {"id": "removed-message", "content": "after"},
                ],
            },
        }
    )
    serialized = {
        "id": "source-chat",
        "name": "Source chat",
        "log": {
            "logs": [
                {"no": 4, "id": "kept-message"},
                {"no": 5, "id": "removed-message"},
            ]
        },
        "agents": [
            {
                "history": history,
                "data": {
                    "responses_state": {
                        "response_id": "resp_current",
                        "response_ids": ["resp_kept", "resp_current"],
                    },
                    "ctx_window": {"text": "source context"},
                },
            }
            for _ in range(2)
        ],
    }

    branched = []

    monkeypatch.setattr(
        branch_chat.AgentContext,
        "get",
        lambda context_id: object() if context_id == "source-chat" else None,
    )
    monkeypatch.setattr(
        branch_chat,
        "_serialize_context",
        lambda _context: copy.deepcopy(serialized),
    )

    def deserialize(data):
        branched.append(copy.deepcopy(data))
        return SimpleNamespace(id="branch-chat")

    monkeypatch.setattr(branch_chat, "_deserialize_context", deserialize)
    monkeypatch.setattr(branch_chat, "save_tmp_chat", lambda _context: None)
    monkeypatch.setattr(
        state_monitor_integration,
        "mark_dirty_all",
        lambda **_kwargs: None,
    )

    result = await branch_chat.BranchChat.process(
        None,
        {"context": "source-chat", "log_no": 4},
        None,
    )

    assert result["ctxid"] == "branch-chat"
    assert len(branched) == 1
    assert _collect_response_ids(branched[0]) == []
    for agent_data in branched[0]["agents"]:
        assert "ctx_window" not in agent_data["data"]
        assert "responses_state" not in agent_data["data"]
        trimmed = json.loads(agent_data["history"])
        messages = trimmed["current"]["messages"]
        assert [message["id"] for message in messages] == ["kept-message"]
        responses = messages[0]["metadata"]["responses"]
        assert "response_id" not in responses
        assert "previous_response_id" not in responses
        assert responses["output_items"] == [{"type": "message"}]

    assert serialized["agents"][0]["data"]["responses_state"]["response_id"] == (
        "resp_current"
    )
    original_message = json.loads(serialized["agents"][0]["history"])["current"][
        "messages"
    ][0]
    assert original_message["metadata"]["responses"]["response_id"] == "resp_kept"
