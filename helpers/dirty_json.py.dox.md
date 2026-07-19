# dirty_json.py DOX

## Purpose

- Own the `dirty_json.py` helper module.
- This module parses and serializes relaxed JSON-like model output.
- Keep this file-level DOX profile synchronized with `dirty_json.py` because this directory is intentionally flat.

## Ownership

- `dirty_json.py` owns the runtime implementation.
- `dirty_json.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `DirtyJson` (no explicit base class)
  - `parse_string(json_string)`
  - `parse(self, json_string)`
  - `feed(self, chunk)`
  - `get_start_pos(self, input_str: str) -> int`
- Top-level functions:
- `try_parse(json_string: str)`
- `parse(json_string: str)`
- `stringify(obj, **kwargs)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, settings/state persistence.
- Imported dependency areas include: `json`.

## Key Concepts

- Important called helpers/classes observed in the source: `DirtyJson.parse_string`, `json.dumps`, `json.loads`, `self._reset`, `self.stack.pop`, `DirtyJson`, `parser.parse`, `self.get_start_pos`, `self._parse`, `self._advance`, `self._skip_whitespace`, `self._parse_object_content`, `self._parse_array_content`, `self._skip_padding_from`, `self._looks_like_missing_comma_before_key`, `result.strip`, `self.current_char.isspace`, `self._parse_value`, `self._continue_parsing`, `self._parse_object`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_dirty_json.py`
  - `tests/test_projects.py`

## Child DOX Index

No child DOX files.
