# modules.py DOX

## Purpose

- Own the `modules.py` helper module.
- This module imports modules and classes dynamically with namespace cache control.
- Keep this file-level DOX profile synchronized with `modules.py` because this directory is intentionally flat.

## Ownership

- `modules.py` owns the runtime implementation.
- `modules.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `import_module(file_path: str) -> ModuleType`
- `load_classes_from_folder(folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool=...) -> list[Type[T]]`
- `load_classes_from_file(file: str, base_class: type[T], one_per_file: bool=...) -> list[type[T]]`
- `purge_namespace(namespace: str)`
- Private helpers: `_framework_import_path()`, `_pin_framework_namespaces()`, `_is_framework_package(module, name)`, `_is_framework_namespace_name(name)`, `_snapshot_framework_modules()`, `_restore_framework_modules(snapshot)`.
- Notable constants/configuration names: `T`, `FRAMEWORK_ROOT`, `FRAMEWORK_NAMESPACES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Dynamic imports run with the framework root first in `sys.path` and pin framework namespace packages (`api`, `helpers`, `plugins`, `tools`, `extensions`) so a plugin directory earlier in `sys.path` cannot shadow core packages. During the import, a cached same-named regular package outside the framework is replaced and its submodules are purged. The original `sys.path` and the previous framework namespace `sys.modules` entries (including a plugin's own `api.*` packages) are restored even when the import fails.
- Observed side-effect areas: filesystem reads, filesystem deletion, temporary `sys.path` reordering, scoped `sys.modules` namespace pinning with restore.
- Imported dependency areas include: `fnmatch`, `helpers.files`, `importlib`, `importlib.util`, `inspect`, `os`, `re`, `sys`, `types`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `TypeVar`, `get_abs_path`, `os.path.basename.replace`, `importlib.util.spec_from_file_location`, `importlib.util.module_from_spec`, `spec.loader.exec_module`, `import_module`, `inspect.getmembers`, `to_delete.sort`, `importlib.invalidate_caches`, `ImportError`, `os.path.join`, `os.path.basename`, `issubclass`, `os.listdir`, `name.startswith`, `n.count`, `fnmatch`, `file_name.endswith`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_plugin_syspath_isolation.py`
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_docker_release_plan.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_file_tree_visualize.py`
  - `tests/test_git_version_label.py`
  - `tests/test_mcp_handler_multimodal.py`
  - `tests/test_memory_quality.py`

## Child DOX Index

No child DOX files.
