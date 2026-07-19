import sys
from pathlib import Path


a0_root = str(Path(__file__).resolve().parents[3])
while a0_root in sys.path:
    sys.path.remove(a0_root)
sys.path.insert(0, a0_root)
