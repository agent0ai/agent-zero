from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from helpers.errors import format_error
from helpers.print_style import PrintStyle


_LOCK = threading.Lock()
_PLUGIN_DIR = Path(__file__).resolve().parent
_ROOT_REQUIREMENTS_FILE = _PLUGIN_DIR.parents[1] / "requirements.txt"


def ensure_dependencies(raise_on_error: bool = True) -> bool:
    """Install the pinned framework-runtime dependency when needed."""
    with _LOCK:
        try:
            requirement = _json_repair_requirement()
            if _json_repair_is_current(requirement):
                return True

            uv = shutil.which("uv")
            if not uv:
                raise RuntimeError(
                    "Context Doctor plugin requires 'uv' to install json_repair automatically"
                )

            PrintStyle.info(
                "Context Doctor: installing pinned json_repair dependency"
            )
            subprocess.check_call(
                [uv, "pip", "install", "--python", sys.executable, requirement],
                cwd=str(_PLUGIN_DIR),
            )
            importlib.invalidate_caches()
            if not _json_repair_is_current(requirement):
                raise RuntimeError(
                    f"Context Doctor dependency {requirement!r} is unavailable after installation"
                )
            return True
        except Exception as exc:
            message = (
                "Context Doctor: failed to install json_repair dependency: "
                f"{format_error(exc)}"
            )
            if raise_on_error:
                raise RuntimeError(message) from exc
            PrintStyle.error(message)
            return False


def install() -> bool:
    return ensure_dependencies(raise_on_error=True)


def _json_repair_requirement() -> str:
    if _ROOT_REQUIREMENTS_FILE.is_file():
        for line in _ROOT_REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
            requirement = line.strip()
            if requirement.startswith("json_repair=="):
                return requirement
    raise RuntimeError(
        f"Context Doctor pinned json_repair requirement not found in {_ROOT_REQUIREMENTS_FILE}"
    )


def _json_repair_is_current(requirement: str) -> bool:
    expected_version = requirement.partition("==")[2]
    if not expected_version or importlib.util.find_spec("json_repair") is None:
        return False
    try:
        return importlib.metadata.version("json-repair") == expected_version
    except importlib.metadata.PackageNotFoundError:
        return False
