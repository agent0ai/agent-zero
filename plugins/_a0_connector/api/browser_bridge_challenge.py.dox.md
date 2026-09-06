# browser_bridge_challenge.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_challenge`.
- Issue a 60-second, memory-only connector challenge for one active Browser
  bridge credential.

## Ownership

- `BrowserBridgeChallenge` owns the purpose-built unauthenticated HTTP boundary
  and its generic no-store response.
- `plugins/_a0_connector/helpers/browser_bridge_auth.py` owns exact challenge,
  nonce, source-rate, expiry, canonical proof, signature, and one-time consume
  rules.

## Local Contracts

- Accept exactly trust version, active `bridge_id`, and a fresh 32-byte client
  nonce encoded as unpadded base64url. Bound request bodies to 8 KiB and reject
  duplicate JSON keys before challenge validation.
- Challenges are process-memory only, expire after 60 seconds, and are consumed
  on the first proof attempt whether verification succeeds or fails.
- Nonexistent, revoked, malformed, mismatched, expired, and rate-limited inputs
  use generic public failures and never expose credential records or raw errors.
- Successful proof uses Ed25519 over the fixed scalar-only RFC 8785 JCS object,
  returns a server-derived `browser_bridge` principal projection, and records
  the authentication time. It does not accept cookies, API keys, bearer tokens,
  client-selected scopes, handlers, protocols, or key generations.
- Responses use `Cache-Control: no-store`. The route remains unavailable while
  the Browser bridge rollout gate is disabled.

## Work Guidance

- Do not advertise `browser_bridge_challenge_v1` or connect this principal to
  `/ws` until origin validation, ambient-cookie isolation, scoped handler
  activation, event filtering, disconnect cleanup, and negotiation tests land
  together.

## Verification

- Run `pytest tests/test_browser_bridge_challenge_foundation.py`.

## Child DOX Index

No child DOX files.
