# browser_bridge_action_authority.py DOX

## Purpose

- Convert one exact, current consequential click or TYPE challenge into a bounded
  protected-user decision and correlated resolution control.
- Compose the existing once-only approval receipt primitive without creating a
  reusable or persistent action grant.

## Trusted inputs

- `ActionChallengeNotice` comes only from the authenticated critical-event
  receiver after exact envelope decoding.
- The current operation, remaining deadline, route/turn status, owned lease,
  semantic document/ref projection, active pairing record, and server instance
  are injected server-side. None may be reconstructed from the WebUI request.
- Core retains the action, semantic ref, expected action class, and canonical
  parameter hash. TYPE additionally retains only the verified exact UTF-8 text
  digest, never the text. It binds the extension-issued target fingerprint to
  that exact operation/document but does not derive page data it cannot
  independently observe.

## Public API projection

- Repository list callers may supply an exact server-derived context/bridge
  filter. List entries contain only challenge ID, canonical origin, action
  (`click`, `type`, or `upload_file`), action class, fixed `decline`/`approve_once` options, and
  expiry; they never reuse container Browser viewer IDs.
- Decisions accept only challenge ID and choice. Same-choice replay returns the
  same cached control identity; changed-choice replay fails closed.
- The companion-local adapter additionally supplies a server-resolved
  `expected_route`; compare exact principal object, SID, load and profile under
  the challenge lock for initial and replayed decisions. HTTP callers retain
  their authenticated subject plus current selection checks.
- `accepted` means the process-owned control task was installed. It does not
  prove that the browser effect ran.

## Authority and lifecycle

- `approve_once` consumes the exact hidden receipt after a final current-route,
  server-selection, operation, lease, document, and ref preflight and
  immediately before queuing one `browser.resolve_challenge`.
- Click binds immutable classification `none`. TYPE binds the complete immutable
  `{kind: text, sensitivity: sensitive, text_sha256}` classification throughout
  event registration, receipt consumption, resolution, and operation grant.
- Upload binds classification `none`, exact `external_side_effect`, a fixed
  file-sharing warning, and the canonical parameter hash containing the
  registered input artifact ID, MIME type, length and prefixed SHA-256 digest.
  The native private file path never enters Core or this authority repository.
- The wire grant is operation-scoped and expires no later than the challenge,
  pending operation, or two-minute ceiling.
- Cancellation, finalization, disconnect, revocation, project/profile selection
  change, document/lease mismatch, expiry, close, or uncertain/mismatched
  control completion withdraws authority.
- Challenge, decision, task, receipt, and tombstone registries are bounded.
  Typed text, page text, DOM, ref values, full URLs, raw payloads, receipts, and
  grants are neither persisted nor logged.

## Non-goals

- This controller does not infer risk or approval from model/user text, create
  challenges through HTTP, authorize later operations, advertise capabilities,
  install runtime ownership, or enable production activation.

## Verification

- Run `pytest tests/test_browser_bridge_action_authority.py`.

## Child DOX Index

No child DOX files.
