from __future__ import annotations

from unittest.mock import patch

import pytest

_DEFAULT_CONFIG = {
    "update_log": False,
    "suppress_xml": True,
    "split_thoughts": True,
}


@pytest.fixture(autouse=True)
def _mock_plugin_config():
    with patch(
        "helpers.plugins.get_plugin_config",
        return_value=_DEFAULT_CONFIG,
    ):
        yield
