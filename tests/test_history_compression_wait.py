import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extensions.python.message_loop_prompts_before._90_organize_history_wait import (
    MAX_SYNC_COMPRESSION_PASSES,
    OrganizeHistoryWait,
)


class _StalledHistory:
    def __init__(self):
        self.compress_calls = 0

    def is_over_limit(self):
        return self.compress_calls < 2

    def get_tokens(self):
        return 1234

    async def compress(self):
        self.compress_calls += 1
        return False


class _MaxPassHistory:
    def __init__(self):
        self.compress_calls = 0
        self.tokens = 2000

    def is_over_limit(self):
        return True

    def get_tokens(self):
        return self.tokens

    async def compress(self):
        self.compress_calls += 1
        self.tokens -= 1
        return True


class _FakeLog:
    def __init__(self):
        self.entries = []

    def set_progress(self, *args, **kwargs):
        pass

    def log(self, **kwargs):
        self.entries.append(kwargs)


class _FakeAgent:
    def __init__(self, history=None):
        self.data = {}
        self.history = history or _StalledHistory()
        self.context = type("Context", (), {"log": _FakeLog()})()

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value


@pytest.mark.asyncio
async def test_history_wait_stops_when_compression_makes_no_progress():
    agent = _FakeAgent()

    await OrganizeHistoryWait(agent).execute()

    assert agent.history.compress_calls == 1
    assert agent.context.log.entries
    assert agent.context.log.entries[-1]["heading"] == "History compression stalled"


@pytest.mark.asyncio
async def test_history_wait_stops_after_max_sync_compression_passes():
    history = _MaxPassHistory()
    agent = _FakeAgent(history)

    await OrganizeHistoryWait(agent).execute()

    assert history.compress_calls == MAX_SYNC_COMPRESSION_PASSES
    assert agent.context.log.entries
    assert agent.context.log.entries[-1]["heading"] == "History compression stalled"
    assert (
        f"stopped after {MAX_SYNC_COMPRESSION_PASSES} passes"
        in agent.context.log.entries[-1]["content"]
    )
