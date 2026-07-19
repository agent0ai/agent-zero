# network.py DOX

## Purpose

- Own the `network.py` helper module.
- This module validates public URLs and fetches remote resources safely.
- Keep this file-level DOX profile synchronized with `network.py` because this directory is intentionally flat.

## Ownership

- `network.py` owns the runtime implementation.
- `network.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `HttpFetchResult` (no explicit base class)
- `UnsafeUrlError` (`ValueError`)
- Top-level functions:
- `_build_request_headers() -> dict[str, str]`
- `_normalize_content_type(content_type: str | None) -> str | None`
- `resolve_host_ips(hostname: str) -> tuple[ipaddress._BaseAddress, ...]`
- `validate_public_http_url(url: str) -> tuple[ipaddress._BaseAddress, ...]`
- `fetch_public_http_resource(url: str, max_bytes: int, max_redirects: int=..., timeout: tuple[float, float]=...) -> HttpFetchResult`
- `is_loopback_address(address: str) -> bool`: Check whether *address* resolves to a loopback interface.
- Notable constants/configuration names: `SAFE_HTTP_SCHEMES`, `DEFAULT_FETCH_TIMEOUT`, `DEFAULT_HTTP_USER_AGENT`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: network calls, secret handling.
- Imported dependency areas include: `__future__`, `dataclasses`, `ipaddress`, `os`, `requests`, `socket`, `struct`, `urllib.parse`.

## Key Concepts

- Important called helpers/classes observed in the source: `frozenset`, `dataclass`, `strip`, `urlparse`, `parsed.hostname.rstrip.lower`, `resolve_host_ips`, `requests.Session`, `ValueError`, `content_type.split.strip.lower`, `socket.getaddrinfo`, `ipaddress.ip_address`, `seen.add`, `UnsafeUrlError`, `hostname.endswith`, `validate_public_http_url`, `socket.inet_pton`, `_checkers`, `parsed.hostname.rstrip`, `os.getenv`, `content_type.split.strip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_oauth_gemini_api.py`
  - `tests/test_oauth_github_copilot.py`
  - `tests/test_oauth_xai_grok.py`
  - `tests/test_plugin_scan_prompt.py`
  - `tests/test_tunnel_remote_link.py`

## Child DOX Index

No child DOX files.
