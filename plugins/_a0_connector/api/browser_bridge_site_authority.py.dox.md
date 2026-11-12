# browser_bridge_site_authority.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_site_authority`.
- List safe pending site prompts and relay one explicit protected-user choice.

## Ownership

- `BrowserBridgeSiteAuthority` owns the authenticated, CSRF-checked, no-store
  presentation boundary.
- `helpers/browser_bridge_site_authority.py` owns exact current-operation and
  lease validation, idempotent decisions, retained resolution tasks, and
  operation/turn origin grants.
- Browser runtime composition owns installing the otherwise unavailable global
  repository and wiring broker, lease-index, route, and lifecycle adapters.

## Local Contracts

- Accept exactly `{action: "list", context_id}` or
  `{action: "decide", challenge_id, decision}` with `decision` equal to `deny`,
  `allow_once`, or `allow_turn` in a bounded duplicate-key-free JSON body.
  Only production `open-site-` requests additionally accept `allow_site`.
- Treat list `context_id` only as a selection hint and derive the selected
  extension bridge from current AgentContext agent0 project/profile config.
  Missing, container, or unselected contexts return a successful empty list
  before the optional authority is retrieved.
- Derive the subject and every bridge, route, operation, lease, document,
  fingerprint, origin, grant, and control field from current server state.
- Recheck that exact context/bridge selection at challenge registration,
  decision, turn-grant lookup, and queued-control authorization; a changed
  selection withdraws authority.
- An exact current turn grant may resolve a newly registered matching challenge
  without another prompt, but it still uses a fresh correlated control and
  cannot authorize another turn, route, origin, or an operation-only grant.
- List only challenge ID, canonical origin, `navigate` or production `open` action class,
  server-generated summary, exact options, and expiry. A decision response may
  additionally expose its stable control ID and accepted status.
- Never accept or expose authority bindings, full URLs, handles, hashes,
  digests, raw extension summary text, page data, or grant internals.
- Responses are allowlisted and `Cache-Control: no-store`. This endpoint does
  not create challenges, infer choices from natural-language text, persist
  Browser data, advertise readiness, or activate the Browser bridge.
- Production `open-site-` IDs belong to `extension_first_open`, not the native
  navigate challenge repository. Merge its current context/bridge prompts into
  the bounded 128-item list. Resolve these IDs only against the installed
  service's exact retained request; missing or stale IDs never fall back to
  native receipt handling. The compatible `control_id` response field contains
  an opaque `open-decision-` decision identifier, not a native control or receipt.
  Only explicit `allow_site` persists saved exact-origin policy through the
  composed helper, from retained authority fields, before waiter release.
  Once/turn decisions never persist policy. This HTTP endpoint cannot create
  requests; only the server Browser operation path may do so. Native navigate
  request options remain the original three-choice list.

## Verification

- Run `pytest tests/test_browser_bridge_site_authority.py`.

## Child DOX Index

No child DOX files.
