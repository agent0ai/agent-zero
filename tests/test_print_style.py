import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.print_style import PrintStyle


class _PassthroughSecretsManager:
    def mask_values(self, text: str) -> str:
        return text


@pytest.fixture(autouse=True)
def _reset_print_style_state():
    PrintStyle.last_endline = True
    yield
    PrintStyle.last_endline = True


def test_get_sanitizes_lone_surrogates():
    style = PrintStyle(log_only=True)
    style.secrets_mgr = _PassthroughSecretsManager()

    plain_text, styled_text, html_text = style.get("bad \ud83d")

    assert plain_text == "bad ?"
    assert "\ud83d" not in styled_text
    assert "\ud83d" not in html_text


def test_print_sanitizes_lone_surrogates_without_crash(capsys):
    style = PrintStyle()
    style.secrets_mgr = _PassthroughSecretsManager()

    style.print("bad \ud83d")

    content = capsys.readouterr().out

    assert "bad ?" in content
    assert "\ud83d" not in content
