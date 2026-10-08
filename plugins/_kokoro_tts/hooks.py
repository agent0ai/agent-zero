from __future__ import annotations

import importlib
import importlib.metadata
import shutil
import subprocess
import sys
import threading

from packaging.requirements import Requirement

from helpers.print_style import PrintStyle
from plugins._kokoro_tts.helpers import migration, runtime

_DEPENDENCIES = (
    Requirement("onnxruntime>=1.19.2"),
    Requirement("en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"),
)
_SETUP_LOCK = threading.Lock()


def _missing_requirements() -> list[str]:
    missing = []
    for requirement in _DEPENDENCIES:
        try:
            version = importlib.metadata.version(requirement.name)
        except importlib.metadata.PackageNotFoundError:
            version = None
        if version is None or version not in requirement.specifier:
            missing.append(str(requirement))
    return missing


def ensure_dependencies(raise_on_error: bool = True) -> bool:
    with _SETUP_LOCK:
        try:
            missing = _missing_requirements()
            if not missing:
                return True
            uv = shutil.which("uv")
            if not uv:
                raise RuntimeError("Local TTS requires 'uv' to prepare its dependencies.")
            PrintStyle.info("Local TTS: preparing dependencies:", ", ".join(missing))
            subprocess.check_call(
                [uv, "pip", "install", "--python", sys.executable, *missing],
                timeout=60,
            )
            importlib.invalidate_caches()
            if _missing_requirements():
                raise RuntimeError("Local TTS dependencies are still unavailable after installation.")
            return True
        except Exception as exc:
            if raise_on_error:
                raise RuntimeError(f"Local TTS dependency setup failed: {exc}") from exc
            PrintStyle.error(f"Local TTS dependency setup failed: {exc}")
            return False


def install() -> bool:
    return ensure_dependencies()


def get_plugin_config(default=None, **kwargs):
    migration.ensure_migrated()
    return runtime.normalize_config(default or {})


def save_plugin_config(default=None, settings=None, **kwargs):
    return runtime.normalize_config(settings or default or {})
