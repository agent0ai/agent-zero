# file_tree.py DOX

## Purpose

- Own the `file_tree.py` helper module.
- This module renders bounded file-tree summaries for prompts and UI surfaces.
- Keep this file-level DOX profile synchronized with `file_tree.py` because this directory is intentionally flat.

## Ownership

- `file_tree.py` owns the runtime implementation.
- `file_tree.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `_TreeEntry` (no explicit base class)
  - `as_dict(self) -> dict[str, Any]`
- Top-level functions:
- `_from_timestamp(timestamp: float) -> datetime`
- `file_tree(relative_path: str, max_depth: int=..., max_lines: int=..., folders_first: bool=..., max_folders: int=..., max_files: int=..., sort: tuple[Literal['name', 'created', 'modified'], Literal['asc', 'desc']]=..., ignore: str | None=..., output_mode: Literal['string', 'flat', 'nested']=...) -> str | list[dict]`: Render a directory tree relative to the repository base path.
- `_normalize_relative_path(path: str) -> str`
- `_directory_has_visible_entries(directory: str, root_abs_path: str, ignore_spec: PathSpec, cache: dict[str, bool], max_depth_remaining: int) -> bool`
- `_create_summary_comment(parent: _TreeEntry, noun: str, count: int) -> _TreeEntry`
- `_create_global_limit_comment(parent: _TreeEntry, hidden_children: Sequence[_TreeEntry]) -> _TreeEntry`
- `_create_folder_unprocessed_comment(folder_node: _TreeEntry, folder_path: str, abs_root: str, ignore_spec: Optional[PathSpec]) -> Optional[_TreeEntry]`
- `_prune_to_visible(node: _TreeEntry, visible_ids: set[int]) -> None`
- `_mark_last_flags(node: _TreeEntry) -> None`
- `_refresh_render_metadata(node: _TreeEntry) -> None`
- `_resolve_ignore_patterns(ignore: str | None, root_abs_path: str) -> Optional[PathSpec]`
- `_list_directory_children(directory: str, root_abs_path: str, ignore_spec: Optional[PathSpec], max_depth_remaining: int, cache: dict[str, bool]) -> tuple[list[os.DirEntry], list[os.DirEntry]]`
- `_apply_sorting_and_limits(folders: list[_TreeEntry], files: list[_TreeEntry], folders_first: bool, sort: tuple[str, str], max_folders: int | None, max_files: int | None, directory_node: _TreeEntry) -> list[_TreeEntry]`
- `_format_line(node: _TreeEntry) -> str`
- `_build_tree_items_flat(items: Sequence[_TreeEntry]) -> list[dict]`
- `_to_nested_structure(items: Sequence[_TreeEntry]) -> list[dict]`
- `_iter_depth_first(items: Sequence[_TreeEntry]) -> Iterable[_TreeEntry]`
- Notable constants/configuration names: `SORT_BY_NAME`, `SORT_BY_CREATED`, `SORT_BY_MODIFIED`, `SORT_ASC`, `SORT_DESC`, `OUTPUT_MODE_STRING`, `OUTPUT_MODE_FLAT`, `OUTPUT_MODE_NESTED`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, subprocess/runtime control, WebSocket state.
- Imported dependency areas include: `__future__`, `collections`, `dataclasses`, `datetime`, `helpers`, `helpers.localization`, `os`, `pathspec`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `dataclass`, `datetime.fromtimestamp`, `files_helper.get_abs_path`, `files_helper.get_abs_path_dockerized`, `_resolve_ignore_patterns`, `os.stat`, `_TreeEntry`, `deque`, `queue.clear`, `_mark_last_flags`, `_refresh_render_metadata`, `path.replace`, `normalized.startswith`, `join`, `_create_global_limit_comment`, `ignore.startswith`, `PathSpec.from_lines`, `segments.reverse`, `os.path.exists`, `FileNotFoundError`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_file_tree_visualize.py`
  - `tests/test_skills_runtime.py`

## Child DOX Index

No child DOX files.
