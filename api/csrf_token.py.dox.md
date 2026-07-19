# csrf_token.py DOX

## Purpose

- Own the `csrf_token.py` API endpoint.
- This module issues or refreshes CSRF tokens for browser API clients.
- Keep this file-level DOX profile synchronized with `csrf_token.py` because this directory is intentionally flat.

## Ownership

- `csrf_token.py` owns the runtime implementation.
- `csrf_token.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `GetCsrfToken` (`ApiHandler`)
  - `get_methods(cls) -> list[str]`
  - `requires_csrf(cls) -> bool`
  - `async process(self, input: Input, request: Request) -> Output`
  - `async check_allowed_origin(self, request: Request)`
  - `async is_allowed_origin(self, request: Request)`
  - `get_origin_from_request(self, request: Request)`
  - `async get_allowed_origins(self) -> list[str]`
  - `get_default_allowed_origins(self) -> list[str]`
- Notable constants/configuration names: `ALLOWED_ORIGINS_KEY`.

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `GetCsrfToken` is an `ApiHandler`.
- `GetCsrfToken` defines `process(...)`.
- `GetCsrfToken` defines `get_methods(...)`.
- `GetCsrfToken` defines `requires_csrf(...)`.
- Observed side-effect areas: filesystem writes, network calls, secret handling, tunnel state.
- Imported dependency areas include: `fnmatch`, `helpers`, `helpers.api`, `secrets`, `urllib.parse`.

## Key Concepts

- Important called helpers/classes observed in the source: `login.is_login_required`, `self.initialize_allowed_origins`, `self.get_origin_from_request`, `urlparse`, `dotenv.get_dotenv_value`, `self.get_default_allowed_origins`, `dotenv.save_dotenv_value`, `self.check_allowed_origin`, `secrets.token_urlsafe`, `runtime.get_runtime_id`, `self.is_allowed_origin`, `self.get_allowed_origins`, `origin.strip`, `join`, `fnmatch.fnmatch`, `split`, `tunnel_api_process`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_http_auth_csrf.py`
  - `tests/test_self_update_tag_filter.py`
  - `tests/test_ws_security.py`

## Child DOX Index

No child DOX files.
