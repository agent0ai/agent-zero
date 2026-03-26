
import re, os, importlib, importlib.util, inspect, sys
from types import ModuleType
from typing import Any, Type, TypeVar
from helpers.files import get_abs_path
from fnmatch import fnmatch


T = TypeVar("T")  # Define a generic type variable


def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace(".py", "")

    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")

    module = importlib.util.module_from_spec(spec)
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