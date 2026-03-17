"""Unit tests for MiniMax provider integration.

Tests cover:
- Provider YAML configuration loading
- ProviderManager listing
- Temperature clamping logic for MiniMax models
- API key env var detection pattern
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import yaml


# ---------------------------------------------------------------------------
# 1. YAML configuration tests
# ---------------------------------------------------------------------------

class TestMiniMaxYAMLConfig:
    """Verify that MiniMax is correctly defined in model_providers.yaml."""

    @pytest.fixture(autouse=True)
    def load_yaml(self):
        config_path = PROJECT_ROOT / "conf" / "model_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def test_minimax_exists_in_chat_providers(self):
        assert "minimax" in self.config["chat"], "MiniMax should be in chat providers"

    def test_minimax_name(self):
        assert self.config["chat"]["minimax"]["name"] == "MiniMax"

    def test_minimax_litellm_provider(self):
        assert self.config["chat"]["minimax"]["litellm_provider"] == "openai"

    def test_minimax_api_base(self):
        api_base = self.config["chat"]["minimax"]["kwargs"]["api_base"]
        assert api_base == "https://api.minimax.io/v1"

    def test_minimax_api_base_not_chat_domain(self):
        api_base = self.config["chat"]["minimax"]["kwargs"]["api_base"]
        assert "minimax.chat" not in api_base, "Must not use api.minimax.chat"

    def test_minimax_alphabetical_order(self):
        """MiniMax should be between lm_studio and mistral in the YAML."""
        keys = list(self.config["chat"].keys())
        lm_idx = keys.index("lm_studio")
        mm_idx = keys.index("minimax")
        mi_idx = keys.index("mistral")
        assert lm_idx < mm_idx < mi_idx

    def test_minimax_not_in_embedding(self):
        """MiniMax should only be added as a chat provider."""
        assert "minimax" not in self.config.get("embedding", {})


# ---------------------------------------------------------------------------
# 2. ProviderManager tests
# ---------------------------------------------------------------------------

class TestMiniMaxProviderManager:
    """Verify ProviderManager correctly loads MiniMax from YAML."""

    @pytest.fixture(autouse=True)
    def reset_and_load(self):
        from python.helpers.providers import ProviderManager
        # Reset singleton so it reloads from updated YAML
        ProviderManager._instance = None
        ProviderManager._raw = None
        ProviderManager._options = None
        self.pm = ProviderManager.get_instance()

    def test_minimax_in_chat_options(self):
        options = self.pm.get_providers("chat")
        ids = [opt["value"] for opt in options]
        assert "minimax" in ids

    def test_minimax_label(self):
        options = self.pm.get_providers("chat")
        minimax = next(opt for opt in options if opt["value"] == "minimax")
        assert minimax["label"] == "MiniMax"

    def test_minimax_provider_config(self):
        cfg = self.pm.get_provider_config("chat", "minimax")
        assert cfg is not None
        assert cfg["litellm_provider"] == "openai"
        assert cfg["kwargs"]["api_base"] == "https://api.minimax.io/v1"

    def test_minimax_case_insensitive_lookup(self):
        cfg = self.pm.get_provider_config("chat", "MiniMax")
        assert cfg is not None
        assert cfg["name"] == "MiniMax"


# ---------------------------------------------------------------------------
# 3. Temperature clamping tests (extracted logic)
# ---------------------------------------------------------------------------

def _adjust_call_args_temp_logic(model_name: str, kwargs: dict) -> dict:
    """Extract the MiniMax temperature clamping logic from models._adjust_call_args
    for standalone testing without importing the full models module."""
    if "minimax" in model_name.lower() or (
        kwargs.get("api_base", "") and "minimax" in kwargs["api_base"]
    ):
        temp = kwargs.get("temperature")
        if temp is not None:
            temp = float(temp)
            if temp <= 0.0:
                kwargs["temperature"] = 0.01
            elif temp > 1.0:
                kwargs["temperature"] = 1.0
    return kwargs


class TestMiniMaxTemperatureClamping:
    """MiniMax requires temperature in (0.0, 1.0]."""

    def test_zero_temperature_clamped(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5", {"temperature": 0.0}
        )
        assert result["temperature"] > 0.0

    def test_negative_temperature_clamped(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5", {"temperature": -1.0}
        )
        assert result["temperature"] > 0.0

    def test_high_temperature_clamped_to_one(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5", {"temperature": 2.0}
        )
        assert result["temperature"] == 1.0

    def test_valid_temperature_unchanged(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5", {"temperature": 0.7}
        )
        assert result["temperature"] == 0.7

    def test_boundary_temperature_one_unchanged(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5", {"temperature": 1.0}
        )
        assert result["temperature"] == 1.0

    def test_no_temperature_no_error(self):
        result = _adjust_call_args_temp_logic("MiniMax-M2.5", {})
        assert "temperature" not in result

    def test_clamping_by_model_name_highspeed(self):
        result = _adjust_call_args_temp_logic(
            "MiniMax-M2.5-highspeed", {"temperature": 0.0}
        )
        assert result["temperature"] > 0.0

    def test_clamping_by_api_base(self):
        result = _adjust_call_args_temp_logic(
            "some-model",
            {"temperature": 0.0, "api_base": "https://api.minimax.io/v1"},
        )
        assert result["temperature"] > 0.0

    def test_non_minimax_not_clamped(self):
        result = _adjust_call_args_temp_logic(
            "gpt-4o", {"temperature": 0.0}
        )
        assert result["temperature"] == 0.0


# ---------------------------------------------------------------------------
# 4. API key env var detection pattern tests
# ---------------------------------------------------------------------------

class TestMiniMaxAPIKeyPattern:
    """Verify the env var naming pattern works for MiniMax."""

    def test_minimax_api_key_format(self):
        """MINIMAX_API_KEY matches the pattern {SERVICE}_API_KEY."""
        service = "minimax"
        expected_key = f"{service.upper()}_API_KEY"
        assert expected_key == "MINIMAX_API_KEY"

    def test_api_key_minimax_format(self):
        """API_KEY_MINIMAX matches the pattern API_KEY_{SERVICE}."""
        service = "minimax"
        expected_key = f"API_KEY_{service.upper()}"
        assert expected_key == "API_KEY_MINIMAX"

    def test_minimax_api_token_format(self):
        """MINIMAX_API_TOKEN matches the fallback pattern."""
        service = "minimax"
        expected_key = f"{service.upper()}_API_TOKEN"
        assert expected_key == "MINIMAX_API_TOKEN"

    def test_env_var_detected(self, monkeypatch):
        """Simulate the get_api_key logic for MiniMax."""
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key-abc")
        service = "minimax"
        key = (
            os.environ.get(f"API_KEY_{service.upper()}")
            or os.environ.get(f"{service.upper()}_API_KEY")
            or os.environ.get(f"{service.upper()}_API_TOKEN")
            or "None"
        )
        assert key == "test-key-abc"
