from __future__ import annotations

import importlib.util
import inspect
import os
from dataclasses import dataclass
from types import ModuleType
from typing import Iterable

from python.helpers.files import get_abs_path
from python.helpers.print_style import PrintStyle
from python.helpers.websocket import WebSocketHandler


@dataclass(frozen=True)
class NamespaceDiscovery:
    namespace: str
    handler_classes: tuple[type[WebSocketHandler], ...]
    source_files: tuple[str, ...]


def _to_namespace(entry_name: str) -> str:
    if entry_name == "_default":
        return "/"
    stripped = (
        entry_name[: -len("_handler")]
        if entry_name.endswith("_handler")
        else entry_name
    )
    if not stripped:
        raise ValueError(f"Invalid handler entry name: {entry_name!r}")
    return f"/{stripped}"


def _unique_module_name(file_path: str) -> str:
    # Use a stable, unique module name derived from the relative path to avoid
    # collisions when importing different files with the same basename.
    rel_path = os.path.relpath(file_path, get_abs_path("."))
    rel_no_ext = os.path.splitext(rel_path)[0]
    safe = "".join(ch if ch.isalnum() else "_" for ch in rel_no_ext)
    return f"a0_ws_ns_{safe}"


def _import_module(file_path: str) -> ModuleType:
    abs_path = get_abs_path(file_path)
    module_name = _unique_module_name(abs_path)
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _get_handler_classes(module: ModuleType) -> list[type[WebSocketHandler]]:
    discovered: list[type[WebSocketHandler]] = []
    for _name, cls in inspect.getmembers(module, inspect.isclass):
        if cls is WebSocketHandler:
            continue
        if not issubclass(cls, WebSocketHandler):
            continue
        if cls.__module__ != module.__name__:
            continue
        discovered.append(cls)
    return discovered


def discover_websocket_namespaces(
    *,
    handlers_folder: str = "python/websocket_handlers",
    include_root_default: bool = True,
) -> list[NamespaceDiscovery]:
    """
    Discover websocket namespaces from first-level filesystem entries.

    Supported entries:
    - File entry: `*_handler.py` defines an application namespace.
    - Folder entry: `<name>/` or `<name>_handler/` defines an application namespace and loads
      `*.py` files one level deep (ignores `__init__.py` and ignores deeper nesting).
    - Reserved root mapping: `_default.py` maps to `/` when `include_root_default=True`.
    """

    abs_folder = get_abs_path(handlers_folder)
    entries: list[NamespaceDiscovery] = []

    try:
        filenames = sorted(os.listdir(abs_folder))
    except FileNotFoundError:
        PrintStyle.warning(f"WebSocket handlers folder not found: {abs_folder}")
        return []

    for entry in filenames:
        entry_path = os.path.join(abs_folder, entry)

        # Folder entries define namespaces and can host multiple handler modules.
        if os.path.isdir(entry_path):
            if entry.startswith("__"):
                continue
            namespace = _to_namespace(entry)

            handler_classes: list[type[WebSocketHandler]] = []
            source_files: list[str] = []

            try:
                child_names = sorted(os.listdir(entry_path))
            except FileNotFoundError:
                continue

            for child in child_names:
                if not child.endswith(".py"):
                    continue
                if child == "__init__.py":
                    continue
                child_path = os.path.join(entry_path, child)
                if not os.path.isfile(child_path):
                    # Ignore deeper nesting.
                    continue

                module = _import_module(child_path)
                discovered = _get_handler_classes(module)
                if not discovered:
                    raise RuntimeError(
                        f"WebSocket handler module {child_path} defines no WebSocketHandler subclasses"
                    )
                if len(discovered) > 1:
                    raise RuntimeError(
                        f"WebSocket handler module {child_path} defines multiple WebSocketHandler subclasses: "
                        f"{', '.join(sorted(cls.__name__ for cls in discovered))}"
                    )
                handler_classes.append(discovered[0])
                source_files.append(child_path)

            if not handler_classes:
                PrintStyle.warning(
                    f"WebSocket handlers folder entry '{entry_path}' is empty; treating namespace '{namespace}' as unregistered"
                )
                continue

            entries.append(
                NamespaceDiscovery(
                    namespace=namespace,
                    handler_classes=tuple(handler_classes),
                    source_files=tuple(source_files),
                )
            )
            continue

        # File entries define namespaces.
        if not entry.endswith(".py"):
            continue
        if entry == "__init__.py":
            continue

        if entry == "_default.py":
            if not include_root_default:
                continue
            entry_name = "_default"
        else:
            if not entry.endswith("_handler.py"):
                continue
            entry_name = entry[: -len("_handler.py")]

        namespace = _to_namespace(entry_name)
        module_path = os.path.join(abs_folder, entry)

        module = _import_module(module_path)
        handler_classes = _get_handler_classes(module)
        if not handler_classes:
            raise RuntimeError(
                f"WebSocket handler module {module_path} defines no WebSocketHandler subclasses"
            )
        if len(handler_classes) > 1:
            raise RuntimeError(
                f"WebSocket handler module {module_path} defines multiple WebSocketHandler subclasses: "
                f"{', '.join(sorted(cls.__name__ for cls in handler_classes))}"
            )

        entries.append(
            NamespaceDiscovery(
                namespace=namespace,
                handler_classes=(handler_classes[0],),
                source_files=(module_path,),
            )
        )

    return entries


def iter_discovered_namespaces(discoveries: Iterable[NamespaceDiscovery]) -> list[str]:
    return [entry.namespace for entry in discoveries]
