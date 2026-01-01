import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import settings as settings_helper


def _build_sections(monkeypatch: pytest.MonkeyPatch, is_dev: bool):
    monkeypatch.setattr(settings_helper.runtime, "is_development", lambda: is_dev)
    output = settings_helper.convert_out(settings_helper.get_settings())
    return output["sections"]


def test_websocket_harness_section_only_in_development(monkeypatch: pytest.MonkeyPatch):
    sections = _build_sections(monkeypatch, True)
    section_ids = [section["id"] for section in sections]
    assert "dev_testing" in section_ids

    dev_index = section_ids.index("dev")
    testing_index = section_ids.index("dev_testing")
    assert testing_index > dev_index

    prod_sections = _build_sections(monkeypatch, False)
    prod_ids = [section["id"] for section in prod_sections]
    assert "dev_testing" not in prod_ids


def test_websocket_harness_template_is_gated_by_runtime():
    template_path = PROJECT_ROOT / "webui" / "components" / "settings" / "developer" / "websocket-tester.html"
    content = template_path.read_text(encoding="utf-8")
    assert "$store.root?.isDevelopment" in content
