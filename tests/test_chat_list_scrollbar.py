from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_chat_list_shows_vertical_scrollbar_without_horizontal_scroll() -> None:
    html = (
        PROJECT_ROOT / "webui/components/sidebar/chats/chats-list.html"
    ).read_text(encoding="utf-8")

    assert 'class="config-list chats-config-list"' in html
    assert 'class="config-list chats-config-list no-scrollbar"' not in html

    style_start = html.index(".chats-config-list {")
    style = html[style_start : html.index("}", style_start)]
    assert "overflow-y: auto;" in style
    assert "overflow-x: hidden;" in style
    assert "overflow: scroll;" not in style
