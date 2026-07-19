# file_browser.py DOX

## Purpose

- Own the `file_browser.py` helper module.
- This module builds safe file-browser views over allowed filesystem roots.
- Keep this file-level DOX profile synchronized with `file_browser.py` because this directory is intentionally flat.

## Ownership

- `file_browser.py` owns the runtime implementation.
- `file_browser.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `FileBrowser` (no explicit base class)
  - `save_file_b64(self, current_path: str, filename: str, base64_content: str)`
  - `save_files(self, files: List, current_path: str=...) -> Tuple[List[str], List[str]]`
  - `delete_file(self, file_path: str) -> bool`
  - `rename_item(self, file_path: str, new_name: str) -> bool`
  - `create_folder(self, parent_path: str, folder_name: str) -> bool`
  - `save_text_file(self, file_path: str, content: str) -> bool`
  - `get_files(self, current_path: str=...) -> Dict`
  - `get_full_path(self, file_path: str, allow_dir: bool=...) -> str`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, subprocess/runtime control, settings/state persistence.
- Imported dependency areas include: `base64`, `datetime`, `helpers`, `helpers.localization`, `helpers.print_style`, `helpers.security`, `os`, `pathlib`, `shutil`, `subprocess`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `Path`, `files.get_abs_path`, `self._get_file_extension`, `file.seek`, `file.tell`, `resolve`, `os.makedirs`, `os.path.exists`, `full_path.with_name`, `new_path.exists`, `os.rename`, `target_dir.exists`, `filename.rsplit.lower`, `subprocess.run`, `result.stdout.strip.split`, `self._get_files_via_ls`, `files.exists`, `ValueError`, `str.startswith`, `file.write`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`
  - `tests/test_office_document_store.py`

## Child DOX Index

No child DOX files.
