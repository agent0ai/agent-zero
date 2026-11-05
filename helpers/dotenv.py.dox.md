# dotenv.py DOX

## Purpose

- Own the `dotenv.py` helper module.
- This module loads and updates `.env` configuration values.
- Keep this file-level DOX profile synchronized with `dotenv.py` because this directory is intentionally flat.

## Ownership

- `dotenv.py` owns the runtime implementation.
- `dotenv.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `load_dotenv()`
- `get_dotenv_file_path()`
- `get_dotenv_value(key: str, default: Any=...)`
- `save_dotenv_value(key: str, value: str, reload_env: bool=...)`
- Notable constants/configuration names: `KEY_AUTH_LOGIN`, `KEY_AUTH_PASSWORD`, `KEY_RFC_PASSWORD`, `KEY_ROOT_PASSWORD`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, secret handling.
- Imported dependency areas include: `dotenv`, `files`, `os`, `re`, `typing`.
- `save_dotenv_value(..., reload_env=False)` updates the persisted file without changing the running process environment.
- `usr/.env` is always written as UTF-8: loaders (python-dotenv) read it as UTF-8 regardless of the platform locale, and Windows process locales (for example cp1252 or cp936) would otherwise corrupt non-ASCII values and crash startup with `UnicodeDecodeError`.
- `_read_env_lines` reads the file as UTF-8 and, when a legacy file written by a locale-encoded save cannot be decoded, falls back to `locale.getencoding()` with replacement characters so the file is healed to UTF-8 on the next save instead of crashing.

## Key Concepts

- Important called helpers/classes observed in the source: `_load_dotenv`, `get_abs_path`, `os.getenv`, `get_dotenv_file_path`, `load_dotenv`, `os.path.isfile`, `locale.getencoding`, `_read_env_lines`, `f.write`, `f.writelines`, `re.match`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/email_parser_test.py`
  - `tests/test_model_config_api_keys.py`
  - `tests/test_timezone_regressions.py`
  - `tests/test_dotenv_encoding.py` (UTF-8 write round-trip and legacy locale-encoded file healing)
  - `tests/test_migration_dotenv.py`
  - `tests/test_backup_large_archives.py`

## Child DOX Index

No child DOX files.
