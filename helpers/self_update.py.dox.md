# self_update.py DOX

## Purpose

- Own the `self_update.py` helper module.
- This module manages self-update status, scheduling, tag selection, and durable scripts.
- Keep this file-level DOX profile synchronized with `self_update.py` because this directory is intentionally flat.

## Ownership

- `self_update.py` owns the runtime implementation.
- `self_update.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `PendingUpdateConfig` (`TypedDict`)
- `UpdateStatus` (`TypedDict`)
- `SelectorTagOption` (`TypedDict`)
- Top-level functions:
- `_now_iso() -> str`
- `get_update_file_path() -> Path`
- `get_status_file_path() -> Path`
- `get_log_file_path() -> Path`
- `get_durable_exe_dir() -> Path`
- `get_durable_self_update_manager_path() -> Path`
- `_load_yaml(path: Path) -> dict[str, Any] | None`
- `_write_yaml(path: Path, payload: dict[str, Any]) -> None`
- `load_pending_update() -> PendingUpdateConfig | None`
- `load_last_status() -> UpdateStatus | None`
- `get_log_text() -> str`
- `get_default_backup_dir(repo_dir: str | Path | None=...) -> Path`
- `get_repo_dir(repo_dir: str | Path | None=...) -> Path`
- `get_repo_self_update_manager_path(repo_dir: str | Path | None=...) -> Path`
- `_get_official_remote_url() -> str`
- `_run_git_raw(*args) -> str`
- `_run_git(repo_dir: str | Path, *args) -> str`
- `_normalize_describe_to_version(describe: str) -> str`
- `_split_describe_version(describe: str) -> tuple[str, int]`
- `_is_latest_selector_tag(tag: str) -> bool`
- `_get_tag_release_time_in_repo(repo_dir: str | Path, tag: str) -> str`
- `get_repo_version_info(repo_dir: str | Path | None=...) -> dict[str, str]`
- `_sanitize_filename(name: str, default_name: str) -> str`
- `_slugify_version(text: str) -> str`
- `build_default_backup_name(current_version: str, target_tag: str | None=...) -> str`
- `_resolve_backup_path(backup_path: str, repo_dir: str | Path | None=...) -> Path`
- `_is_excluded_self_update_branch(branch: str) -> bool`
- `_sort_branch_names(branches: list[str]) -> list[str]`
- `_get_remote_branch_names() -> list[str]`
- `_get_local_origin_branch_names(repo_dir: str | Path | None=...) -> list[str]`
- Notable constants/configuration names: `OFFICIAL_REPO_AUTHOR`, `OFFICIAL_REPO_NAME`, `BRANCH_OPTIONS`, `SUPPORTED_BRANCHES`, `BACKUP_CONFLICT_POLICIES`, `MIN_SELECTOR_VERSION`, `REMOTE_BRANCH_TAG_CACHE_TTL_SECONDS`, `REMOTE_BRANCH_LIST_CACHE_TTL_SECONDS`, `UPDATE_FILE_PATH`, `STATUS_FILE_PATH`, `LOG_FILE_PATH`, `DURABLE_EXE_DIR`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, subprocess/runtime control, settings/state persistence.
- Imported dependency areas include: `__future__`, `datetime`, `helpers`, `helpers.localization`, `os`, `pathlib`, `re`, `subprocess`, `tempfile`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `Path`, `Localization.get.now_iso`, `yaml.loads`, `path.parent.mkdir`, `path.write_text`, `_load_yaml`, `get_log_file_path`, `path.read_text`, `subprocess.run`, `completed.stdout.strip`, `re.fullmatch`, `describe.strip`, `tag.strip`, `get_repo_dir`, `_run_git`, `_normalize_describe_to_version`, `strip`, `re.sub.strip`, `Localization.get.now.strftime`, `path.resolve`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_office_document_store.py`
  - `tests/test_self_update_tag_filter.py`

## Child DOX Index

No child DOX files.
