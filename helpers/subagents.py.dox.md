# subagents.py DOX

## Purpose

- Own the `subagents.py` helper module.
- This module discovers, merges, loads, and saves agent profile definitions.
- Keep this file-level DOX profile synchronized with `subagents.py` because this directory is intentionally flat.

## Ownership

- `subagents.py` owns the runtime implementation.
- `subagents.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `SubAgentListItem` (`BaseModel`)
  - `post_validator(self)`
- `SubAgent` (`SubAgentListItem`)
- Top-level functions:
- `get_agents_list(project_name: str | None=...) -> list[SubAgentListItem]`
- `get_agents_dict(project_name: str | None=...) -> dict[str, SubAgentListItem]`
- `_get_agents_list_from_dir(dir: str, origin: Origin) -> dict[str, SubAgentListItem]`
- `load_agent_data(name: str, project_name: str | None=...) -> SubAgent`
- `save_agent_data(name: str, subagent: SubAgent) -> None`
- `delete_agent_data(name: str) -> None`
- `_load_agent_data_from_dir(dir: str, name: str, origin: Origin) -> SubAgent | None`
- `_merge_agents(base: SubAgent | None, override: SubAgent | None) -> SubAgent | None`
- `_merge_agent_list_items(base: SubAgentListItem, override: SubAgentListItem) -> SubAgentListItem`
- `get_agents_roots() -> list[str]`
- `get_all_agents_list() -> list[dict[str, str]]`
- `_merge_origins(base: list[Origin], override: list[Origin]) -> list[Origin]`
- `get_default_promp_file_names() -> list[str]`
- `get_available_agents_dict(project_name: str | None) -> dict[str, SubAgentListItem]`
- `get_paths(agent: 'Agent|None', *subpaths, must_exist_completely: bool=..., include_project: bool=..., include_user: bool=..., include_default: bool=..., include_plugins: bool=..., default_root: str=...) -> list[str]`: Returns list of file paths for the given agent and subpaths, searched in order of priority:
- Notable constants/configuration names: `GLOBAL_DIR`, `USER_DIR`, `DEFAULT_AGENTS_DIR`, `USER_AGENTS_DIR`, `PATHS_CACHE_AREA`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, plugin state, settings/state persistence.
- Imported dependency areas include: `helpers`, `json`, `os`, `pydantic`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `cache.toggle_area`, `model_validator`, `_get_agents_list_from_dir`, `plugins.get_enabled_plugin_paths`, `_merge_agent_dicts`, `files.get_subdirectories`, `_load_agent_data_from_dir`, `_merge_agent`, `files.write_file`, `files.delete_dir`, `SubAgent`, `SubAgentListItem`, `files.find_existing_paths_by_pattern`, `get_agents_roots`, `files.list_files`, `get_agents_dict`, `cache.determine_cache_key`, `cache.add`, `projects.get_project_meta`, `FileNotFoundError`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_skills_runtime.py`

## Child DOX Index

No child DOX files.
