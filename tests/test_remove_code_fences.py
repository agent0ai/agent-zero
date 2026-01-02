import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.files import remove_code_fences


def test_remove_code_fences_does_not_strip_inline_tildes_or_join_lines():
    src = (
        "full message is automatically markdown do not wrap ~~~markdown\n"
        "use emojis as icons improve readability\n"
        "usage:\n"
        "~~~json\n"
        "{\n"
        '  \"a\": 1\n'
        "}\n"
        "~~~\n"
    )

    out = remove_code_fences(src)

    assert "wrap ~~~markdown\nuse emojis" in out
    assert "wrap ~~~markdownuse emojis" not in out
    assert "~~~json" not in out
    assert "\n~~~\n" not in out
    assert '"a": 1' in out
