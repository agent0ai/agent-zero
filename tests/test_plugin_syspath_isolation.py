import importlib
import shutil
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import modules


def _clear_api_modules() -> None:
    for name in [
        module_name
        for module_name in sys.modules
        if module_name == "api" or module_name.startswith("api.")
    ]:
        del sys.modules[name]


def _plugin_with_api_probe(
    base_dir: Path, plugin_name: str = "plugin"
) -> tuple[Path, Path]:
    plugin_dir = base_dir / plugin_name
    plugin_api = plugin_dir / "api"
    plugin_api.mkdir(parents=True)
    (plugin_api / "__init__.py").write_text("", encoding="utf-8")
    probe = plugin_dir / "probe.py"
    probe.write_text(
        "import importlib.util\n"
        "import api\n"
        "RESOLVED = list(api.__path__)\n"
        "HAS_CORE_SUBMODULE = importlib.util.find_spec('api.health') is not None\n",
        encoding="utf-8",
    )
    return plugin_dir, plugin_api


def test_plugin_dir_first_in_sys_path_cannot_shadow_core_api(tmp_path):
    plugin_dir, plugin_api = _plugin_with_api_probe(tmp_path)
    core_api = (PROJECT_ROOT / "api").resolve()

    saved_path = list(sys.path)
    _clear_api_modules()
    sys.path.insert(0, str(plugin_dir))
    polluted_path = list(sys.path)
    try:
        module = modules.import_module(str(plugin_dir / "probe.py"))

        resolved = [Path(entry).resolve() for entry in module.RESOLVED]
        assert core_api in resolved
        assert plugin_api.resolve() not in resolved
        assert module.HAS_CORE_SUBMODULE
        assert sys.path == polluted_path
    finally:
        sys.path[:] = saved_path
        _clear_api_modules()


def test_cached_plugin_api_package_is_replaced_with_core_package(tmp_path):
    plugin_dir, plugin_api = _plugin_with_api_probe(tmp_path)
    (plugin_api / "marker.py").write_text("VALUE = 1\n", encoding="utf-8")
    core_api = (PROJECT_ROOT / "api").resolve()

    saved_path = list(sys.path)
    _clear_api_modules()
    sys.path.insert(0, str(plugin_dir))
    polluted_path = list(sys.path)
    try:
        # Simulate plugin code importing a regular api package before the
        # framework dispatcher loads its lazy handler.
        importlib.import_module("api")
        importlib.import_module("api.marker")
        assert Path(sys.modules["api"].__file__).resolve().parent == plugin_api.resolve()

        module = modules.import_module(str(plugin_dir / "probe.py"))

        resolved = [Path(entry).resolve() for entry in module.RESOLVED]
        assert core_api in resolved
        assert plugin_api.resolve() not in resolved
        assert module.HAS_CORE_SUBMODULE
        assert sys.path == polluted_path
    finally:
        sys.path[:] = saved_path
        _clear_api_modules()


def test_plugin_under_framework_root_cannot_shadow_core_api():
    plugin_name = f"pytest_syspath_{uuid.uuid4().hex[:8]}"
    plugins_root = PROJECT_ROOT / "usr" / "plugins"
    plugins_root.mkdir(parents=True, exist_ok=True)
    plugin_dir, plugin_api = _plugin_with_api_probe(plugins_root, plugin_name)
    core_api = (PROJECT_ROOT / "api").resolve()

    saved_path = list(sys.path)
    _clear_api_modules()
    sys.path.insert(0, str(plugin_dir))
    polluted_path = list(sys.path)
    try:
        module = modules.import_module(str(plugin_dir / "probe.py"))

        resolved = [Path(entry).resolve() for entry in module.RESOLVED]
        assert core_api in resolved
        assert plugin_api.resolve() not in resolved
        assert module.HAS_CORE_SUBMODULE
        assert sys.path == polluted_path
    finally:
        sys.path[:] = saved_path
        _clear_api_modules()
        shutil.rmtree(plugin_dir, ignore_errors=True)


def test_plugin_api_remains_usable_after_dynamic_import(tmp_path):
    plugin_dir, plugin_api = _plugin_with_api_probe(tmp_path)
    (plugin_api / "marker.py").write_text("VALUE = 1\n", encoding="utf-8")

    saved_path = list(sys.path)
    _clear_api_modules()
    sys.path.insert(0, str(plugin_dir))
    polluted_path = list(sys.path)
    try:
        importlib.import_module("api")
        importlib.import_module("api.marker")
        plugin_api_module = sys.modules["api"]
        plugin_marker_module = sys.modules["api.marker"]

        modules.import_module(str(plugin_dir / "probe.py"))

        assert sys.path == polluted_path
        assert sys.modules["api"] is plugin_api_module
        assert sys.modules["api.marker"] is plugin_marker_module
        assert importlib.import_module("api.marker").VALUE == 1
    finally:
        sys.path[:] = saved_path
        _clear_api_modules()


def test_failed_dynamic_import_restores_sys_path(tmp_path):
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    probe = plugin_dir / "broken.py"
    probe.write_text("raise RuntimeError('boom')\n", encoding="utf-8")

    saved_path = list(sys.path)
    sys.path.insert(0, str(plugin_dir))
    polluted_path = list(sys.path)
    try:
        try:
            modules.import_module(str(probe))
        except RuntimeError as exc:
            assert str(exc) == "boom"
        else:
            raise AssertionError("expected the probe import to fail")

        assert sys.path == polluted_path
    finally:
        sys.path[:] = saved_path
