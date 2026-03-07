"""Tests for SettingsValidator."""

import pytest

from python.helpers.settings_validation import SettingsValidator


@pytest.mark.unit
class TestSettingsValidator:
    def test_valid_settings(self):
        raw = {
            "chat_model_provider": "openai",
            "chat_model_name": "gpt-4",
            "embed_model_provider": "openai",
            "embed_model_name": "text-embedding-3-small",
            "chat_model_ctx_length": 8192,
            "chat_model_rl_requests": 100,
            "chat_model_rl_input": 0,
            "chat_model_rl_output": 0,
        }
        validated, warnings = SettingsValidator.validate(raw)
        assert validated["chat_model_provider"] == "openai"
        # No warnings about required fields
        required_warnings = [w for w in warnings if "required field" in w]
        assert len(required_warnings) == 0

    def test_negative_ctx_length_warning(self):
        raw = {
            "chat_model_provider": "openai",
            "chat_model_name": "gpt-4",
            "embed_model_provider": "openai",
            "embed_model_name": "text-embedding-3-small",
            "chat_model_ctx_length": -1,
        }
        _, warnings = SettingsValidator.validate(raw)
        assert any("chat_model" in w and "ctx_length" in w for w in warnings)

    def test_negative_rate_limit_warning(self):
        raw = {
            "chat_model_provider": "openai",
            "chat_model_name": "gpt-4",
            "embed_model_provider": "openai",
            "embed_model_name": "text-embed",
            "chat_model_rl_requests": -5,
        }
        _, warnings = SettingsValidator.validate(raw)
        assert any("chat_model" in w for w in warnings)

    def test_missing_required_fields(self):
        _, warnings = SettingsValidator.validate({})
        required_warnings = [w for w in warnings if "required field" in w]
        assert len(required_warnings) >= 4

    def test_port_out_of_range(self):
        raw = {
            "chat_model_provider": "x",
            "chat_model_name": "y",
            "embed_model_provider": "x",
            "embed_model_name": "y",
            "rfc_port_http": 99999,
        }
        _, warnings = SettingsValidator.validate(raw)
        assert any("deployment" in w for w in warnings)

    def test_memory_interval_zero(self):
        raw = {
            "chat_model_provider": "x",
            "chat_model_name": "y",
            "embed_model_provider": "x",
            "embed_model_name": "y",
            "memory_recall_interval": 0,
        }
        _, warnings = SettingsValidator.validate(raw)
        assert any("memory" in w for w in warnings)

    def test_memory_threshold_out_of_range(self):
        raw = {
            "chat_model_provider": "x",
            "chat_model_name": "y",
            "embed_model_provider": "x",
            "embed_model_name": "y",
            "memory_recall_similarity_threshold": 1.5,
        }
        _, warnings = SettingsValidator.validate(raw)
        assert any("memory" in w for w in warnings)

    def test_valid_ports(self):
        raw = {
            "chat_model_provider": "x",
            "chat_model_name": "y",
            "embed_model_provider": "x",
            "embed_model_name": "y",
            "rfc_port_http": 8080,
            "rfc_port_ssh": 22,
        }
        validated, warnings = SettingsValidator.validate(raw)
        deployment_warnings = [w for w in warnings if "deployment" in w]
        assert len(deployment_warnings) == 0
        assert validated["rfc_port_http"] == 8080

    def test_empty_dict_returns_validated(self):
        validated, _ = SettingsValidator.validate({})
        assert isinstance(validated, dict)
