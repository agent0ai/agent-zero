# secrets.py DOX

## Purpose

- Own the `secrets.py` helper module.
- This module loads, aliases, masks, and streams secret values safely.
- Keep this file-level DOX profile synchronized with `secrets.py` because this directory is intentionally flat.

## Ownership

- `secrets.py` owns the runtime implementation.
- `secrets.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `EnvLine` (no explicit base class)
- `StreamingSecretsFilter` (no explicit base class)
  - `process_chunk(self, chunk: str) -> str`
  - `finalize(self) -> str`
- `SecretsManager` (no explicit base class)
  - `get_instance(cls, *secrets_files) -> 'SecretsManager'`
  - `read_secrets_raw(self) -> str`
  - `load_secrets(self) -> Dict[str, str]`
  - `save_secrets(self, secrets_content: str)`
  - `save_secrets_with_merge(self, submitted_content: str)`
  - `get_keys(self) -> List[str]`
  - `get_secrets_for_prompt(self) -> str`
  - `create_streaming_filter(self) -> 'StreamingSecretsFilter'`
- Top-level functions:
- `alias_for_key(key: str, placeholder: str=...) -> str`
- `get_secrets_manager(context: 'AgentContext|None'=...) -> SecretsManager`
- `get_project_secrets_manager(project_name: str, merge_with_global: bool=...) -> SecretsManager`
- `get_default_secrets_manager() -> SecretsManager`
- Notable constants/configuration names: `ALIAS_PATTERN`, `DEFAULT_SECRETS_FILE`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- The agent-facing `get_secrets_manager` masks and unpacks values from `usr/.env`, the global `usr/secrets.env`, and the active project's `secrets.env`; `get_default_secrets_manager` remains scoped to the single writable `usr/secrets.env` file.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, WebSocket state, settings/state persistence, secret handling.
- Imported dependency areas include: `dataclasses`, `dotenv.parser`, `helpers`, `helpers.errors`, `helpers.extension`, `io`, `os`, `re`, `threading`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `key.upper`, `placeholder.format`, `SecretsManager.get_instance`, `self._replace_full_values`, `self._longest_suffix_prefix`, `threading.RLock`, `join`, `files.write_file`, `self._invalidate_all_caches`, `self.load_secrets`, `self.read_secrets_raw`, `self.parse_env_lines`, `self._serialize_env_lines`, `StreamingSecretsFilter`, `re.sub`, `self.parse_env_content`, `parse_stream`, `AgentContext.current`, `projects.get_context_project_name`, `files.get_abs_path`, `dotenv.get_dotenv_file_path`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_plugin_scan_prompt.py`
  - `tests/test_print_style.py`
  - `tests/test_time_travel.py`

## Child DOX Index

No child DOX files.
