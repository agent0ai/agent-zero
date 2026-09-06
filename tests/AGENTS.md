# Tests DOX

Legacy retirement tests use only the exact temporary prototype fixture and
synthetic journals. Cover once-only bounded draining, no replay, payload purge,
and legacy-only fail-closed guards without touching live tabs or credentials.
Quarantine tests cover durable private backup before exact field removal,
idempotence, user-attachment preservation, symlink refusal, real persistence
hook dispatch, and bounded loaded-context-only sweep behavior.

## Purpose

- Own pytest regression, security, integration, and contract tests.
- Keep tests focused on behavior that should remain stable across framework changes.

## Ownership

- Test files live directly under `tests/` and are named for the behavior or subsystem they cover.
- Shared fixtures should be added only when multiple tests need them.
- Browser setup, selection, access and pairing UI regressions share
  `test_browser_bridge_setup_webui.py`; site/action consent UI shares
  `test_browser_approval_inbox_webui.py`. Keep artifact transfer/materialization
  in `test_browser_bridge_artifact_controller.py` and lifecycle composition in
  `test_browser_extension_services.py`. Reuse `browser_bridge_test_support.py`
  for Node runners and identical synthetic fixtures, not middleware security proofs.
- Runtime artifacts created during tests should use pytest temporary directories or existing isolated test helpers.

## Local Contracts

- Tests must not require real API keys, network-only services, private user data, or local `usr/` runtime state.
- Keep tests deterministic and isolated from existing chats, uploads, downloads, plugin state, and settings.
- Prefer exercising public helper/API contracts over fragile implementation details when practical.
- Security regression tests should assert the protected behavior directly.
- Static connector discovery coverage is consolidated in
  `test_browser_bridge_foundation_status.py`; do not repeat the same module
  stubs and feature-list assertions in each pairing/policy/approval/metadata
  suite. Keep their behavioral auth, schema, expiry and side-effect tests.
- Launcher gateway tests must cover feature negotiation, authenticated and
  CSRF-protected control, acknowledgement timeout, identity lifecycle,
  context-bound CLI routing precedence, duplicate/multiple-host behavior,
  scope-driven availability, and emergency disconnect without a live host.
- Browser extension bridge foundation tests must remain host-independent and
  effect-free: use temporary legacy-plugin fixtures, assert redacted versioned
  projections, preserve existing container/A0 CLI CDP behavior, and prove that
  every reserved `extension:` selection fails before legacy or container
  fallback while the runtime is unavailable.
- MV3 runtime foundation tests must assert the exact frozen runtime, adapter,
  and protocol identifiers while proving the projection stays disabled and
  browser-host-only, with no lease/finalization validation claim. Test actual
  binding, redaction and finalization behavior in the production lifecycle,
  lease and broker suites, not parallel discovery-only model tests.
- Browser bridge pairing tests must remain host-independent and use synthetic
  in-memory records. Prove default rollout/config failure, 160-bit five-minute
  creation, one active intent per authenticated session, no-store and CSRF,
  exact extension/server/public-key binding, atomic single use, generic bounded
  failures including duplicate JSON keys at every object depth, public-key-only
  persistence, redacted status, and browser-host-only Docker semantics. Pairing
  WebUI tests must prove the code stays transient in the open panel, cleanup and
  cancel clear it, status cannot rehydrate it, copy is explicit, and UI requests
  cannot supply server-owned identity. Pairing tests must also prove that
  challenge/session and browser-control capabilities remain absent until their
  complete security boundary exists.
- Browser bridge challenge tests must use synthetic in-memory bridge records and
  deterministic nonces/clocks. Prove 60-second expiry, exact request/proof
  schemas, active-record and server binding, source-rate bounds, atomic consume
  on both valid and invalid proof attempts, real Ed25519 verification over the
  fixed JCS bytes, last-authenticated persistence, generic no-store endpoint
  failures, and continued absence from capability discovery until scoped
  WebSocket principal activation is complete.
- Browser bridge site-policy tests must use synthetic durable state and active
  pairing records. Prove exact HTTP(S)-origin canonicalization, rejection of
  userinfo, paths, queries, fragments, wildcards, ambiguous numeric hosts, and
  restricted schemes, plus default deny, bridge/subject/server isolation,
  atomic idempotent allow, revoke, corruption failure, strict bounded bodies,
  normal auth/CSRF, no-store responses, and continued non-advertisement of
  Browser runtime and one-operation approvals.
- Browser bridge approval tests must use synthetic current routes, active
  pairing records, clocks, and identifiers. Prove exact binding across bridge,
  subject, key/load generation, connector, context, browser session, turn,
  action, operation, tab and document generation, parameter hash, target
  fingerprint, origin, and action class; one winning user decision; one exact
  receipt consumption; two-minute
  expiry; bounded state; and denial on mismatch, cancellation, finalization,
  disconnect, revocation, or expiry. The protected API must accept only a
  challenge ID and explicit decision, reject binding injection and malformed or
  duplicate-key bodies, require auth/CSRF, return no-store projections, and
  remain non-activating with no permissive route-resolver fallback.
- Browser bridge context tests must use synthetic principals, routes, data
  sources, and log entries. Prove exact principal-object, SID, and load-generation
  isolation; advertise-before-subscribe/read/message authority; current-route
  rechecks after source calls; bounded UTF-8-safe message projection from only
  the actual `input`, `user`, and `response` log types; classification-only
  projection for other known log types; and complete removal of tool/browser
  payloads, headings, kvps, scripts, selectors, paths, raw errors, snapshots,
  and attachments. Preserve cursor, history pagination, and completion state,
  reject nonadvancing pages, and keep the helper separate from legacy and live
  runtime wiring.
- Browser bridge runtime-registry tests must use synthetic immutable principals,
  typed active-record verification and typed complete-runtime admission. Prove
  exact hello shape and bounds, rejection of remote authority and unproven
  capabilities, default-deny admission, current server-instance scoping,
  fail-isolated cleanup after route removal, same-principal reconnect and
  generation replacement, cross-principal/SID isolation, session capacity,
  explicit context plus extension selection, and exact active-route operation
  and control settlement. The restricted sender test must assert direct shared
  manager emission with the expected principal and exact handler while rejecting
  every non-operation/control event. Keep tests independent of the legacy
  connector registry and do not imply production activation.
- Browser bridge transport tests must prove only the exact process-owned
  production profile is accepted. Reject retired development identities even
  with complete scope sets; structural identity never supplies missing runtime
  capabilities. Preserve production reconciliation and scoped-sender checks.
- Browser bridge bootstrap/handler tests must prove the default application is
  absent and hello-only, full immutable event sets require explicit server
  binding, exact hello admission precedes any ready response, and the success
  projection includes the complete fresh typed activation and authenticated
  transport binding while omitting subject, raw instance claims, exec config,
  and legacy metadata. Prove an unadmitted SID and a missing owner fail closed,
  restricted events never enter legacy handlers, disconnect retires the exact
  route, and an installed owner cannot be synchronously unbound or replaced;
  exact async retirement must await cleanup before clearing API ownership. Keep
  the admission evaluator synthetic; these tests do not establish production cutover.
- Browser bridge message tests use synthetic durable state and delivery hooks.
  Assert reservation-before-effect, accepted replay across reconnect without
  duplicate execution, payload conflict, current authority before delivery,
  and uncertain partial delivery or acceptance-write failure without retry.
  Never start a real model, touch existing contexts, or persist message text in
  idempotency fixtures.
- Message and queue journal coverage must include a full original 2,048-record
  store, the downgrade-fencing version marker, new individually indexed KVP
  receipts, reconstruction, retained old
  replay/conflict/uncertainty protection, corruption and failed reservation
  writes. Use temporary KVP roots; retain the separate 32-live-item queue bound.
  Injected stores must use the same KVP-shaped reads/writes and migration path
  as production; do not maintain a test-only whole-journal implementation.
- Server startup tests must enter multiple ASGI lifespans on the same runtime,
  including startup-hook failure and plugin disablement. Each attempt owns
  installation plus awaited cleanup; the legacy HTTP guard remains independent.
- Browser queue tests use the real Core queue with synthetic contexts and
  hash-only in-memory journals: prove owned-only projection, foreign-item
  isolation, reservation-before-effect, changed-payload conflict, no duplicate
  enqueue or delivery, and no retry after uncertain effects. Local approval
  tests prove exact retained principal object, SID and load-generation matching
  in the real site/action decision repositories, not only subject equality.
- Browser bridge context-controller tests must exercise only synthetic routes,
  context sources, message effects, and WebSocket managers. Prove exact native
  acknowledgement shapes, cursor-preserving snapshot/live projection, strict
  body and empty-placeholder handling, expected-principal/handler emission,
  separate stable item and source-update cursors without mid-page skipping,
  stream capacity, stale-route suppression, and principal/SID/generation-bound
  unsubscribe/disconnect. A healthy explicit subscription must not silently
  expire, and presentation cleanup must never cancel a simulated agent task.
- Browser bridge critical-event tests must use synthetic current routes,
  durable stores, callbacks, and WebSocket managers. Prove exact supported
  event/data enums and bounds, reservation-before-callback, hash-only storage,
  event-ID/sequence conflict rejection, callback-error replay, passive-created
  lease behavior, gap-safe contiguous cursor advancement, crash-safe duplicate
  ACK, current-generation replacement, and exact ACK transport. Finalization
  observers must receive no usable control-result proof, and unsupported event
  types, stale routes, malformed data, and permissive defaults stay fail-closed.
- Browser bridge reconciliation tests must use synthetic fixed-profile
  principals, provisional route checks, snapshots, transport and an atomic
  promoter. Prove exact frozen request parity, full nested result validation,
  synchronous promotion before future delivery, stale/forged/timeout denial,
  and redacted-count-only retention. Embedded pending events are validation
  input only: never invoke their callbacks, persist them, or ACK a cursor. Keep
  production admission, runtime ownership, browser selection and live transport
  out of these fixtures.
- Browser bridge site-authority tests must use synthetic current operations,
  leases, routes, turns, clocks, and control completions. Prove exact retained
  origin/parameter/lease/document/fingerprint validation, server-generated safe
  projection, explicit decision-only WebUI input, no grant before a matching
  control result, operation-only scope, exact current-turn reuse with automatic
  fresh-challenge resolution, lifecycle invalidation, bounded state, strict
  bodies, auth/CSRF, no-store responses, and unavailable defaults. Critical
  challenge registration must precede cursor advancement and persist only event
  and payload hashes, never origin, summary, or binding values.
- Browser bridge artifact-controller tests use synthetic exact routes, pending
  operation bindings, receivers, clocks, and WebSocket managers. Prove exact
  phase schemas and binding comparison, canonical base64 and size bounds,
  progress/descriptor/abort acknowledgement shapes, exact expected-principal
  emission, no guessed chunk replay, pathless completion, one bounded expiry
  owner, and principal/SID/generation-only disconnect cleanup. Sender and
  screenshot cases also cover upload bounds and safe materialization; do not
  activate live handlers or transfer real user files.
- Restricted WebSocket tests must prove authoritative proof presence with no
  ambient credential rescue, origin-before-proof, exact handler binding,
  immutable event sets, credential revalidation, and isolation from ordinary
  user buckets, global handlers, broadcasts, diagnostics and reconnect buffers.
  Exercise stale-SID replacement, generation-bound delayed delivery, duplicate
  disconnect, partial activation rollback and raw-error canaries. The initial
  connector adapter accepts hello only and must not activate legacy CLI tools
  or advertise operational readiness. Keep tests synthetic and effect-free.
- Browser companion release-metadata tests use only synthetic public catalogs.
  They must prove default unavailability, the distinct non-install-ready
  presentation contract, strict compatibility and the independent non-lowerable
  server floor, complete signed artifact validation, canonical URL and
  secret/path/extension-ID rejection, normal auth/CSRF, malformed/nonempty raw
  request-body rejection, and the browser-host-only Docker boundary.

## Work Guidance

- Add focused tests near the affected subsystem's existing tests.
- Use descriptive test names that state the regression or contract.
- Avoid broad sleeps or real-time dependencies; use monkeypatching or controlled clocks where possible.

## Verification

- Run `pytest` for broad changes.
- Run `pytest tests/test_name.py` for narrow changes and mention any broader test gaps at closeout.

## Child DOX Index

No child DOX files.
