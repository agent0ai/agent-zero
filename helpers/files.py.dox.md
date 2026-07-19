# files.py DOX

## Purpose

- Own the `files.py` helper module.
- This module owns repository/user path helpers and file read/write/parsing primitives.
- Keep this file-level DOX profile synchronized with `files.py` because this directory is intentionally flat.

## Ownership

- `files.py` owns the runtime implementation.
- `files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `VariablesPlugin` (`ABC`)
  - `get_variables(self, file: str, backup_dirs: list[str] | None=..., **kwargs) -> dict[str, Any]`
- Top-level functions:
- `load_plugin_variables(file: str, backup_dirs: list[str] | None=..., **kwargs) -> dict[str, Any]`
- `parse_file(_filename: str, _directories: list[str] | None=..., _encoding=..., **kwargs)`
- `read_prompt_file(_file: str, _directories: list[str] | None=..., _encoding=..., **kwargs)`
- `evaluate_text_conditions(_content: str, **kwargs)`
- `read_file(relative_path: str, encoding=...)`
- `read_file_json(relative_path: str, encoding=...)`
- `read_file_yaml(relative_path: str, encoding=...)`
- `read_file_bin(relative_path: str)`
- `read_file_base64(relative_path)`
- `is_probably_binary_bytes(data: bytes, threshold: float=...) -> bool`: Binary detection.
- `is_probably_binary_file(file_path: str, sample_size: int=..., threshold: float=...) -> bool`: Binary detection by reading only the first ~sample_size bytes of a file.
- `replace_placeholders_text(_content: str, **kwargs)`
- `replace_placeholders_json(_content: str, **kwargs)`
- `replace_placeholders_dict(_content: dict, **kwargs)`
- `process_includes(_content: str, _directories: list[str], _source_file: str=..., _source_dir: str=..., **kwargs)`
- `_get_dirs_after(_directories: list[str], _source_dir: str) -> list[str]`: Return directories after _source_dir in the priority list.
- `find_file_in_dirs(_filename: str, _directories: list[str])`: This function searches for a filename in a list of directories in order.
- `get_unique_filenames_in_dirs(dir_paths: list[str], pattern: str=..., type: Literal['file', 'dir', 'any']=...)`
- `find_existing_paths_by_pattern(pattern: str)`
- `remove_code_fences(text)`
- `is_full_json_template(text)`
- `write_file(relative_path: str, content: str, encoding: str=...)`
- `delete_file(relative_path: str)`
- `write_file_bin(relative_path: str, content: bytes)`
- `write_file_base64(relative_path: str, content: str)`
- `delete_dir(relative_path: str)`
- `move_dir(old_path: str, new_path: str)`
- `move_dir_safe(src, dst, rename_format=...)`
- `create_dir_safe(dst, rename_format=...)`
- `create_dir(relative_path: str)`
- Notable constants/configuration names: `AGENTS_DIR`, `PLUGINS_DIR`, `PROJECTS_DIR`, `EXTENSIONS_DIR`, `USER_DIR`, `TEMP_DIR`, `API_DIR`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, subprocess/runtime control, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `abc`, `base64`, `fnmatch`, `glob`, `helpers`, `helpers.strings`, `json`, `mimetypes`, `os`, `re`, `shutil`, `simpleeval`, `tempfile`, `typing`, `zipfile`.

## Key Concepts

- Important called helpers/classes observed in the source: `os.path.dirname`, `os.path.abspath`, `find_file_in_dirs`, `is_full_json_template`, `remove_code_fences`, `evaluate_text_conditions`, `replace_placeholders_text`, `process_includes`, `re.compile`, `_process`, `get_abs_path`, `is_probably_binary_bytes`, `replace_value`, `re.sub`, `os.path.normpath`, `FileNotFoundError`, `result.sort`, `glob.glob`, `matches.sort`, `re.fullmatch`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_default_prompt_budget.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_file_tree_visualize.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_image_get_security.py`

## Child DOX Index

No child DOX files.
