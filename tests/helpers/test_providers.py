"""Tests for python/helpers/providers.py — ProviderManager, get_providers, get_provider_config."""

import sys
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def reset_provider_manager():
    """Reset ProviderManager singleton between tests."""
    from python.helpers.providers import ProviderManager
    ProviderManager._instance = None
    ProviderManager._raw = None
    ProviderManager._options = None
    yield


class TestProviderManager:
    def test_get_instance_returns_singleton(self):
        from python.helpers.providers import ProviderManager
        a = ProviderManager.get_instance()
        b = ProviderManager.get_instance()
        assert a is b

    def test_loads_yaml_mapping_format(self):
        yaml_content = """
chat:
  openai:
    name: OpenAI
    id: openai
  anthropic:
    name: Anthropic
embedding:
  openai:
    name: OpenAI Embeddings
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import ProviderManager
                pm = ProviderManager.get_instance()
        chat = pm.get_providers("chat")
        assert len(chat) >= 2
        ids = [p["value"] for p in chat]
        assert "openai" in ids
        assert "anthropic" in ids

    def test_loads_yaml_list_format(self):
        yaml_content = """
chat:
  - id: openai
    name: OpenAI
embedding: []
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import ProviderManager
                pm = ProviderManager.get_instance()
        chat = pm.get_providers("chat")
        assert len(chat) >= 1
        assert any(p["value"] == "openai" for p in chat)

    def test_get_providers_returns_empty_for_unknown_type(self):
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import ProviderManager
                pm = ProviderManager.get_instance()
        assert pm.get_providers("unknown") == []

    def test_get_provider_config_case_insensitive(self):
        yaml_content = """
chat:
  openai:
    name: OpenAI
    api_key_env: OPENAI_API_KEY
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import ProviderManager
                pm = ProviderManager.get_instance()
        cfg = pm.get_provider_config("chat", "OPENAI")
        assert cfg is not None
        assert cfg.get("name") == "OpenAI"

    def test_get_provider_config_returns_none_for_unknown(self):
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import ProviderManager
                pm = ProviderManager.get_instance()
        assert pm.get_provider_config("chat", "nonexistent") is None


class TestConvenienceFunctions:
    def test_get_providers_returns_list(self):
        with patch("builtins.open", mock_open(read_data="chat:\n  x: {id: x, name: X}")):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import get_providers
                result = get_providers("chat")
        assert isinstance(result, list)

    def test_get_raw_providers_returns_list_of_dicts(self):
        with patch("builtins.open", mock_open(read_data="chat:\n  x: {id: x}")):
            with patch("python.helpers.providers.files") as mf:
                mf.get_abs_path.return_value = "/conf/model_providers.yaml"
                from python.helpers.providers import get_raw_providers
                result = get_raw_providers("chat")
        assert isinstance(result, list)
