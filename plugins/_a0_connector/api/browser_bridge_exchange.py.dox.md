# browser_bridge_exchange.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_exchange`.
- Atomically exchange one short-lived pairing code for a server-side public-key
  bridge record.

## Ownership

- `BrowserBridgeExchange` owns the purpose-built unauthenticated exchange HTTP
  boundary and its generic no-store response.
- `plugins/_a0_connector/helpers/browser_bridge_pairing.py` owns exact schema,
  identity, public-key, attempt, expiry, source-rate, and persistence rules.

## Local Contracts

- This endpoint deliberately uses `PublicConnectorApiHandler`: the single-use
  pairing code replaces ambient WebUI authentication and CSRF for this route
  only. It grants no session cookie, API key, bearer credential, or private key.
- Accept exactly trust version, pairing code, normalized server base URL,
  server-pinned extension ID, companion instance ID, and an Ed25519 raw
  base64url public key. Bound request bodies to 8 KiB and reject duplicate JSON
  object keys at every depth before exchange validation.
- Nonexistent, expired, consumed, malformed, mismatched, and attempt-exhausted
  pairing inputs return the same `pairing_exchange_failed` response. Never
  include input values or exception text.
- Successful exchange persists only the allowlisted public bridge record and
  returns fixed browser-bridge scopes and non-secret identity. It continues to
  report connector-session and browser-control readiness as false until the
  signed proof and negotiated extension runtime are implemented.
- Responses use `Cache-Control: no-store`. The route is disabled when the
  instance rollout gate or server-pinned extension ID is unavailable.

## Work Guidance

- Keep signed connector challenge/proof activation in its own later security
  frontier; do not advertise challenge or browser-control features here.

## Verification

- Run `pytest tests/test_browser_bridge_pairing_foundation.py`.

## Child DOX Index

No child DOX files.
