import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Some environments may have a third-party `agents` module installed, which can
# shadow this repo's top-level `agents/` folder and break imports like
# `agents.gatekeeper...`. Ensure the local namespace package wins.
maybe_agents = sys.modules.get("agents")
if maybe_agents is not None and not hasattr(maybe_agents, "__path__"):
    del sys.modules["agents"]

# Pre-import local `agents/` so subsequent `import agents` doesn't resolve to an
# external module with the same name.
try:
    import agents  # noqa: F401
except Exception:
    pass
