import asyncio
import importlib
from pathlib import Path
import sys
import types

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _bind_local_plugins_namespace() -> None:
    plugins_pkg = types.ModuleType("plugins")
    plugins_pkg.__path__ = [str(PROJECT_ROOT / "plugins")]
    sys.modules["plugins"] = plugins_pkg


def test_task_scheduler_import_is_safe_inside_uvloop_event_loop():
    uvloop = pytest.importorskip("uvloop")
    sys.modules.pop("helpers.task_scheduler", None)
    _bind_local_plugins_namespace()

    async def import_task_scheduler() -> None:
        importlib.import_module("helpers.task_scheduler")

    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(import_task_scheduler())
