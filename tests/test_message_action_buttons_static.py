from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_message_action_buttons_are_not_text_selectable() -> None:
    css = PROJECT_ROOT.joinpath(
        "webui",
        "components",
        "messages",
        "action-buttons",
        "simple-action-buttons.css",
    ).read_text(encoding="utf-8")

    block = css[css.index(".step-action-buttons {"):css.index("}", css.index(".step-action-buttons {"))]
    assert "user-select: none;" in block
