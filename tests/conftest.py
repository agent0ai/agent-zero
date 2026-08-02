"""Pytest session bootstrap for the framework test suite.

- Triggers the Telegram plugin's lazy runtime dependency install (aiogram)
  before collection so test_telegram_* modules import cleanly. If the
  install is not possible (e.g. offline environment), the telegram modules
  are excluded from collection instead of erroring the whole suite.
- Excludes legacy manual scripts that are not automated tests.
- Guards the live usr tree: any test that tries to write under <repo>/usr
  via the helpers.files write/delete functions or the helpers.dotenv save
  path fails loudly. Inside the deployed container that path is the
  persistent volume holding real chats, model presets, .env secrets and
  time-travel history, and suite runs have corrupted it in the past. Tests
  that need a usr tree must redirect helpers.files._base_dir to tmp_path.
  Scope note: only those helpers.files / helpers.dotenv write paths are
  intercepted. Direct open(), Path.write_text(), shutil, os.makedirs() or
  subprocess writes from test or helper code are NOT guarded.
"""

import os
import subprocess
import sys
import warnings
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

    # Modules that did `from helpers.files/dotenv import ...` at their own
    # import time (i.e. before this fixture ran) hold the ORIGINAL unguarded
    # function object, bypassing the guard - e.g. helpers.task_scheduler
    # imported at collection time by test_task_scheduler_timezone.py would
    # write usr/scheduler/tasks.json straight through. Re-bind those names
    # to the guarded versions. Modules not imported yet are skipped: a later
    # `from helpers.files import write_file` picks up the already-guarded
    # attribute. Tests that stub one of these names themselves simply
    # replace this patch.
    for module_name, attr, source in (
        ("helpers.localization", "save_dotenv_value", a0_dotenv),
        ("helpers.task_scheduler", "write_file", a0_files),
    ):
        module = sys.modules.get(module_name)
        if module is not None:
            monkeypatch.setattr(module, attr, getattr(source, attr))
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

    # Intentional collection-time side effect: the telegram plugin installs
    # its runtime dependencies lazily (uv pip install), so doing it up front
    # here lets the test_telegram_* modules import cleanly.
    ensure_dependencies()
except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
    # Dependency installation failed (e.g. offline environment, or a
    # missing/broken uv binary): exclude the telegram tests at collection
    # time rather than failing the whole suite, but say so loudly in the
    # pytest warnings summary - silently erasing five test files would mask
    # real plugin regressions in CI. Import errors from plugin code itself
    # are intentionally NOT caught here and will fail the run.
    warnings.warn(
        f"telegram dependencies unavailable ({exc}); "
        "excluding test_telegram_* from collection.",
        stacklevel=2,
    )
    collect_ignore_glob = ["test_telegram_*.py"]
