from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return PROJECT_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_component_loader_deduplicates_body_assets() -> None:
    source = read("webui", "js", "components.js")

    assert 'const componentAssetSelector = "style, script, link[rel=\'stylesheet\']";' in source
    assert "...doc.querySelectorAll(componentAssetSelector)" in source
    assert "...Array.from(doc.body.childNodes).filter(" in source
    assert "(node) => !node.matches?.(componentAssetSelector)" in source


def test_component_loader_loading_lifecycle() -> None:
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the component-loader regression.")

    subprocess.run(
        ["node", "--test", str(PROJECT_ROOT / "tests/test_webui_component_loader.mjs")],
        check=True,
        timeout=30,
    )
