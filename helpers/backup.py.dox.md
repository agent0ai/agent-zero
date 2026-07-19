# backup.py DOX

## Purpose

- Own the `backup.py` helper module.
- This module builds, inspects, previews, tests, and restores Agent Zero backup archives.
- Keep this file-level DOX profile synchronized with `backup.py` because this directory is intentionally flat.

## Ownership

- `backup.py` owns the runtime implementation.
- `backup.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupService` (no explicit base class)
  - `get_default_backup_metadata(self) -> Dict[str, Any]`
  - `async test_patterns(self, metadata: Dict[str, Any], max_files: Optional[int]=...) -> List[Dict[str, Any]]`
  - `async create_backup(self, include_patterns: List[str], exclude_patterns: List[str], include_hidden: bool=..., backup_name: str=...) -> str`
  - `async inspect_backup(self, backup_file) -> Dict[str, Any]`
  - `async preview_restore(self, backup_file, restore_include_patterns: Optional[List[str]]=..., restore_exclude_patterns: Optional[List[str]]=..., overwrite_policy: str=..., clean_before_restore: bool=..., user_edited_metadata: Optional[Dict[str, Any]]=...) -> Dict[str, Any]`
  - `async restore_backup(self, backup_file, restore_include_patterns: Optional[List[str]]=..., restore_exclude_patterns: Optional[List[str]]=..., overwrite_policy: str=..., clean_before_restore: bool=..., user_edited_metadata: Optional[Dict[str, Any]]=...) -> Dict[str, Any]`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, settings/state persistence, secret handling.
- Imported dependency areas include: `datetime`, `helpers`, `helpers.localization`, `helpers.print_style`, `json`, `os`, `pathspec`, `platform`, `tempfile`, `typing`, `zipfile`.
- `test_patterns(..., max_files=None)` is the unlimited scan mode. UI preview and dry-run callers may pass bounded limits, but real backup creation and restore clean-before-restore must use unlimited matching so archives and cleanup are not silently truncated.
- Default backup metadata includes persistent `/usr` data but excludes Time Travel shadow history under `usr/.time_travel/**`.

## Key Concepts

- Important called helpers/classes observed in the source: `self._get_agent_zero_version`, `files.get_abs_path`, `Localization.get.now_iso`, `self._get_default_patterns`, `self._parse_patterns`, `self.agent_zero_root.rstrip`, `patterns.split`, `join`, `file_path.lstrip`, `backed_up_agent_root.rstrip`, `current_agent_root.rstrip`, `self._patterns_to_string`, `self._get_explicit_patterns`, `tempfile.mkdtemp`, `os.path.join`, `self._translate_patterns`, `git.get_git_info`, `line.strip`, `line.startswith`, `getpass.getuser`.
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
  - `tests/test_self_update_tag_filter.py`

## Child DOX Index

No child DOX files.
