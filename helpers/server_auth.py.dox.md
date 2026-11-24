# server_auth.py DOX

## Purpose

- Own the `server_auth.py` helper module.
- This module holds the shared header-based authentication and project routing used by the MCP server (`mcp_server.py`) and the A2A server (`fasta2a_server.py`).
- Keep this file-level DOX profile synchronized with `server_auth.py` because this directory is intentionally flat.

## Ownership

- `server_auth.py` owns the runtime implementation.
- `server_auth.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RequestRejected` (`Exception`): a request with an invalid or conflicting project; carries `status_code` and `detail`.
- Top-level functions:
- `token_matches(candidate: str | None, expected: str | None) -> bool`: constant-time token comparison (`hmac.compare_digest`); an empty or missing token never matches.
- `get_header(scope, name: str) -> str | None`: first value of header `name` from an ASGI scope (case-insensitive, latin-1), or None.
- `get_bearer_token(scope) -> str | None`: token of an `Authorization: Bearer <token>` header (scheme case-insensitive), or None.
- `resolve_project(url_project: str | None, scope) -> str | None`: the project from the URL segment or the `X-A0-Project` header.
- Notable constants/configuration names: `PROJECT_HEADER` (`"X-A0-Project"`).

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Auth contract: both servers accept the API token (the `mcp_server_token` setting) either in the URL (`/t-<token>/`) or as `Authorization: Bearer <token>`; the URL form keeps working unchanged. Callers compare tokens only through `token_matches`.
- Project-routing contract: the project may come from the URL (`/p-<project>/`) or the `X-A0-Project` header. `resolve_project` validates each with `projects.validate_project_name` and raises `RequestRejected(400, ...)` when the URL value is invalid, the header value is invalid, or both are given and differ. A blank header counts as absent. It returns the URL project, else the header project, else None.
- `RequestRejected.detail` is safe to return to the client; it never contains the token.
- Never log the token or the raw header value.
- Observed side-effect areas: none (pure functions over the ASGI scope).
- Imported dependency areas include: `hmac`, `helpers`.

## Key Concepts

- Important called helpers/classes observed in the source: `hmac.compare_digest`, `projects.validate_project_name`.
- Callers: `DynamicMcpProxy.__call__` in `mcp_server.py` maps `RequestRejected` to a Starlette `HTTPException`; `DynamicA2AProxy.__call__` in `fasta2a_server.py` sends a plain-text response with `status_code`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Keep this module free of server-specific routing; path parsing stays in each server's proxy.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests:
  - `tests/test_mcp_a2a_header_auth.py`

## Child DOX Index

No child DOX files.
