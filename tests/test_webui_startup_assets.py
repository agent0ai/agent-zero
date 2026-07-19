from pathlib import Path
from html.parser import HTMLParser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.scripts.append(dict(attrs))


def test_bootstrap_is_local_and_deferred() -> None:
    index_html = (PROJECT_ROOT / "webui" / "index.html").read_text(encoding="utf-8")

    assert "cdn.jsdelivr.net/npm/bootstrap" not in index_html
    assert '<script defer src="vendor/bootstrap/bootstrap.bundle.min.js"></script>' in index_html
    assert (PROJECT_ROOT / "webui" / "vendor" / "bootstrap" / "bootstrap.bundle.min.js").is_file()


def test_classic_startup_scripts_are_deferred() -> None:
    index_html = (PROJECT_ROOT / "webui" / "index.html").read_text(encoding="utf-8")
    parser = ScriptParser()
    parser.feed(index_html)

    blocking_scripts = [
        script["src"]
        for script in parser.scripts
        if script.get("src")
        and script.get("type") != "module"
        and "defer" not in script
        and "async" not in script
    ]

    assert blocking_scripts == []
