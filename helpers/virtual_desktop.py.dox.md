# virtual_desktop.py DOX

## Purpose

- Own the `virtual_desktop.py` helper module.
- This module registers and proxies virtual desktop sessions.
- Keep this file-level DOX profile synchronized with `virtual_desktop.py` because this directory is intentionally flat.

## Ownership

- `virtual_desktop.py` owns the runtime implementation.
- `virtual_desktop.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `VirtualDesktopEndpoint` (no explicit base class)
- `VirtualDesktopRegistry` (no explicit base class)
  - `register(self, endpoint: VirtualDesktopEndpoint) -> None`
  - `unregister(self, token: str) -> None`
  - `proxy_for_token(self, token: str) -> VirtualDesktopEndpoint | None`
  - `resize(self, token: str, width: int, height: int) -> dict[str, Any]`
- Top-level functions:
- `register_session(token: str, host: str, port: int, owner: str=..., title: str=..., resize: ResizeCallback | None=...) -> None`
- `unregister_session(token: str) -> None`
- `proxy_for_token(token: str) -> VirtualDesktopEndpoint | None`
- `resize_session(token: str, width: int, height: int) -> dict[str, Any]`
- `get_registry() -> VirtualDesktopRegistry`
- `session_url(token: str, title: str=...) -> str`
- `collect_status() -> dict[str, Any]`
- `find_xpra_html_root() -> Path | None`
- `_package_installed(package: str) -> bool`
- `normalize_size(width: int | float | str, height: int | float | str, max_width: int=..., max_height: int=..., min_width: int=..., min_height: int=...) -> tuple[int, int]`
- `normalize_desktop_display_size(width: int | float | str, height: int | float | str, max_width: int=..., max_height: int=..., min_width: int=..., min_height: int=..., min_aspect_ratio: float=...) -> tuple[int, int]`
- `resize_display(display: int, width: int, height: int, max_width: int=..., max_height: int=..., window_class: str=..., keys: tuple[str, ...]=..., xauthority: str=..., home: str=...) -> dict[str, Any]`
- `_ensure_xrandr_mode(env: dict[str, str], width: int, height: int) -> None`
- `_select_xrandr_mode(env: dict[str, str], width: int, height: int) -> subprocess.CompletedProcess[str]`
- `_xrandr_output_modes(env: dict[str, str]) -> tuple[str, set[str]]`
- `current_display_size(display: int, xauthority: str=..., home: str=...) -> tuple[int, int] | None`
- `fit_window_until(display: int, width: int, height: int, window_class: str=..., keys: tuple[str, ...]=..., settle_seconds: float=..., timeout_seconds: float=..., process: subprocess.Popen[Any] | None=..., xauthority: str=..., home: str=...) -> None`
- `fit_window(display: int, width: int, height: int, window_class: str=..., keys: tuple[str, ...]=..., xauthority: str=..., home: str=...) -> bool`
- `has_window(display: int, window_class: str=..., name: str=..., xauthority: str=..., home: str=...) -> bool`
- `find_window(display: int, window_class: str=..., name: str=..., xauthority: str=..., home: str=...) -> str`
- `close_windows(display: int, names: tuple[str, ...]=..., window_class: str=..., xauthority: str=..., home: str=...) -> int`
- `_find_window(display: int, window_class: str=..., name: str=..., xauthority: str=..., home: str=...) -> str`
- `_display_env(display: int, xauthority: str=..., home: str=...) -> dict[str, str]`
- Notable constants/configuration names: `STATE_DIR`, `DEFAULT_WIDTH`, `DEFAULT_HEIGHT`, `MAX_WIDTH`, `MAX_HEIGHT`, `MIN_WIDTH`, `MIN_HEIGHT`, `MIN_DESKTOP_ASPECT_RATIO`, `SESSION_PATH`, `XPRA_HTML_ROOT_CANDIDATES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, network calls, subprocess/runtime control, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `__future__`, `dataclasses`, `helpers`, `helpers.localization`, `math`, `os`, `pathlib`, `re`, `shutil`, `subprocess`, `threading`, `time`, `typing`, `urllib.parse`.

## Key Concepts

- Important called helpers/classes observed in the source: `Path`, `files.get_abs_path`, `get_registry.register`, `get_registry.unregister`, `get_registry.proxy_for_token`, `get_registry.resize`, `quote`, `urlencode`, `find_xpra_html_root`, `subprocess.run`, `normalize_size`, `shutil.which`, `_display_env`, `current_display_size`, `_ensure_xrandr_mode`, `_select_xrandr_mode`, `time.sleep`, `strip`, `_xrandr_output_modes`, `result.stdout.splitlines`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_office_canvas_setup.py`
  - `tests/test_office_desktop_state.py`
  - `tests/test_office_document_store.py`

## Child DOX Index

No child DOX files.
