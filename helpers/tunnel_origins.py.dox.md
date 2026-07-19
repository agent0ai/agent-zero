# tunnel_origins.py DOX

## Purpose

- Own origin normalization for Remote Control tunnel URLs and CSRF/WebSocket same-origin checks.
- Provide a small helper boundary between tunnel discovery and security enforcement.

## Ownership

- `tunnel_origins.py` owns the runtime implementation.
- `tunnel_origins.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `origin_from_url(value)`
- `origin_key(value)`
- `get_active_tunnel_origins()`

## Runtime Contracts

- Normalize URL and Origin header values to `scheme://host[:port]`, omitting default ports.
- Return comparable origin keys with default ports restored for same-origin checks.
- Treat invalid, missing, or malformed origins as `None`.
- Discover active tunnel origins from `TunnelManager` and the Docker tunnel API without raising if either source is unavailable.
- Keep tunnel service lookups short-timeout and local-only.

## Work Guidance

- Keep parsing based on `urllib.parse` rather than hand-rolled string checks.
- Preserve defensive exception handling because tunnel services are optional and may not be running.
- Coordinate security-sensitive changes with CSRF and WebSocket tests.

## Verification

- Run `pytest tests/test_csrf_tunnel_origins.py tests/test_ws_csrf.py -q` after changing tunnel origin behavior.

## Child DOX Index

No child DOX files.
