from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_katex_css_font_assets_are_complete():
    katex = PROJECT_ROOT / "webui" / "vendor" / "katex"
    css = (katex / "katex.min.css").read_text(encoding="utf-8")
    referenced = set(re.findall(r"fonts/(KaTeX_[^)\"']+\.(?:woff2|woff|ttf))", css))
    available = {path.name for path in (katex / "fonts").iterdir() if path.is_file()}

    assert referenced == available
