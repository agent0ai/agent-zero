import sys
import threading
import types
from pathlib import Path

from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules.setdefault("giturlparse", types.SimpleNamespace(parse=lambda *args, **kwargs: None))
sys.modules.setdefault("whisper", types.SimpleNamespace(load_model=lambda *args, **kwargs: None))

from plugins._model_config.api.model_search import ModelSearch


def _handler():
    return ModelSearch(Flask(__name__), threading.Lock())


def test_model_search_parses_openai_style_data():
    handler = _handler()

    assert handler._parse({"data": [{"id": "gpt-4.1"}, {"id": "gpt-4o-mini"}]}, "openai") == [
        "gpt-4.1",
        "gpt-4o-mini",
    ]


def test_model_search_parses_google_models_and_strips_prefix():
    handler = _handler()

    assert handler._parse({"models": [{"name": "models/gemini-pro"}]}, "google") == ["gemini-pro"]


def test_model_search_parses_ollama_models():
    handler = _handler()

    assert handler._parse({"models": [{"name": "llama3.2"}]}, "ollama") == ["llama3.2"]


def test_model_search_builds_ollama_running_models_url():
    handler = _handler()

    assert handler._ollama_ps_url("http://host.docker.internal:11434/api/tags") == (
        "http://host.docker.internal:11434/api/ps"
    )


def test_model_search_parses_list_style_dicts_and_strings():
    handler = _handler()

    assert handler._parse([{"id": "mistral-large"}, "mistral-small"], "openai") == [
        "mistral-large",
        "mistral-small",
    ]


def test_model_search_resolves_v1_base_without_duplicate_v1():
    handler = _handler()

    url, fmt = handler._resolve_url({"endpoint_url": "/v1/models"}, "http://host.docker.internal:1234/v1")

    assert url == "http://host.docker.internal:1234/v1/models"
    assert fmt == "openai"


def test_model_search_filters_non_chat_models():
    handler = _handler()

    assert handler._filter_models(["gpt-4.1", "text-embedding-3-small", "gpt-image-1"], "chat") == ["gpt-4.1"]


def test_model_search_falls_back_to_litellm_registry(monkeypatch):
    handler = _handler()
    fake_litellm = types.SimpleNamespace(
        models_by_provider={"openai": {"openai/gpt-4.1", "text-embedding-3-small"}}
    )
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    assert set(handler._litellm_fallback("openai", {"litellm_provider": "openai"})) == {"gpt-4.1"}
