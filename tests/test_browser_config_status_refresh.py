import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="Node.js is required")


def test_background_status_refresh_keeps_the_loading_indicator_off():
    path = PROJECT_ROOT / "plugins" / "_browser" / "webui" / "browser-config-store.js"
    source = path.read_text(encoding="utf-8")
    source = re.sub(r"^import .*;\n", "", source, flags=re.M)
    source = source.replace("export const store = createStore", "const store = createStore")
    script = (
        "const createStore = (_name, value) => value;\n"
        "const callJsonApi = async () => ({ host_browser: { connectors: [] } });\n"
        "const showConfirmDialog = async () => false;\n"
        + source
        + "\nstore.config = ensureConfig({});\n"
        "const initial = store.loadHostBrowserStatus();\n"
        "if (!store.hostBrowserStatusLoading) throw new Error('initial load lost its spinner');\n"
        "await initial;\n"
        "if (store.hostBrowserStatusLoading) throw new Error('initial load kept the spinner');\n"
        "const refresh = store.loadHostBrowserStatus();\n"
        "if (store.hostBrowserStatusLoading) throw new Error('background refresh flashes the spinner');\n"
        "if (!store.hostBrowserStatusRefreshing) throw new Error('background refresh runs unguarded');\n"
        "await refresh;\n"
        "if (store.hostBrowserStatusRefreshing) throw new Error('background refresh never cleared');\n"
        "store.cleanup();\n"
        "if (store.hostBrowserStatusRefreshing) throw new Error('cleanup left the refresh flag set');\n"
    )

    subprocess.run(["node", "--input-type=module", "-e", script], check=True, text=True)
