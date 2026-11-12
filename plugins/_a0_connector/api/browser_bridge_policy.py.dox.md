# browser_bridge_policy.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_policy`.
- Manage persistent exact-origin allow decisions for one currently active Browser bridge.

## Ownership

- `BrowserBridgePolicy` owns protected `list`, `allow`, `revoke`, and production `set_mode` actions and no-store response projection.
- `plugins/_a0_connector/helpers/browser_bridge_policy.py` owns canonical origin validation, bounded durable persistence, and fail-closed lookup.

## Local Contracts

- Use `ApiHandler` directly so normal WebUI session authentication and CSRF are mandatory.
- Reject non-string actions with HTTP 400 before reading pairing or policy state.
- Accept only `{action: list, bridge_id}`, `{action: allow, bridge_id, origin}`, or `{action: revoke, bridge_id, origin}` in a bounded duplicate-key-free JSON body.
- Also accept exactly `{action: set_mode, bridge_id, site_mode}`, where mode is
  `ask_per_site` or `allow_all_websites`. The latter is explicit persistent
  browsing permission for this server/subject/bridge only, never action
  approval. Read back successful persistence before returning the mode.
  Default remains `ask_per_site`; development cannot set or adopt this mode.
- Resolve the exact active bridge record for the current server instance before reading or mutating its policy. Derive the subject from that record; never accept server or subject identity from the request.
- Site identity is a normalized HTTP(S) origin only. Reject userinfo, paths, query strings, fragments, wildcards, restricted schemes, malformed hosts, and ambiguous encodings.
- Responses are allowlisted and `Cache-Control: no-store`. This foundation never creates consequential-action receipts, dispatches browser work, or advertises runtime readiness.
- Response contract/version stay v1 with the two recognized site-mode values.
  Internal store v2 adds at most 128 all-websites owner records, validates the
  entire document, and continues reading legacy v1 exact grants. Each mode
  generation derives distinct exact-origin grant IDs; visited URLs/origins
  are not accumulated. Disabling removes only that mode, not saved sites.

## Work Guidance

- Keep Browser Settings presentation and one-operation approval challenges outside this endpoint.
- Do not include page URLs, titles, content, request arguments, or raw exceptions in policy records or responses.

## Verification

- Run `pytest tests/test_browser_bridge_policy_foundation.py`.

## Child DOX Index

No child DOX files.
