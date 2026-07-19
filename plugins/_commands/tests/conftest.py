# tests/conftest.py
import sys
from pathlib import Path

# Ensure A0 framework root is first in sys.path so that
# `from helpers import ...` resolves to A0's helpers/, not
# the Commands plugin's local helpers/ directory.
a0_root = str(Path(__file__).resolve().parents[3])  # tests/ → _commands → plugins → a0
while a0_root in sys.path:
    sys.path.remove(a0_root)
sys.path.insert(0, a0_root)
