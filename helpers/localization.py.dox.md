# localization.py DOX

## Purpose

- Own the `localization.py` helper module.
- This module loads and resolves localized UI/application text.
- Keep this file-level DOX profile synchronized with `localization.py` because this directory is intentionally flat.

## Ownership

- `localization.py` owns the runtime implementation.
- `localization.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Localization` (no explicit base class)
  - `get(cls, *args, **kwargs)`
  - `get_timezone(self) -> str`
  - `get_tzinfo(self)`
  - `get_offset_minutes(self) -> int`
  - `apply_process_timezone(self) -> None`
  - `now(self) -> datetime`
  - `now_iso(self, sep: str=..., timespec: str=...) -> str`
  - `localize_naive_datetime(self, dt: datetime) -> datetime`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, settings/state persistence.
- Imported dependency areas include: `datetime`, `helpers.dotenv`, `helpers.print_style`, `os`, `pytz`, `time`.

## Key Concepts

- Important called helpers/classes observed in the source: `get_dotenv_value`, `pytz.timezone`, `datetime.now`, `now_in_tz.utcoffset`, `self.now.isoformat`, `self.get_tzinfo`, `cls`, `self.set_timezone`, `self._compute_offset_minutes`, `self.apply_process_timezone`, `tzinfo.localize`, `PrintStyle.debug`, `save_dotenv_value`, `localtime_str.strip.replace`, `local_datetime_obj.astimezone`, `utc_dt.astimezone`, `local_datetime_obj.isoformat`, `dt.astimezone`, `local_dt.isoformat`, `time.tzset`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_timezone_regressions.py`

## Child DOX Index

No child DOX files.
