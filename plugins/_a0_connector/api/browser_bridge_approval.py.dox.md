# browser_bridge_approval.py DOX

## Purpose

- Own `POST /api/plugins/_a0_connector/browser_bridge_approval`.
- List safe consequential-action prompts for the extension bridge selected by
  one current chat and record one explicit WebUI decision for an existing
  challenge.

## Ownership

- `BrowserBridgeApproval` owns the authenticated, CSRF-checked decision boundary and its no-store response.
- `plugins/_a0_connector/helpers/browser_bridge_approval.py` owns the exact
  once-only receipt primitive.
- `plugins/_a0_connector/helpers/browser_bridge_action_authority.py` owns
  current operation/lease/document validation, safe listing, decision
  idempotency, receipt consumption, control correlation, and lifecycle cleanup.

## Local Contracts

- Accept only `{action: "list", context_id}` or `{challenge_id, choice}` with
  `choice` equal to `approve_once` or `decline` in a bounded,
  duplicate-key-free JSON body. Reject non-string choices with HTTP 400 before
  resolving authority; array/object values must not raise enum-lookup errors.
- Treat list `context_id` only as a selection hint. Resolve its current
  `host_required` `extension:<bridge>` choice from the exact AgentContext agent0
  project/profile configuration before retrieving the optional authority.
  Missing, container, or unselected contexts return the same successful empty
  list; a selected bridge with no authority remains unavailable.
- Never accept bridge, generation, context, browser-session, turn, action, operation, origin, action-class, target, or parameter bindings from this request.
- Pending projections contain only challenge ID, server-owned action
  discriminator (`click` or `type`), canonical origin, action class, fixed
  options, and expiry. Context and bridge are server-side filters and are never
  reflected as Browser viewer IDs or submitted decision authority.
- Require the active paired bridge, server-derived subject, key generation,
  connector, load generation, context, session, turn, action, operation, tab
  handle, retained parameter hash, owned lease digests/origin, semantic
  document identity/epoch, and requested semantic ref to remain exact.
- Approval receipts are process-memory-only, expire within two minutes and at current-turn termination, and authorize exactly one matching consumption.
- TYPE receipts bind the exact immutable sensitive-text classification and
  verified text digest. The endpoint never receives or returns the typed text,
  digest, ref, or target fingerprint.
- `approve_once` consumes the hidden receipt after a final current-route check
  and immediately before queuing one exact `browser.resolve_challenge` control.
  The process-owned control task and exact correlated result do not convert the
  WebUI acknowledgement into proof that the click succeeded.
- Disconnect, cancellation, turn finalization, revocation, expiry, or any binding mismatch destroys approval authority.
- A changed project/profile extension selection destroys approval authority;
  selection is rechecked at registration, decision, receipt, and queued-control
  authorization boundaries.
- Responses are allowlisted and `Cache-Control: no-store`. This foundation does not create challenges from HTTP, infer approval from natural-language text, persist page or operation payloads, dispatch control events, or advertise Browser runtime readiness.

## Work Guidance

- Compose the controller only from the runtime broker, exact route/turn
  verifiers, owned lease/document indexes, and restricted control sender; never
  make a permissive resolver fallback.
- Keep durable site policy and persistent origin decisions in `browser_bridge_policy`, not this endpoint.

## Verification

- Run `pytest tests/test_browser_bridge_action_authority.py`.

## Child DOX Index

No child DOX files.
