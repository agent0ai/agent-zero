from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return (PROJECT_ROOT / Path(*parts)).read_text(encoding="utf-8")


def test_top_bar_stacks_above_composer_below_mobile_overlay():
    css = read("webui", "index.css")

    assert "z-index: 1002" in css.split("#time-date-container")[1].split("}")[0]
    overlay_block = css.split(".sidebar-overlay {", 1)[1].split("}", 1)[0]
    assert "z-index: 1003" in overlay_block
