from __future__ import annotations

from python.helpers import startup_selector


def _base_settings() -> dict:
    return {
        "chat_execution_backend": "native",
        "chat_model_provider": "ollama",
        "chat_model_name": "qwen2.5-coder:3b",
        "chat_model_api_base": "http://localhost:11434",
        "util_model_api_base": "http://localhost:11434",
        "browser_model_api_base": "http://localhost:11434",
        "agent_profile": "agent0",
        "startup_auto_select_enabled": True,
        "startup_selection_goal": "reliability",
        "startup_context_priority": "project",
        "startup_fallback_policy": "chain",
        "startup_fallback_chain": ["claude_local", "codex_local", "native_local", "native_gemini"],
        "startup_active_project": "",
    }


def test_startup_selector_falls_back_to_next_ready_candidate(monkeypatch):
    startup_selector.reset_startup_selection_state()
    settings = _base_settings()
    settings["chat_execution_backend"] = "claude_code"

    monkeypatch.setattr(startup_selector, "_resolve_external_executable", lambda backend: "")
    monkeypatch.setattr(startup_selector, "_ollama_reachable", lambda _api_base: (True, "ok"))
    monkeypatch.setattr(startup_selector.models, "get_api_key", lambda _provider: "")

    selected = startup_selector.apply_startup_selection(settings)
    assert selected["chat_execution_backend"] == "native"
    assert selected["chat_model_provider"] == "ollama"

    decision = startup_selector.get_startup_selection_state()
    assert decision["status"] == "selected"
    assert decision["selected"]["backend"] == "native"


def test_startup_selector_applies_project_context_override(monkeypatch):
    startup_selector.reset_startup_selection_state()
    settings = _base_settings()
    settings["startup_active_project"] = "demo_project"

    monkeypatch.setattr(
        startup_selector,
        "_load_project_startup_overrides",
        lambda _project: {
            "chat_execution_backend": "codex",
            "chat_model_provider": "ollama",
            "chat_model_name": "qwen2.5-coder:3b",
            "agent_profile": "developer",
        },
    )
    monkeypatch.setattr(
        startup_selector,
        "_resolve_external_executable",
        lambda backend: "/usr/bin/codex" if backend == "codex" else "",
    )
    monkeypatch.setattr(startup_selector, "_ollama_reachable", lambda _api_base: (True, "ok"))
    monkeypatch.setattr(startup_selector.models, "get_api_key", lambda _provider: "")

    selected = startup_selector.apply_startup_selection(settings)
    assert selected["chat_execution_backend"] == "codex"
    assert selected["agent_profile"] == "developer"

    decision = startup_selector.get_startup_selection_state()
    assert decision["source"] == "project"


def test_startup_selector_hard_fail_keeps_existing_when_not_ready(monkeypatch):
    startup_selector.reset_startup_selection_state()
    settings = _base_settings()
    settings["chat_execution_backend"] = "claude_code"
    settings["startup_fallback_policy"] = "hard_fail"

    monkeypatch.setattr(startup_selector, "_resolve_external_executable", lambda _backend: "")
    monkeypatch.setattr(startup_selector, "_ollama_reachable", lambda _api_base: (True, "ok"))
    monkeypatch.setattr(startup_selector.models, "get_api_key", lambda _provider: "")

    selected = startup_selector.apply_startup_selection(settings)
    assert selected["chat_execution_backend"] == "claude_code"

    decision = startup_selector.get_startup_selection_state()
    assert decision["status"] == "failed"


def test_startup_selector_avoids_invalid_cloud_key_by_selecting_local(monkeypatch):
    startup_selector.reset_startup_selection_state()
    settings = _base_settings()
    settings["chat_model_provider"] = "google"
    settings["chat_model_name"] = "gemini-2.0-flash"
    settings["chat_model_api_base"] = ""
    settings["startup_fallback_chain"] = ["native_local"]

    monkeypatch.setattr(startup_selector, "_resolve_external_executable", lambda _backend: "")
    monkeypatch.setattr(startup_selector, "_ollama_reachable", lambda _api_base: (True, "ok"))
    monkeypatch.setattr(startup_selector.models, "get_api_key", lambda _provider: "")

    selected = startup_selector.apply_startup_selection(settings)
    assert selected["chat_model_provider"] == "ollama"
    assert selected["chat_model_name"] == "qwen2.5-coder:3b"
