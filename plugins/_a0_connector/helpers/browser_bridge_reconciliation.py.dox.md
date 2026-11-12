# Browser bridge reconciliation DOX

## Purpose

- Produce one exact `browser.reconcile` control for a process-owned provisional
  Browser transport route.
- Strictly validate the complete native/extension snapshot before allowing a
  future owner to atomically promote that exact route.
- Retain only redacted counts; lease, provider, operation, receipt, orphan and
  event records remain non-authoritative peer claims.

## Local Contracts

- `ReconciliationBinding` binds the exact principal object, fixed transport
  profile, connector SID, load generation and control ID. The broker requires
  `browser.control`, the selected profile handler and
  `connector_browser_control` at initial authorization and queued dispatch.
- Requests preserve the frozen bounded arrays: at most 128 expected contexts,
  32 active turns per context, 16 generation cursors and 2,048 known controls.
  Identifiers and duplicates fail closed.
- Result acceptance checks the exact outer bridge/load/control binding and the
  complete lease, inflight operation, terminal receipt, pending critical-event
  and old-generation orphan schema. The actual non-artifact packet remains
  limited to 524,288 bytes even though hello negotiates a 786,432-byte maximum
  JSON frame.
- The settlement acceptor validates and synchronously calls the injected atomic
  compare-and-promote callback before the broker resolves its future. Transport
  FIFO is not treated as handler-completion ordering. The callback must not
  await or block, and composition must preserve a consistent broker/owner lock
  order.
- `route_current` means the exact binding is live in either provisional or
  promoted state. Current authority is rechecked before snapshot construction,
  after broker begin, during synchronous settlement, after promotion and after
  the result wait.
- Pending critical events are schema-checked only. This helper never invokes
  event callbacks, writes event receipts, advances cursors or emits ACKs. The
  normal durable receiver owns replay after promotion.
- Reconciliation tasks are bounded and process-owned so caller cancellation
  does not interrupt a sent control. The future route owner must retire stale
  provisional routes and disconnect their broker tickets on loss or shutdown.
- Timeout, disconnect, stale authority, malformed snapshots and failed atomic
  promotion never grant route authority. No runtime principal, admission,
  owner, browser selection, Browser factory or production activation is created
  here.
- Fixed private diagnostics distinguish lost scope before the run/snapshot,
  broker authorization, pending wait or settlement. Use only the application's
  allowlisted five-per-symbol logger; never record a binding, payload, exception
  text or peer-supplied code. Diagnostic classification does not alter denial.
- After waiting for a broker completion, preserve a typed negative outcome
  before checking current authority: disconnect intentionally withdraws the
  route before delivering `CONNECTION_LOST`. Otherwise that real failure is
  obscured by a secondary scope error. Successful completion still requires
  the exact post-wait route check; no negative outcome promotes or replays work.

## Verification

- Run `pytest tests/test_browser_bridge_reconciliation.py`.
- Run the existing operation-broker and critical-event test files after broker
  or event-schema changes.

## Child DOX Index

No child DOX files.
