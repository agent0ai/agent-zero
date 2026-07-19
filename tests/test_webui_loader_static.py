from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_extension_discovery_requests_are_serialized() -> None:
    source = (PROJECT_ROOT / "webui/js/extensions.js").read_text(encoding="utf-8")

    assert "let extensionRequestQueue = Promise.resolve();" in source
    assert "extensionRequestQueue = request.catch(() => {});" in source
    assert source.count("await requestExtensionPaths(") == 2


def test_component_placeholder_is_removed_after_failure() -> None:
    source = (PROJECT_ROOT / "webui/js/components.js").read_text(encoding="utf-8")
    finally_block = source.rsplit("} finally {", maxsplit=1)[1]

    assert "targetElement.querySelector(':scope > .loading')?.remove();" in finally_block
