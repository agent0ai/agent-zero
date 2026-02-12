import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import codex_exec


def test_base_cmd_contains_required_flags():
    cmd = codex_exec._base_cmd("gpt-5-codex")
    joined = " ".join(cmd)
    assert "exec" in cmd
    assert "--json" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert '-c model_reasoning_effort="high"' in joined
    assert "-c mcp_servers={}" in joined
    assert "-m gpt-5-codex" in joined


def test_run_codex_exec_parses_thread_message_and_reasoning(monkeypatch):
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"thread-1"}',
            '{"type":"item.completed","item":{"type":"reasoning","text":"Thinking..."}}',
            '{"type":"item.completed","item":{"type":"agent_message","text":"HELLO"}}',
            '{"type":"turn.completed","usage":{"output_tokens":5}}',
        ]
    )

    def _fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(codex_exec.subprocess, "run", _fake_run)
    result = codex_exec.run_codex_exec("Reply with HELLO", model="gpt-5-codex")

    assert result.ok is True
    assert result.thread_id == "thread-1"
    assert result.message == "HELLO"
    assert result.reasoning == "Thinking..."
    assert result.errors == []


def test_run_codex_exec_collects_failures(monkeypatch):
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"thread-2"}',
            '{"type":"error","message":"Re-connecting... 1/5"}',
            '{"type":"turn.failed","error":{"message":"model not found"}}',
        ]
    )

    def _fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(codex_exec.subprocess, "run", _fake_run)
    result = codex_exec.run_codex_exec("hello")

    assert result.ok is False
    assert result.thread_id == "thread-2"
    assert "model not found" in result.diagnostic


def test_run_codex_exec_resume_uses_stdin_prompt(monkeypatch):
    captured = {}

    def _fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return SimpleNamespace(returncode=0, stdout='{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}', stderr="")

    monkeypatch.setattr(codex_exec.subprocess, "run", _fake_run)
    result = codex_exec.run_codex_exec(
        "resume-prompt",
        model="gpt-5-codex",
        resume_thread_id="thread-123",
    )

    assert result.ok is True
    assert captured["input"] == "resume-prompt"
    assert "resume" in captured["cmd"]
    assert "thread-123" in captured["cmd"]
    assert "resume-prompt" not in captured["cmd"]


def test_get_codex_status_parses_chatgpt_login(monkeypatch):
    monkeypatch.setattr(codex_exec.shutil, "which", lambda _bin: "/usr/local/bin/codex")

    def _fake_run(cmd, *args, **kwargs):
        if "--version" in cmd:
            return SimpleNamespace(returncode=0, stdout="codex-cli 0.53.0\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Logged in using ChatGPT\n", stderr="")

    monkeypatch.setattr(codex_exec.subprocess, "run", _fake_run)
    status = codex_exec.get_codex_status()

    assert status["installed"] is True
    assert status["version"] == "codex-cli 0.53.0"
    assert status["logged_in"] is True
    assert status["auth_mode"] == "chatgpt"
    assert status["diagnostic"] == ""


def test_get_cached_codex_models_defaults():
    payload = codex_exec.get_cached_codex_models()
    assert "models" in payload
    assert isinstance(payload["models"], list)
    assert any(item.get("value") == "gpt-5-codex" for item in payload["models"])


def test_get_codex_models_without_login(monkeypatch):
    monkeypatch.setattr(
        codex_exec,
        "get_codex_status",
        lambda: {
            "installed": True,
            "version": "codex-cli test",
            "logged_in": False,
            "auth_mode": "none",
            "diagnostic": "not logged in",
        },
    )
    payload = codex_exec.get_codex_models(force_refresh=True)
    assert payload["verified"] is False
    assert "Log in to ChatGPT subscription" in payload["diagnostic"]
