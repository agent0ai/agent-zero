# server_startup.py DOX

## Purpose

- Own the `server_startup.py` helper module.
- This module runs Uvicorn startup with health checks and retry tracking.
- Keep this file-level DOX profile synchronized with `server_startup.py` because this directory is intentionally flat.

## Ownership

- `server_startup.py` owns the runtime implementation.
- `server_startup.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `StartupConfig` (no explicit base class)
  - `from_env(cls) -> 'StartupConfig'`
- `StartupStageRecord` (no explicit base class)
- `StartupMonitor` (no explicit base class)
  - `mark(self, stage: str, detail: str | None=...) -> None`
  - `stage(self, stage: str, detail: str | None=...) -> Iterator[None]`
  - `lifespan(self)`
  - `attach_server(self, server: uvicorn.Server) -> None`
  - `start_watchdog(self) -> None`
  - `mark_ready(self, source: str=...) -> None`
  - `is_ready(self) -> bool`
  - `close(self) -> None`
- `_UvicornServerWrapper` (no explicit base class)
  - `shutdown(self) -> None`
- Top-level functions:
- `_env_int(name: str, default: int, minimum: int=...) -> int`
- `_env_float(name: str, default: float, minimum: float=...) -> float`
- `get_health_probe_host(bind_host: str) -> str`
- `run_uvicorn_with_retries(host: str, port: int, build_asgi_app: Callable[[StartupMonitor], object], flush_callback: Callable[[str], None], access_log: bool=..., log_level: str=..., ws: str=..., startup_config: StartupConfig | None=...) -> None`
- `_run_server_attempt(host: str, health_host: str, port: int, startup_monitor: StartupMonitor, build_asgi_app: Callable[[StartupMonitor], object], flush_callback: Callable[[str], None], access_log: bool, log_level: str, ws: str) -> bool`
- `wait_for_health(host: str, port: int, startup_monitor: StartupMonitor) -> None`
- `_serve_uvicorn(server: uvicorn.Server) -> None`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, network calls, subprocess/runtime control, settings/state persistence.
- Imported dependency areas include: `asyncio`, `collections`, `contextlib`, `dataclasses`, `faulthandler`, `helpers`, `helpers.print_style`, `os`, `sys`, `threading`, `time`, `typing`, `urllib.request`, `uvicorn`.

## Key Concepts

- Important called helpers/classes observed in the source: `dataclass`, `get_health_probe_host`, `PrintStyle.debug`, `RuntimeError`, `startup_monitor.start_watchdog`, `server.config.get_loop_factory`, `cls`, `time.monotonic`, `deque`, `threading.Event`, `threading.RLock`, `self.mark`, `threading.Thread`, `self._watchdog_thread.start`, `self._ready.is_set`, `self.snapshot`, `PrintStyle.error`, `join`, `StartupConfig.from_env`, `StartupMonitor`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
