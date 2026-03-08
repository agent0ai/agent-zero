import threading
from collections import deque

from agent import AgentContext, UserMessage


def _make_minimal_context() -> AgentContext:
    ctx = object.__new__(AgentContext)
    ctx.output_data = {}
    ctx.data = {}
    ctx._queue_lock = threading.Lock()
    ctx._message_queue = deque()
    ctx._runtime_state = "idle"
    ctx._dispatch_status = {}
    ctx.paused = False
    ctx.task = None
    return ctx


def test_enqueue_reject_new_when_full():
    ctx = _make_minimal_context()
    accepted1, pos1, depth1 = ctx._enqueue_message(UserMessage("first"), max_depth=1, drop_policy="reject_new")
    accepted2, pos2, depth2 = ctx._enqueue_message(UserMessage("second"), max_depth=1, drop_policy="reject_new")

    assert accepted1 is True
    assert pos1 == 1
    assert depth1 == 1
    assert accepted2 is False
    assert pos2 == 0
    assert depth2 == 1
    assert len(ctx._message_queue) == 1
    assert ctx._message_queue[0].message.message == "first"


def test_enqueue_drop_oldest_when_full():
    ctx = _make_minimal_context()
    ctx._enqueue_message(UserMessage("first"), max_depth=1, drop_policy="drop_oldest")
    accepted2, pos2, depth2 = ctx._enqueue_message(UserMessage("second"), max_depth=1, drop_policy="drop_oldest")

    assert accepted2 is True
    assert pos2 == 1
    assert depth2 == 1
    assert len(ctx._message_queue) == 1
    assert ctx._message_queue[0].message.message == "second"
