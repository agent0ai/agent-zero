"""Plugin lifecycle hooks for deimos_openbao_secrets.

Called by the Agent Zero framework via helpers.plugins.call_plugin_hook().
See plugins/README.md for the hooks.py contract.

Available hooks:
    install()   — called after plugin install/update (via plugin installer)
    uninstall() — called before plugin deletion
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).parent
_REQUIREMENTS = _PLUGIN_DIR / "requirements.txt"


def install():
    """Install plugin dependencies into the framework runtime.

    Called automatically by the plugin installer after:
      - install_from_git()
      - install_from_zip()
      - update_from_git()

    Reads requirements.txt and installs into the current Python
    environment (the A0 framework venv, typically /opt/venv-a0).
    """
    if not _REQUIREMENTS.exists():
        logger.warning("requirements.txt not found at %s — skipping", _REQUIREMENTS)
        return

    logger.info("Installing deimos_openbao_secrets dependencies from %s", _REQUIREMENTS)
    try:
        subprocess.check_call(
            [
                sys.executable, "-m", "pip", "install",
                "--quiet",
                "-r", str(_REQUIREMENTS),
            ],
            timeout=120,
        )
        logger.info("deimos_openbao_secrets dependencies installed successfully")
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install dependencies: %s", exc)
        raise
    except subprocess.TimeoutExpired:
        logger.error("Timeout installing dependencies (120s)")
        raise
