from __future__ import annotations

import importlib
import importlib.util
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from helpers.errors import format_error
from helpers.print_style import PrintStyle


_LOCK = threading.Lock()
_CHECKED = False
_PLUGIN_DIR = Path(__file__).resolve().parent
_ROOT_REQUIREMENTS_FILE = _PLUGIN_DIR.parents[1] / "requirements.txt"


def has_liteparse() -> bool:
    return importlib.util.find_spec("liteparse") is not None


def ensure_dependencies(raise_on_error: bool = True) -> bool:
    """Install framework-runtime dependencies needed by the plugin."""
    global _CHECKED

    if _CHECKED and has_liteparse():
        return True

    with _LOCK:
        if _CHECKED and has_liteparse():
            return True
        if has_liteparse():
            _CHECKED = True
            return True

        try:
            _install_requirements()
            importlib.invalidate_caches()
            if not has_liteparse():
                raise RuntimeError(
                    "Document Query dependency 'liteparse' is still unavailable after installation"
                )
            _CHECKED = True
            return True
        except Exception as e:
            message = (
                "Document Query: failed to install LiteParse dependency: "
                f"{format_error(e)}"
            )
            if raise_on_error:
                raise RuntimeError(message) from e
            PrintStyle.error(message)
            return False


def install() -> bool:
    return ensure_dependencies(raise_on_error=True)


def _install_requirements() -> None:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError(
            "Document Query plugin requires 'uv' to install liteparse automatically"
        )
    requirement = _liteparse_requirement()
    if not requirement:
        raise RuntimeError(
            f"Document Query LiteParse requirement not found in {_ROOT_REQUIREMENTS_FILE}"
        )

    cmd = [
        uv,
        "pip",
        "install",
        "--python",
        sys.executable,
        requirement,
    ]

    PrintStyle.info("Document Query: liteparse not found, installing plugin dependency")
    subprocess.check_call(cmd, cwd=str(_PLUGIN_DIR))


def _liteparse_requirement() -> str:
    if not _ROOT_REQUIREMENTS_FILE.is_file():
        return ""
    for line in _ROOT_REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        requirement = line.strip()
        if requirement.startswith("liteparse"):
            return requirement
    return ""
