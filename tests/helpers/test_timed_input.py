"""Tests for python/helpers/timed_input.py — timeout_input."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from inputimeout import TimeoutOccurred


class TestTimeoutInput:
    def test_returns_user_input_when_provided(self):
        with patch("python.helpers.timed_input.inputimeout") as m:
            m.return_value = "hello"
            from python.helpers.timed_input import timeout_input
            result = timeout_input("Prompt: ", timeout=10)
        assert result == "hello"
        m.assert_called_once_with(prompt="Prompt: ", timeout=10)

    def test_returns_empty_on_timeout(self):
        with patch("python.helpers.timed_input.inputimeout") as m:
            m.side_effect = TimeoutOccurred
            from python.helpers.timed_input import timeout_input
            result = timeout_input("Prompt: ", timeout=5)
        assert result == ""

    def test_default_timeout_is_10(self):
        with patch("python.helpers.timed_input.inputimeout") as m:
            m.return_value = "x"
            from python.helpers.timed_input import timeout_input
            timeout_input(">")
        m.assert_called_once_with(prompt=">", timeout=10)
