"""Tests for python/helpers/perplexity_search.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestPerplexitySearch:
    def test_returns_message_content(self):
        from python.helpers import perplexity_search

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Search result text"

        with patch("python.helpers.perplexity_search.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            with patch("python.helpers.perplexity_search.models") as mock_models:
                mock_models.get_api_key.return_value = "test-key"

                result = perplexity_search.perplexity_search("test query")

                assert result == "Search result text"
                mock_client.chat.completions.create.assert_called_once()

    def test_uses_api_key_from_models_when_not_provided(self):
        from python.helpers import perplexity_search

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"

        with patch("python.helpers.perplexity_search.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            with patch("python.helpers.perplexity_search.models") as mock_models:
                mock_models.get_api_key.return_value = "from-models"

                perplexity_search.perplexity_search("q")

                mock_openai_cls.assert_called_once_with(
                    api_key="from-models",
                    base_url="https://api.perplexity.ai",
                )

    def test_uses_provided_api_key(self):
        from python.helpers import perplexity_search

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"

        with patch("python.helpers.perplexity_search.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            perplexity_search.perplexity_search("q", api_key="custom-key")

            mock_openai_cls.assert_called_once_with(
                api_key="custom-key",
                base_url="https://api.perplexity.ai",
            )
