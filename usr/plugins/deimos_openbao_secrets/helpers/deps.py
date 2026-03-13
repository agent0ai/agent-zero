"""Auto-install plugin dependencies on first load.

Ensures hvac, tenacity, and circuitbreaker are available in the
A0 runtime venv without requiring manual pip install.
"""
import importlib
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

_REQUIRED = [
    ("hvac", "hvac>=2.1.0"),
    ("tenacity", "tenacity>=8.2.0"),
    ("circuitbreaker", "circuitbreaker>=2.0.0"),
]

_installed = False


def ensure_dependencies() -> bool:
    """Check and install missing dependencies. Returns True if all available."""
    global _installed
    if _installed:
        return True

    missing = []
    for import_name, pip_spec in _REQUIRED:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_spec)

    if not missing:
        _installed = True
        return True

    logger.info("Installing missing OpenBao plugin dependencies: %s", missing)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        # Verify imports after install
        for import_name, _ in _REQUIRED:
            importlib.import_module(import_name)
        _installed = True
        logger.info("OpenBao plugin dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install OpenBao plugin dependencies: %s", exc.stderr.decode() if exc.stderr else exc)
        return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout installing OpenBao plugin dependencies")
        return False
    except ImportError as exc:
        logger.error("Dependencies installed but import still fails: %s", exc)
        return False
