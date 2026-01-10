import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import settings as settings_helper


def test_websocket_harness_entrypoint_is_present_in_developer_settings_template():
    dev_template_path = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "developer"
        / "dev.html"
    )
    content = dev_template_path.read_text(encoding="utf-8")
    assert "websocket-tester.html" in content
    assert "!$store.settingsStore.additional?.is_dockerized" in content


def test_websocket_harness_template_is_gated_by_runtime():
    template_path = PROJECT_ROOT / "webui" / "components" / "settings" / "developer" / "websocket-tester.html"
    content = template_path.read_text(encoding="utf-8")
    assert "window.runtimeInfo?.isDevelopment" in content
    assert "$store.root?.isDevelopment" not in content
