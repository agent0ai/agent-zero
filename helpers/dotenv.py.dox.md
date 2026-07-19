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
- `save_dotenv_value(key: str, value: str)`
- Notable constants/configuration names: `KEY_AUTH_LOGIN`, `KEY_AUTH_PASSWORD`, `KEY_RFC_PASSWORD`, `KEY_ROOT_PASSWORD`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, secret handling.
- Imported dependency areas include: `dotenv`, `files`, `os`, `re`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `_load_dotenv`, `get_abs_path`, `os.getenv`, `get_dotenv_file_path`, `load_dotenv`, `os.path.isfile`, `f.readlines`, `f.seek`, `f.writelines`, `f.truncate`, `f.write`, `re.match`.
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

## Child DOX Index

No child DOX files.
