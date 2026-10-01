# ws_limits.py DOX

## Purpose

- Own the effective WebSocket payload ceiling shared by Uvicorn, Engine.IO, and connector protocol negotiation.

## Ownership

- `A0_WS_MAX_PAYLOAD_BYTES` reads the positive `A0_WS_MAX_PAYLOAD_BYTES` environment override once at process startup and otherwise defaults to 50 MiB.
- `LEGACY_WS_MAX_PAYLOAD_BYTES` is the conservative 4 MiB receive floor used when a connector peer does not advertise a limit.
- `peer_ws_max_payload_bytes()` validates peer declarations and never permits outbound payloads above the local transport ceiling.

## Runtime Contracts

- Transport configuration and connector capability responses must source their limit from this module.
- Invalid, missing, zero, or negative peer limits degrade to the legacy floor rather than risking a transport disconnect.

## Work Guidance

- Keep this module dependency-light so startup and bundled plugins can import it safely.

## Verification

- Run `pytest tests/test_run_ui_config.py tests/test_ws_manager.py` and connector plugin protocol tests after changing these limits.

## Child DOX Index

No child DOX files.
