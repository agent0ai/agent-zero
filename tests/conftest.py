"""Pytest session bootstrap for the framework test suite.

- Triggers the Telegram plugin's lazy runtime dependency install (aiogram)
  before collection so test_telegram_* modules import cleanly. If the
  install is not possible (e.g. offline environment), the telegram modules
  are excluded from collection instead of erroring the whole suite.
- Excludes legacy manual scripts that are not automated tests.
- Guards the live usr tree: any test that tries to write under <repo>/usr
  fails loudly. Inside the deployed container that path is the persistent
  volume holding real chats, model presets, .env secrets and time-travel
  history, and suite runs have corrupted it in the past. Tests that need a
  usr tree must redirect helpers.files._base_dir to tmp_path.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import dotenv as a0_dotenv
from helpers import files as a0_files

_REAL_USR_DIR = os.path.realpath(os.path.join(a0_files.get_base_dir(), "usr"))


def _live_usr_path(path: object) -> str | None:
    """Return the resolved live-usr path a write would hit, or None."""
    try:
        candidate = str(path)
    except Exception:
        return None
    if not os.path.isabs(candidate):
        candidate = os.path.join(a0_files.get_base_dir(), candidate)
    real = os.path.realpath(candidate)
    if real == _REAL_USR_DIR or real.startswith(_REAL_USR_DIR + os.sep):
        return real
    return None


@pytest.fixture(autouse=True)
def _guard_live_usr_writes(monkeypatch):
    """Fail any test that writes into the live Agent Zero usr tree."""

    def guard_write(original):
        def wrapper(relative_path, *args, **kwargs):
            hit = _live_usr_path(relative_path)
            if hit is not None:
                raise RuntimeError(
                    f"test attempted to write live Agent Zero usr path: {hit}"
                )
            return original(relative_path, *args, **kwargs)

        return wrapper

    for name in (
        "write_file",
        "write_file_bin",
        "write_file_base64",
        "delete_file",
        "delete_dir",
    ):
        monkeypatch.setattr(a0_files, name, guard_write(getattr(a0_files, name)))

    original_save = a0_dotenv.save_dotenv_value

    def guarded_save_dotenv_value(key, value):
        hit = _live_usr_path(a0_dotenv.get_dotenv_file_path())
        if hit is not None:
            raise RuntimeError(
                f"test attempted to write live Agent Zero env file: {hit}"
            )
        return original_save(key, value)

    monkeypatch.setattr(a0_dotenv, "save_dotenv_value", guarded_save_dotenv_value)
    # helpers.localization imported save_dotenv_value by value, so it needs
    # its own patch; tests that stub it themselves simply replace this one.
    from helpers import localization as a0_localization

    monkeypatch.setattr(
        a0_localization, "save_dotenv_value", guarded_save_dotenv_value
    )
    yield

collect_ignore = [
    # Legacy manual smoke scripts, not automated tests. email_parser_test.py
    # imports helpers.email_client.read_messages, which no longer exists (the
    # module is fully commented out), and its only test is marked skip with a
    # note asking to move it to a script. rate_limiter_test.py performs a real
    # LLM API call at import time.
    "email_parser_test.py",
    "rate_limiter_test.py",
]

try:
    from plugins._telegram_integration.helpers.dependencies import (
        ensure_dependencies,
    )

    ensure_dependencies()
except (RuntimeError, subprocess.CalledProcessError) as exc:
    # Dependency installation failed (e.g. offline environment): exclude the
    # telegram tests at collection time rather than failing the whole suite,
    # but say so loudly - silently erasing five test files would mask real
    # plugin regressions in CI. Import errors from plugin code itself are
    # intentionally NOT caught here and will fail the run.
    print(
        f"WARNING: telegram dependencies unavailable ({exc}); "
        "excluding test_telegram_* from collection."
    )
    collect_ignore_glob = ["test_telegram_*.py"]
