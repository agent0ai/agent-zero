from __future__ import annotations
import uuid
from helpers import virtual_desktop
from plugins._browser.helpers.sandbox import worker
DEFAULT_WIDTH, DEFAULT_HEIGHT = 1024, 768

def keyboard_options() -> dict[str, str]:
    """Resolve the configured XKB keyboard layout for browser displays."""
    from plugins._browser.helpers.config import (
        KEYBOARD_LAYOUT_KEY,
        KEYBOARD_VARIANT_KEY,
        get_browser_config,
    )

    config = get_browser_config()
    return {
        "layout": str(config.get(KEYBOARD_LAYOUT_KEY, "") or "").strip(),
        "variant": str(config.get(KEYBOARD_VARIANT_KEY, "") or "").strip(),
    }



def collect_status():
    return {'available': True, 'missing': [], 'sandbox': True, 'running': worker.ready}
