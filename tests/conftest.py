"""Pytest session bootstrap for the framework test suite.

- Triggers the Telegram plugin's lazy runtime dependency install (aiogram)
  before collection so test_telegram_* modules import cleanly. If the
  install is not possible (e.g. offline environment), the telegram modules
  are excluded from collection instead of erroring the whole suite.
- Excludes legacy manual scripts that are not automated tests.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
