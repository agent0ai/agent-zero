"""Tests for MiniMax provider entries and the Responses temperature clamp."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_chat_providers() -> dict:
    yaml_path = PROJECT_ROOT / "conf" / "model_providers.yaml"
    return yaml.safe_load(yaml_path.read_text())["chat"]


def test_minimax_global_provider_registered():
    providers = _load_chat_providers()
    assert "minimax" in providers
    entry = providers["minimax"]
    assert entry["litellm_provider"] == "openai"
    assert entry["kwargs"]["api_base"] == "https://api.minimax.io/v1"
    assert entry["kwargs"]["a0_api_mode"] == "responses"


def test_minimax_cn_provider_registered():
    providers = _load_chat_providers()
    assert "minimax-cn" in providers
    entry = providers["minimax-cn"]
    assert entry["litellm_provider"] == "openai"
    assert entry["kwargs"]["api_base"] == "https://api.minimaxi.com/v1"
    assert entry["kwargs"]["a0_api_mode"] == "responses"


@pytest.mark.parametrize(
    ("provider_name", "model_name", "api_base", "input_temp", "expected_temp"),
    [
        # provider name match
        ("minimax", "MiniMax-M3", None, 0.0, 0.01),
        ("minimax", "MiniMax-M3", None, 1.5, 1.0),
        ("minimax-cn", "MiniMax-M3", None, -0.5, 0.01),
        # api_base match (custom "openai" provider repointed at MiniMax)
        ("openai", "gpt-4", "https://api.minimax.io/v1", 0.0, 0.01),
        # model_name match (caller forgot to set provider correctly)
        ("openai", "MiniMax-M3", None, 2.0, 1.0),
        # in-range values pass through unchanged
        ("minimax", "MiniMax-M3", None, 0.7, 0.7),
        ("minimax", "MiniMax-M3", None, 1.0, 1.0),
    ],
)
def test_minimax_temperature_clamp(provider_name, model_name, api_base, input_temp, expected_temp):
    from models import _adjust_call_args

    kwargs = {"temperature": input_temp}
    if api_base is not None:
        kwargs["api_base"] = api_base

    _, _, adjusted = _adjust_call_args(provider_name, model_name, kwargs)
    assert adjusted["temperature"] == pytest.approx(expected_temp)


def test_non_minimax_provider_temperature_untouched():
    """Make sure the clamp doesn't fire for other providers."""
    from models import _adjust_call_args

    _, _, adjusted = _adjust_call_args("openai", "gpt-4", {"temperature": 0.0})
    assert adjusted["temperature"] == 0.0  # not clamped

    _, _, adjusted = _adjust_call_args("anthropic", "claude-3-opus", {"temperature": 1.5})
    assert adjusted["temperature"] == 1.5  # not clamped


def test_minimax_chat_temperature_uses_chat_api_range():
    from models import _adjust_call_args

    _, _, adjusted = _adjust_call_args(
        "openai",
        "MiniMax-M3",
        {"a0_api_mode": "chat", "temperature": 1.5},
    )
    assert adjusted["temperature"] == 1.5
