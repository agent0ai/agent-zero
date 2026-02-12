import copy
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from python.helpers import codex_exec
from python.helpers import settings as settings_helper


def test_get_chat_model_routes_codex_provider():
    model = models.get_chat_model(
        provider="codex",
        name="gpt-5-codex",
        a0_role="chat",
        a0_context_id="ctx-1",
    )
    assert isinstance(model, models.CodexExecChatWrapper)


@pytest.mark.asyncio
async def test_codex_failure_falls_back_without_mutating_settings(monkeypatch):
    cfg = settings_helper.get_default_settings()
    cfg["chat_model_provider"] = "codex"
    cfg["chat_model_name"] = "gpt-5-codex"
    cfg["chat_model_provider_prev"] = "openai"
    cfg["chat_model_name_prev"] = "gpt-4o-mini"
    cfg["chat_model_api_base_prev"] = "https://api.openai.com/v1"
    cfg["chat_model_kwargs_prev"] = {"temperature": "0"}
    cfg_before = copy.deepcopy(cfg)

    monkeypatch.setattr(settings_helper, "get_settings", lambda: cfg)
    monkeypatch.setattr(
        codex_exec,
        "run_codex_exec",
        lambda *args, **kwargs: codex_exec.CodexExecResult(
            ok=False,
            errors=["codex failed"],
        ),
    )

    class DummyFallbackModel:
        async def unified_call(self, **kwargs):
            return "fallback-response", ""

    original_get_chat_model = models.get_chat_model

    def fake_get_chat_model(provider, name, model_config=None, **kwargs):
        if provider == "codex":
            return original_get_chat_model(
                provider=provider,
                name=name,
                model_config=model_config,
                **kwargs,
            )
        return DummyFallbackModel()

    monkeypatch.setattr(models, "get_chat_model", fake_get_chat_model)

    wrapper = models.CodexExecChatWrapper(
        model="gpt-5-codex",
        provider="codex",
        a0_role="chat",
        a0_context_id="ctx-1",
    )
    response, reasoning = await wrapper.unified_call(user_message="hello")

    assert response == "fallback-response"
    assert reasoning == ""
    assert cfg == cfg_before

    warning = codex_exec.get_latest_warning()
    assert warning is not None
    assert warning.get("fallback_provider") == "openai"


@pytest.mark.asyncio
async def test_codex_failure_without_valid_fallback_raises(monkeypatch):
    cfg = settings_helper.get_default_settings()
    cfg["chat_model_provider"] = "codex"
    cfg["chat_model_name"] = "gpt-5-codex"
    cfg["chat_model_provider_prev"] = "codex"
    cfg["chat_model_name_prev"] = "gpt-5-codex"
    cfg["chat_model_api_base_prev"] = ""
    cfg["chat_model_kwargs_prev"] = {}

    monkeypatch.setattr(settings_helper, "get_settings", lambda: cfg)
    monkeypatch.setattr(
        codex_exec,
        "run_codex_exec",
        lambda *args, **kwargs: codex_exec.CodexExecResult(
            ok=False,
            errors=["codex failed"],
        ),
    )

    wrapper = models.CodexExecChatWrapper(
        model="gpt-5-codex",
        provider="codex",
        a0_role="chat",
        a0_context_id="ctx-2",
    )

    with pytest.raises(RuntimeError):
        await wrapper.unified_call(user_message="hello")
