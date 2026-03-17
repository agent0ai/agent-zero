"""Integration tests for MiniMax provider.

These tests call the real MiniMax API and are skipped when MINIMAX_API_KEY
is not set.  They verify that the OpenAI-compatible endpoint works with the
configuration defined in model_providers.yaml.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import yaml

API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = "https://api.minimax.io/v1"

pytestmark = pytest.mark.skipif(not API_KEY, reason="MINIMAX_API_KEY not set")


@pytest.fixture
def openai_client():
    """Create an OpenAI client pointed at MiniMax."""
    import openai

    return openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)


class TestMiniMaxChatCompletion:
    """Verify MiniMax chat completion via OpenAI-compatible API."""

    def test_basic_chat(self, openai_client):
        response = openai_client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
            max_tokens=20,
            temperature=1.0,
        )
        assert response.choices
        content = response.choices[0].message.content
        assert content, "Response should not be empty"
        assert len(content) > 0

    def test_highspeed_model(self, openai_client):
        response = openai_client.chat.completions.create(
            model="MiniMax-M2.5-highspeed",
            messages=[{"role": "user", "content": "Reply with 'ok'."}],
            max_tokens=10,
            temperature=1.0,
        )
        assert response.choices
        assert response.choices[0].message.content

    def test_streaming(self, openai_client):
        stream = openai_client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[{"role": "user", "content": "Count from 1 to 3."}],
            max_tokens=50,
            temperature=1.0,
            stream=True,
        )
        chunks = list(stream)
        assert len(chunks) > 1, "Streaming should produce multiple chunks"

    def test_system_message(self, openai_client):
        response = openai_client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'test passed'."},
            ],
            max_tokens=20,
            temperature=1.0,
        )
        assert response.choices[0].message.content

    def test_temperature_near_zero(self, openai_client):
        """Verify that a near-zero temperature (but > 0) works."""
        response = openai_client.chat.completions.create(
            model="MiniMax-M2.5",
            messages=[{"role": "user", "content": "Say 'deterministic'."}],
            max_tokens=10,
            temperature=0.01,
        )
        assert response.choices[0].message.content


class TestMiniMaxYAMLConsistency:
    """Verify the YAML config matches what works with the real API."""

    def test_yaml_api_base_works(self, openai_client):
        """The api_base from YAML should be the one the client is using."""
        config_path = PROJECT_ROOT / "conf" / "model_providers.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        yaml_base = config["chat"]["minimax"]["kwargs"]["api_base"]
        assert yaml_base == BASE_URL
