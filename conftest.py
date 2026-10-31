import sys
from pathlib import Path

# pytest prepends test dirs to sys.path, so api/plugins.py shadows the plugins namespace package
collect_ignore_glob = ["api/*_test.py", "plugins/*/api/test_*.py"]

_tests = str(Path(__file__).resolve().parent / "tests")
if _tests not in sys.path:
    sys.path.append(_tests)
