import sys
from types import SimpleNamespace
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._chat_compaction.helpers import compactor


class _FakeAgent:
    def read_prompt(self, name: str, **kwargs):
        if name == "compact.sys.md":
            return "system"
        if name == "compact.msg.md":
            return kwargs.get("conversation", "")
        raise AssertionError(f"Unexpected prompt: {name}")


class _FakeLog:
    def __init__(self):
        self.updates = []
        self.streams = []

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def stream(self, **kwargs):
        self.streams.append(kwargs)


class _RecordingModel:
    def __init__(self):
        self.user_messages = []

    async def unified_call(self, system_message, user_message, response_callback=None):
        self.user_messages.append(user_message)
        if response_callback:
            await response_callback("done", "done")
        return f"summary-{len(self.user_messages)}", None


class _CompactionHistory:
    def output(self):
        return [{"ai": False, "content": "hello"}]


class _StructuredCompactionHistory:
    def output(self):
        return [
            {"ai": False, "content": "Inspect the service."},
            {
                "ai": True,
                "content": (
                    '{"thoughts":["Read the credentials"],'
                    '"headline":"Checking service status",'
                    '"tool_name":"code_execution_tool",'
                    '"tool_args":{"code":"print(SECRET_VALUE)"}}'
                ),
            },
        ]


class _CompactionLog:
    def __init__(self):
        self.logs = []
        self.entries = []
        self.reset_called = False
        self.progress = None

    def log(self, **kwargs):
        self.entries.append(kwargs)
        return _FakeLog()

    def reset(self):
        self.reset_called = True

    def set_progress(self, *args, **kwargs):
        self.progress = (args, kwargs)


class _CompactionAgent:
    DATA_NAME_RESPONSES_STATE = "responses_state"

    def __init__(self):
        self.history = _CompactionHistory()
        self.data = {
            "ctx_window": {
                "text": "pre-compaction transcript with secret values",
                "tokens": 42,
            },
            "responses_state": {
                "response_id": "resp_current",
                "previous_response_id": "resp_previous",
                "response_ids": ["resp_previous", "resp_current"],
            }
        }

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value


def test_compaction_prompt_is_resumable_task_state_without_secret_values():
    prompt = (
        PROJECT_ROOT / "plugins" / "_chat_compaction" / "prompts" / "compact.sys.md"
    ).read_text(encoding="utf-8")
    headings = [
        "## Current objective and latest user request",
        "## Authorized scope and prohibited actions",
        "## Decisions and assumptions",
        "## Completed work with evidence",
        "## Modified files and artifacts",
        "## Pending jobs and next executable step",
        "## Blockers and checks not run",
        "## Loaded skill names",
        "## Secret references",
    ]

    positions = [prompt.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "Never include passwords, API keys, tokens, credentials" in prompt
    assert "Preserve only a secret's name, purpose, storage location" in prompt
    assert "Keep exact values: file paths, config values, code identifiers, credentials" not in prompt
    assert "next executable step" in prompt
    assert "job IDs" in prompt


def test_pre_compaction_backup_sanitizes_surrogate_text(tmp_path, monkeypatch):
    monkeypatch.setattr(
        compactor,
        "get_chat_folder_path",
        lambda _ctxid: str(tmp_path),
    )
    monkeypatch.setattr(
        compactor,
        "export_json_chat",
        lambda _context: '{"content":"before\ud83dafter"}',
    )

    paths = compactor._save_pre_compaction_backup(
        SimpleNamespace(id="surrogate-chat"),
        "transcript before\ud83dafter",
    )

    json_backup = Path(paths["json"]).read_text(encoding="utf-8")
    text_backup = Path(paths["txt"]).read_text(encoding="utf-8")

    assert "\ud83d" not in json_backup
    assert "\ud83d" not in text_backup
    assert "before?after" in json_backup
    assert "before?after" in text_backup


def test_compaction_splitter_wraps_single_line_85k_payload(monkeypatch):
    monkeypatch.setattr(
        compactor.tokens, "approximate_tokens", lambda text: len(text or "")
    )

    agent = _FakeAgent()
    chunks = compactor._split_text_for_compaction(
        agent,
        "x" * 85_000,
        token_count=85_000,
        max_input_tokens=10_000,
    )

    assert len(chunks) > 2
    assert all(chunks)
    assert "".join(chunks) == "x" * 85_000
    assert all(
        compactor._compaction_input_tokens(agent, chunk) <= 10_000
        for chunk in chunks
    )


@pytest.mark.asyncio
async def test_large_compaction_does_not_send_unsplit_single_line_payload(monkeypatch):
    monkeypatch.setattr(
        compactor.tokens, "approximate_tokens", lambda text: len(text or "")
    )

    agent = _FakeAgent()
    model = _RecordingModel()

    summary = await compactor._compact_large_history(
        agent,
        "x" * 85_000,
        token_count=85_000,
        max_input_tokens=10_000,
        log_item=_FakeLog(),
        model=model,
    )

    chunk_messages = model.user_messages[:-1]
    assert summary == f"summary-{len(model.user_messages)}"
    assert len(chunk_messages) > 2
    assert all(chunk_messages)
    assert all(len(message) <= 10_000 for message in chunk_messages)


@pytest.mark.asyncio
async def test_manual_compaction_preserves_summary_and_clears_responses_state(
    monkeypatch,
):
    async def fake_single_pass(*args, **kwargs):
        return "summary"

    agent = _CompactionAgent()
    context = SimpleNamespace(
        id="compact-chat",
        agent0=agent,
        log=_CompactionLog(),
        streaming_agent=object(),
    )

    monkeypatch.setattr(
        compactor,
        "_build_model",
        lambda *args: ({"ctx_length": 128000}, _RecordingModel()),
    )
    monkeypatch.setattr(compactor, "_compact_single_pass", fake_single_pass)
    monkeypatch.setattr(
        compactor,
        "_save_pre_compaction_backup",
        lambda *args: {"txt": "/tmp/pre.txt"},
    )
    monkeypatch.setattr(compactor, "save_tmp_chat", lambda *args: None)
    monkeypatch.setattr(compactor, "remove_msg_files", lambda *args: None)
    monkeypatch.setattr(compactor, "mark_dirty_all", lambda *args, **kwargs: None)

    await compactor.run_compaction(context)

    prompt_history = agent.history.current.output_langchain()
    assert len(prompt_history) == 1
    assert isinstance(prompt_history[0], HumanMessage)
    assert "## Context compacted\n\nsummary" in prompt_history[0].content

    state = agent.data["responses_state"]
    assert "response_id" not in state
    assert "previous_response_id" not in state
    assert state["response_ids"] == ["resp_previous", "resp_current"]
    assert "ctx_window" not in agent.data


@pytest.mark.asyncio
async def test_manual_compaction_summarizes_plain_view_but_backs_up_raw_history(
    monkeypatch,
):
    captured = {}

    async def fake_single_pass(_agent, transcript, *_args, **_kwargs):
        captured["summary_transcript"] = transcript
        return "summary"

    def fake_backup(_context, transcript):
        captured["backup_transcript"] = transcript
        return {"txt": "/tmp/pre.txt"}

    agent = _CompactionAgent()
    agent.history = _StructuredCompactionHistory()
    context = SimpleNamespace(
        id="compact-structured-chat",
        agent0=agent,
        log=_CompactionLog(),
        streaming_agent=object(),
    )

    monkeypatch.setattr(
        compactor,
        "_build_model",
        lambda *args: ({"ctx_length": 128000}, _RecordingModel()),
    )
    monkeypatch.setattr(compactor, "_compact_single_pass", fake_single_pass)
    monkeypatch.setattr(compactor, "_save_pre_compaction_backup", fake_backup)
    monkeypatch.setattr(compactor, "save_tmp_chat", lambda *args: None)
    monkeypatch.setattr(compactor, "remove_msg_files", lambda *args: None)
    monkeypatch.setattr(compactor, "mark_dirty_all", lambda *args, **kwargs: None)

    await compactor.run_compaction(context)

    assert captured["summary_transcript"] == (
        "user: Inspect the service.\n"
        "assistant: Checking service status (tool: code_execution_tool)"
    )
    assert "Read the credentials" not in captured["summary_transcript"]
    assert "SECRET_VALUE" not in captured["summary_transcript"]
    assert '"thoughts"' in captured["backup_transcript"]
    assert "SECRET_VALUE" in captured["backup_transcript"]
