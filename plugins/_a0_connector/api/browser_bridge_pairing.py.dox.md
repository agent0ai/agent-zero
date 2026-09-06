# browser_bridge_pairing.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_pairing`.
- Create, inspect, and cancel one pending Browser bridge pairing intent for the
  current authenticated WebUI/A0 CLI session.

## Ownership

- `BrowserBridgePairing` owns the `create`, `status`, and `cancel` request
  actions and their no-store HTTP responses.
- `plugins/_a0_connector/helpers/browser_bridge_pairing.py` owns validation,
  expiry, rate limits, exchange, and public bridge-record persistence.

## Local Contracts

- Use `ApiHandler` directly so normal session authentication and CSRF remain
  mandatory even when Agent Zero login is disabled. Do not use
  `ProtectedConnectorApiHandler`, which disables CSRF for legacy connector
  clients.
- Accept exactly `{action: create, display_name}`,
  `{action: status}`, or `{action: cancel, pairing_id}` with a bounded JSON
  request. Reject duplicate JSON object keys at every depth before dispatch.
  Reject arbitrary extension IDs, server URLs, scopes, keys, or overrides from
  this authenticated presentation route.
- `create` is unavailable unless the instance rollout gate is `preview` or
  `available` and `A0_BROWSER_BRIDGE_EXTENSION_ID` contains an exact pinned
  Chrome extension ID. The external Agent Zero base URL comes from the request
  origin/host or the server-owned `A0_BROWSER_BRIDGE_SERVER_BASE_URL` override.
- Responses use `Cache-Control: no-store`. Only the creation response contains
  the one-time code. Status, cancel, logs, and persistent state never contain
  it.
- Every response identifies the native runtime as belonging to the user's
  browser host, never the Agent Zero Docker container. Pairing does not imply a
  proven connector session or active browser control.

## Work Guidance

- Keep UI orchestration and QR/copy rendering outside this handler.
- Do not add pairing material to query strings, URLs, environment variables,
  logs, analytics, or persistent KVP state.

## Verification

- Run `pytest tests/test_browser_bridge_pairing_foundation.py`.

## Child DOX Index

No child DOX files.
