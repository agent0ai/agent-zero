
import re, os, importlib, importlib.machinery, importlib.util, inspect, sys, threading
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Type, TypeVar
from helpers.files import get_abs_path
from fnmatch import fnmatch


T = TypeVar("T")  # Define a generic type variable

FRAMEWORK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMEWORK_NAMESPACES = ("api", "helpers", "plugins", "tools", "extensions")
_sys_path_lock = threading.RLock()


def _is_framework_package(module: ModuleType, name: str) -> bool:
    paths = getattr(module, "__path__", None)
    if paths is None:
        return False
    expected = os.path.normcase(
        os.path.abspath(os.path.join(FRAMEWORK_ROOT, name))
    )
    return {os.path.normcase(os.path.abspath(path)) for path in paths} == {expected}


def _is_framework_namespace_name(module_name: str) -> bool:
    return any(
        module_name == namespace or module_name.startswith(namespace + ".")
        for namespace in FRAMEWORK_NAMESPACES
    )


def _snapshot_framework_modules() -> dict[str, ModuleType]:
    return {
        module_name: module
        for module_name, module in list(sys.modules.items())
        if _is_framework_namespace_name(module_name)
    }


def _restore_framework_modules(snapshot: dict[str, ModuleType]):
    for module_name in [
        name for name in list(sys.modules) if _is_framework_namespace_name(name)
    ]:
        if module_name not in snapshot:
            del sys.modules[module_name]
    sys.modules.update(snapshot)


def _pin_framework_namespaces():
    """Make framework namespace packages resolve before same-named plugin packages.

    Framework source directories (``api``, ``helpers``, ...) are namespace
    packages. A regular package with the same name anywhere in ``sys.path``
    wins over a namespace portion, even when the framework root comes first.
    Registering the framework portion explicitly prevents plugin directories
    from shadowing core packages during dynamic imports.
    """
    for name in FRAMEWORK_NAMESPACES:
        package_dir = os.path.join(FRAMEWORK_ROOT, name)
        if not os.path.isdir(package_dir):
            continue
        existing = sys.modules.get(name)
        if existing is not None and _is_framework_package(existing, name):
            continue
        if existing is not None:
            for submodule_name in [
                module_name
                for module_name in sys.modules
                if module_name.startswith(name + ".")
            ]:
                del sys.modules[submodule_name]
        spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
        spec.submodule_search_locations = [package_dir]
        sys.modules[name] = importlib.util.module_from_spec(spec)


@contextmanager
def _framework_import_path():
    """Temporarily prioritize the framework root during a dynamic import.

    Plugin directories may be present earlier in ``sys.path`` from plugin code
    or installation scripts. During the import they must not shadow framework
    packages such as ``api``, ``helpers`` or ``plugins``. Both the original
    path and the previous framework namespace modules (including a plugin's own
    ``api.*`` packages) are restored afterwards, so the change never leaks past
    the import.
    """
    with _sys_path_lock:
        original_path = list(sys.path)
        original_modules = _snapshot_framework_modules()
        try:
            _pin_framework_namespaces()
            if not sys.path or sys.path[0] != FRAMEWORK_ROOT:
                while FRAMEWORK_ROOT in sys.path:
                    sys.path.remove(FRAMEWORK_ROOT)
                sys.path.insert(0, FRAMEWORK_ROOT)
            yield
        finally:
            sys.path[:] = original_path
            _restore_framework_modules(original_modules)


def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace(".py", "")

    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")

    module = importlib.util.module_from_spec(spec)
    with _framework_import_path():
        spec.loader.exec_module(module)
    return module


def load_classes_from_folder(
    folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool = True
) -> list[Type[T]]:
    classes = []
    abs_folder = get_abs_path(folder)

    # Get all .py files in the folder that match the pattern, sorted alphabetically
    py_files = sorted(
        [
            file_name
            for file_name in os.listdir(abs_folder)
            if fnmatch(file_name, name_pattern) and file_name.endswith(".py")
        ]
    )

    # Iterate through the sorted list of files
    for file_name in py_files:
        file_path = os.path.join(abs_folder, file_name)
        # Use the new import_module function
        module = import_module(file_path)

        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)

        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break

    return classes


def load_classes_from_file(
    file: str, base_class: type[T], one_per_file: bool = True
) -> list[type[T]]:
    classes = []
    # Use the new import_module function
    module = import_module(file)

    # Get all classes in the module
    class_list = inspect.getmembers(module, inspect.isclass)

    # Filter for classes that are subclasses of the given base_class
    # iterate backwards to skip imported superclasses
    for cls in reversed(class_list):
        if cls[1] is not base_class and issubclass(cls[1], base_class):
            classes.append(cls[1])
            if one_per_file:
                break

    return classes


def purge_namespace(namespace: str):
    to_delete = [
        name
        for name in sys.modules
        if name == namespace or name.startswith(namespace + ".")
    ]

    # delete deepest first just to be tidy
    to_delete.sort(key=lambda n: n.count("."), reverse=True)

    for name in to_delete:
        del sys.modules[name]

    importlib.invalidate_caches()
    return to_delete