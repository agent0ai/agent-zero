import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import settings as settings_helper


def test_switching_to_codex_preserves_previous_snapshot():
    cfg = settings_helper.get_default_settings()

    cfg["chat_model_provider"] = "openai"
    cfg["chat_model_name"] = "gpt-4o-mini"
    cfg["chat_model_api_base"] = "https://api.openai.com/v1"
    cfg["chat_model_kwargs"] = {"temperature": "0.2"}
    settings_helper._sync_previous_model_snapshots(cfg)

    assert cfg["chat_model_provider_prev"] == "openai"
    assert cfg["chat_model_name_prev"] == "gpt-4o-mini"

    cfg["chat_model_provider"] = "codex"
    cfg["chat_model_name"] = "gpt-5-codex"
    cfg["chat_model_api_base"] = ""
    cfg["chat_model_kwargs"] = {"temperature": "0"}
    settings_helper._sync_previous_model_snapshots(cfg)

    assert cfg["chat_model_provider_prev"] == "openai"
    assert cfg["chat_model_name_prev"] == "gpt-4o-mini"
    assert cfg["chat_model_api_base_prev"] == "https://api.openai.com/v1"


def test_non_codex_updates_previous_snapshot():
    cfg = settings_helper.get_default_settings()

    cfg["util_model_provider"] = "openrouter"
    cfg["util_model_name"] = "google/gemini-2.0-flash-001"
    cfg["util_model_kwargs"] = {"temperature": "0.1"}
    settings_helper._sync_previous_model_snapshots(cfg)
    assert cfg["util_model_provider_prev"] == "openrouter"

    cfg["util_model_provider"] = "anthropic"
    cfg["util_model_name"] = "claude-3-5-sonnet"
    cfg["util_model_api_base"] = ""
    cfg["util_model_kwargs"] = {"temperature": "0"}
    settings_helper._sync_previous_model_snapshots(cfg)

    assert cfg["util_model_provider_prev"] == "anthropic"
    assert cfg["util_model_name_prev"] == "claude-3-5-sonnet"


def test_embedding_model_not_part_of_codex_snapshot_logic():
    cfg = settings_helper.get_default_settings()
    settings_helper._sync_previous_model_snapshots(cfg)

    assert "embed_model_provider_prev" not in cfg
    assert "embed_model_name_prev" not in cfg
