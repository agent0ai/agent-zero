import sys
from pathlib import Path

# Keep file-discovered API/socket handlers out of pytest collection.
collect_ignore_glob = ["api/*_test.py", "plugins/*/api/test_*.py", "socket/test_*.py", "plugins/*/socket/test_*.py"]

_tests = str(Path(__file__).resolve().parent / "tests")
if _tests not in sys.path:
    sys.path.append(_tests)
