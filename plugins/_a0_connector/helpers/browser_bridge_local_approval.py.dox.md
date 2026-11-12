# Browser bridge local approval adapter

## Contract

- Accept only integer `contract_version: 1`, `challenge_id`, `kind`, and
  `decision` from an admitted principal with `browser.approval`.
- `kind: site` accepts `deny`, `allow_once`, `allow_turn`; `kind: action`
  accepts `decline`, `approve_once`. Inputs cannot supply subject, context,
  bridge, browser, operation, receipt or grant bindings.
- Existing site/action repositories compare the caller's immutable principal
  object, SID, load generation and fixed transport profile to their retained
  challenge under the repository lock, including same-choice replay. Shared
  subject identity alone cannot decide another bridge's challenge.
- Reuse repository receipt and correlated-control lifecycles; return only
  their public accepted projection. Accepted never means browser-applied.
- The companion must expose this event only from explicit local user action,
  not a page script or model/tool call. Server adapter construction alone
  does not attest that companion boundary or activate production.

## Verification

- Run `tests/test_browser_bridge_local_approval.py` for exact-principal,
  socket/generation isolation and existing site/action decision composition.
