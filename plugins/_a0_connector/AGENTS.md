# A0 Connector Plugin DOX

## Purpose

- Own the current Agent Zero connector plugin for HTTP and WebSocket integration.
- Provide remote execution, text-editing freshness, and connector runtime bridges.

## Ownership

- `plugin.yaml` owns plugin metadata and settings scope.
- `api/` owns connector WebSocket and API entry points.
- `helpers/` owns chat context, event bridge, execution config, freshness, version, and WebSocket runtime helpers.
- `tools/`, `prompts/`, `skills/`, `extensions/`, and `webui/` own connector-facing agent and UI contributions.

## Local Contracts

- `tools/computer_use_remote.py` logs its message as the dedicated `computer_use_remote` type with an `icon://desktop_windows` gerund headline naming the action, such as `Computer use: Capturing screen`; `extensions/webui/get_message_handler/` owns the `DSK` badge presentation in its own lilac accent shared with the agent-to-agent badge, distinct from the execution badge's purple accent and `extensions/webui/get_process_step_types/` registers the type.
- `tools/text_editor_remote.py` logs `type="text_editor"` through a `get_log_object()` override so the WebUI routes its messages through the `_text_editor` plugin's `get_message_handler` JS extension; keep remote edits visually consistent with local edits.
- Remote text editing reuses the shipped `_text_editor` patch and log helpers. Disabling local editor discovery does not remove these Python modules; removing the bundled dependency is unsupported.
- Preserve session-auth and `auth.handlers` activation assumptions.
- `v1/chats_list` keeps the normal list response unchanged. An optional string `query` (at most 200 characters) returns read-only `matches` over those loaded contexts, using the bundled `_sidebar_folders.helpers.search` pure helper independently of its UI activation/config. Return only IDs, title flags and bounded literal text parts; blank queries do not scan. Preserve the existing protected route's authentication. CLI search scope/order stays with its original candidate list.
- Keep remote tool prompts synchronized with remote tool behavior and disclose
  them only from connected CLI metadata: no connected CLI hides all remote tool
  prompts, remote file metadata enables `text_editor_remote`, F4-enabled remote
  execution metadata enables `code_execution_remote` and `input_remote`, and supported enabled
  Computer Use that does not need re-arming enables `computer_use_remote`.
- Remote execution uses the same runtime set as local code execution. `input_remote`
  mirrors local `input`, forwarding trimmed `keyboard` through gated terminal
  execution with framework-owned `allow_running`. It shares connection, write
  access, timeout, transfer, and disconnect handling; ordinary model args cannot
  enable `allow_running`. There is no `runtime=input` or `code` input alias.
- `input_remote` requires both its own policy permission and the bundled
  `plugin:_a0_connector:code_execution_remote` terminal action. Both are enabled
  by the default policy without an Agent Editor grant. Custom restrictions remain
  authoritative. Shared policy resolution
  applies the dependency to prompts, native schemas, and execution; the input
  wrapper rechecks that exact capability before rewriting args or dispatching,
  including when a profile shadows the execution tool name.
- Computer Use prompts keep `element_index` top-level and semantic `target` syntax in backend skills. macOS `app-scoped-semantic-targeting` enables explicit app/window scope; older clients use the indexed window workflow. Native `get_window_state.mode` only labels output and stays out of model-facing guidance.
- `computer_use_remote` starts a missing chat session inside the first requested action only after the host returns `COMPUTER_USE_SESSION_REQUIRED` before dispatch. Start once on the same socket/context and resume with the returned session ID and a fresh operation ID. Never auto-replace an explicit session binding, retry permission/ambiguous failures, or start from `status`/`stop_session`; keep existing host enablement, trust, and platform approval checks. Attach the requested action's capture, not an extra startup capture.
- Host Computer Use skills begin with `list_windows` or `capture`. Linux X11/XWayland viewer guidance lives in `skills/host-computer-use-linux/references/x11-viewers.md` and requires independently enabled host code execution for shell techniques. Permission denials remain stop conditions; the internal Docker/Xpra desktop and standalone X11 backend selection are unchanged.
- Agent-scoped skill discovery includes this plugin's `skills/` root only when a routed connected socket has connector capability metadata. WebUI-only sockets do not qualify; disabled capabilities still count as a connected CLI. Filter roots on each discovery without mutating cached paths or persisting visibility settings. `setup-a0-cli` lives in root `skills/` and stays discoverable while disconnected.
- Never re-add a connector prompt that the effective project/profile tool policy
  blocks.
- Do not bypass WebSocket authentication or leak connector session data.
- `helpers/event_bridge.py` preserves `tool_start` events for dedicated tool log types as well as legacy `tool` logs. Wait/countdown logs remain status events.
- Host Files transfers use authenticated HTTP for both directions. Download receipts use opaque, request-scoped slots in server-owned temporary directories; the protected `file_browser_transfer` API rejects expired slots, enforces byte limits and rechecks host access. Cleanup and receipt publication share a lock so late requests cannot recreate expired files. WebSocket control/results retain the negotiated limits. Editor inherits the configurable File Browser text limit (10 MiB by default).
- Context kill/remove extensions release pending transfer state synchronously before task shutdown and send best-effort abort notices on the shared background worker, covering native Stop/reset/delete as well as Connector routes.
- HTTP capabilities and `connector_hello` advertise
  `capabilities.ws_max_payload_bytes`. Store the peer ceiling per authenticated
  SID, remove it on disconnect, and use the 4 MiB legacy floor when absent or
  invalid. Every connector event sent to that SID must pass the ceiling to the
  shared WebSocket manager; oversize becomes a structured
  `PAYLOAD_TOO_LARGE` error and never a transport disconnect. Mirror the same
  limit into the manager's live connection state so Socket.IO acknowledgements
  are constrained after their final result envelope is assembled.
- `helpers/file_browser.py` registers the bundled live host-folder provider for Files. Discover CLI sessions and the unique active Launcher gateway through existing routing; never choose an ambiguous gateway or expose raw socket IDs. Bind each virtual folder to the socket and exposed root, recheck scopes on every operation, and reject stale folders after disconnect/root changes. Older connectors show an update/restart hint. Host settings remain in the CLI/Launcher; Files cannot change their scopes or exposed path. This is filesystem access, not a Launcher control surface.
- Browser bridge HTTP action/choice values must be strings before enum-set
  lookup; malformed JSON values return no-store HTTP 400 without state access.
- Production restricted handlers copy the WsManager-unwrapped payload and
  remove only its sanitized `correlationId` before strict hello and application
  decoding. Preserve the original transport payload for correlated ACKs and
  reject every other extra document field; ordinary CLI dispatch is unchanged.
- Advertise Launcher gateways additively through HTTP capability
  `launcher_gateway` and WebSocket feature `launcher_gateway_control`. Older
  ordinary CLI clients retain their existing protocol fields and behavior; do
  not provide a partial tools-only fallback when either feature is absent.
- A Launcher `connector_hello` carries a versioned gateway object with kind,
  stable ID, host label, and bounded status. Store it per authenticated socket,
  remove it on disconnect, and let context-bound CLI sockets retain routing
  priority. One unique Launcher gateway may be the global fallback. A duplicate
  socket with the same ID replaces stale state; distinct simultaneous IDs fail
  closed as Multiple hosts.
- `connector_gateway_control` and `connector_gateway_control_result` cover
  master state, complete scope replacement, and Disconnect
  (`emergency_disconnect` on the wire). Protected
  WebUI mutations require CSRF, await the matching acknowledgement, and return
  refreshed status. Apply acknowledged master and scope state to remote file
  and execution routing before resolving the control request; the follow-up
  `connector_hello` only reconciles metadata. Never let the WebUI select a host
  folder or personal browser profile.
- Launcher gateway scopes expose file reading and writing separately. File
  writing depends on reading, and Code execution depends on file writing. Keep
  older gateway declarations without `file_write` read/write compatible.
- Agent Zero WebUI exposes no Launcher gateway icon, menu, status, or control
  bridge. Host access settings, Disconnect/Reconnect, scope changes, and
  Computer Use approval belong only to attached or detached A0 Launcher chrome.
  Keep the authenticated gateway HTTP/WebSocket protocol available for the
  Launcher and connector runtime without adding a Core WebUI surface.
- HTTP capabilities and `connector_hello` advertise `transfer_protocol=1`.
  Eligible large file, exec, Computer Use, browser, and gateway requests/results
  use one symmetric start, ordered 64 KiB chunk, end, and abort contract with
  declared size and SHA-256. Bound each receive by the local ceiling, four
  concurrent transfers per SID, a 30-second idle timeout, and disk spooling
  above 1 MiB. Resolve a pending operation only after exact size, order, hash,
  JSON object shape, and operation ID all verify. Missing capability and legacy
  file chunks fail once with a structured error and do not disconnect the SID.
- Associate transfer state with the operation's existing context. Pause, reset,
  and delete abort matching transfers; disconnect aborts all SID-owned state.
  Mark outbound loops before emitting abort so raw payloads and pending futures
  are released promptly even when the peer disappears mid-frame.
- `text_editor_remote` is a bounded text control plane. Core must reject write
  and patch content over 256 KiB before creating a pending WebSocket operation;
  the CLI independently enforces the same ceiling. Reads return at most 2,000
  lines or 256 KiB with continuation metadata and reject binary-looking files.
  Prompts must direct complete or binary transfer to authenticated HTTP.
- Host browser status metadata may advertise `available_browsers` entries with browser ids, labels, CDP endpoints, status, and enabled state; keep older CLI payloads without those fields compatible.
- `computer_use_remote` action results may report `requested_dispatch`, `actual_dispatch`, and `foreground_fallback_used` (`fallback_used` legacy); these are output-only fields, not tool args. `scroll` reads `dx`/`dy` with legacy aliases `delta_x`/`delta_y`; document only canonical args in model-facing prompts.
- `computer_use_remote` reads legacy `name` as an `operation` fallback for element/ax/uia actions; it stays out of model-facing prompts.
- Advertise the Chrome extension bridge foundation additively; do not advertise pairing or runtime capabilities before those implementations exist. Legacy Chrome bridge detection is read-only, descriptor-anchored, bounded, and symlink-safe, and is confirmed only by exact prototype name/version plus at least two independent structural markers with no unavailable inspection. Inspect canonical roots in runtime precedence order: a higher-priority present partial or unknown copy blocks a lower-priority confirmed copy. Missing roots are absent, but present incomplete roots are partial and inspection failures are unknown; both partial and unknown block cutover. Public cutover projections are versioned and allowlisted, contain no paths, URLs, identifiers, payloads, credentials, or raw errors, and must not claim quarantine, draining, purge, or activation before those effects are implemented.
- Explicit legacy retirement is separate from read-only detection. Read
  `helpers/browser_bridge_legacy_retirement.py.dox.md` and its protected API
  DOX before editing its bounded process drain, journal, or request/tool guards.
  Do not auto-retire on startup, replay interrupted work, touch legacy browser
  tabs/credentials, or treat legacy disabling as production activation proof.
- Legacy context/history migration is owned by
  `helpers/browser_bridge_legacy_quarantine.py.dox.md`. Preserve removed values
  in private recoverable quarantine before exact-owner redaction. Generic
  persistence hooks and the bounded loaded-context sweep must not scan/delete
  arbitrary user artifacts or imply Chrome-local storage cleanup.
- Capability discovery may advertise `browser_extension_mv3_runtime_foundation` only when the schema helper is present. This is an effect-free contract/validation seam, not the negotiated `browser_extension_bridge_v1` runtime feature; it must not imply pairing, transport, dispatch, installation, or browser mutation readiness.
- Browser bridge pairing uses the instance rollout gate plus the server-pinned `A0_BROWSER_BRIDGE_EXTENSION_ID` and optional canonical `A0_BROWSER_BRIDGE_SERVER_BASE_URL`. `browser_bridge_pairing` uses normal `ApiHandler` session authentication and CSRF for exact create/status/cancel actions; only create may return the five-minute 160-bit code, and pending secrets remain bounded process memory. `browser_bridge_exchange` is the sole public one-time-code boundary, with an exact 8 KiB request, duplicate-key rejection at every JSON object depth, five generic failed attempts per intent, coarse bounded source rates, constant-time digest comparison, and atomic consumption into an allowlisted durable Ed25519 public-key record. Both routes use no-store responses and browser-host-only Docker semantics. Pairing discovery advertises `browser_bridge_pairing_v1`; it does not establish signed-session or browser-runtime readiness. Those require the complete production admission path below.
- The obsolete development bridge endpoints, credentials-as-authority, runtime
  owner and UI are retired. Only the fixed production transport is accepted.
  Do not migrate development keys or grants into production or delete private
  stored records during startup. Old selectors must fail without fallback.
- Browser bridge connector challenges accept only an active server-side bridge ID and a fresh 32-byte client nonce, then return a 60-second 32-byte server nonce. Challenge material and source-rate state are bounded process memory, and the first proof attempt consumes the challenge regardless of outcome. Verify the exact frozen proof with Ed25519 over fixed scalar-only RFC 8785 JCS bytes and derive the `browser_bridge` principal only from the active record. Signed sessions require WebSocket origin enforcement, ambient-cookie isolation, scoped handler activation, event filtering and disconnect cleanup; browser control additionally requires production runtime admission and reconciliation.
- The scoped-session adapter accepts the exact singleton connector
  proof envelope only after shared Origin validation. Recheck current server
  URL/instance and extension pin at authentication, and gate, active record,
  subject, extension pin, key generation and scopes during use. Bind only the
  immutable shared principal; keep `requires_auth()` true. Restricted SIDs
  never enter the legacy CLI registry or remote-tool metadata handlers.
  Without an installed application it remains hello-only, returning no features
  or exec configuration and reporting runtime readiness false. The composed
  production application admits exact hello through its registry before any
  other restricted dispatch; authentication alone never grants browser control.
- The browser operation broker is a bounded, process-memory-only dispatch seam,
  not runtime activation. It accepts authority and delivery only through
  injected adapters, and never reads the legacy connector registry or trusts
  hello metadata. Bind every pending operation/control immutably to the exact
  restricted principal object, SID, bridge, load generation, context, browser
  session, turn, action, and correlation IDs. Emit canonical nested browser
  requests with additive `bridge_id` and `load_generation_id` (and
  `browser_session_id` on cancel), validate all negotiated capabilities before
  send, and settle only an exact echoed binding. Caller cancellation never
  cancels the shared receipt future. Disconnect/send/deadline loss is
  `OUTCOME_UNKNOWN` for mutations and controls; only read-only work may return a
  retryable not-applied result. This seam correlates cancel, turn finalization,
  and exact pending-navigation site resolution; retained navigation metadata
  contains only target handle, canonical parameter hash, and destination origin.
  Site controls require a server-owned decision preflight and remain bounded by
  the pending operation deadline. Production composition supplies the attested
  capability authorizer and exact restricted sender; the broker alone cannot
  advertise or activate browser control.
- Broker transport tasks are retained and bounded separately from pending
  replies. Recheck current authority, negotiated capabilities, pending identity,
  and the injected site/turn preflight immediately before send. Process-owned
  deadlines survive waiter cancellation; a late response cannot bypass expiry.
  Only exact immutable turn bindings may enumerate pending operations for
  cancel-before-finalize cleanup.
- Persistent Browser bridge site policy defaults to exact canonical HTTP(S)
  origins keyed by current server instance, active bridge and server-derived
  subject. Production additionally supports explicit `allow_all_websites` via
  protected `set_mode`; it is never enabled by pairing or by an agent request.
  Store v2 adds bounded bridge-scoped mode records; legacy v1 grants remain
  unchanged. Project exact-origin grant IDs from the current mode generation
  without storing visited origins. Disabling the mode withdraws those derived
  grants while preserving individually saved sites. The protected, CSRF-checked
  policy endpoint accepts only bounded `list`, `allow`, `revoke`, and `set_mode`
  requests, resolves the
  active bridge before every action, and fails closed on invalid or unavailable
  durable state. Policy records never contain page URLs, content, operation
  arguments, or request-selected authority. This foundation does not mint
  one-operation approval receipts, dispatch Browser work, advertise runtime
  readiness, or enable Browser control.
- Saved browsing policy may automatically resolve only a genuine current
  native navigation challenge through the ordinary exact `allow_once` control.
  Retain its saved exact-origin grant ID and recheck it before control dispatch
  and receipt settlement; mode withdrawal or generation replacement invalidates
  that automatic choice. Never synthesize a native challenge, broaden its
  document/lease/operation scope, or auto-approve consequential actions.
- Consequential Browser action approval is a separate bounded, process-memory
  seam. Register only an extension-issued challenge ID bound to the exact
  current server-owned bridge principal, key and load generations, connector,
  context, browser session, turn, action, operation, tab handle, document
  identity and epoch, canonical parameter hash, target fingerprint, exact
  origin, and consequential action class. The
  protected decision endpoint accepts only `challenge_id` plus
  `approve_once` or `decline`; it cannot create challenges or supply authority
  bindings. Recheck the active bridge record, server-derived subject, and
  current route at registration, decision, and receipt consumption. Receipts
  expire within two minutes, authorize one exact consumption, and are denied
  on mismatch, cancellation, turn finalization, disconnect, revocation, or
  expiry. Production action authority supplies the exact route resolver and
  control dispatch. Standalone repositories default closed and cannot advertise
  readiness.
- Browser bridge context access is a purpose-built seam, separate from the
  legacy connector event projection. Bind advertised context IDs and
  subscriptions to the exact immutable bridge principal object, connector SID,
  and load generation, rechecking current route authority after every data
  source call. Subscribe, read, and message authorization may target only IDs
  advertised to that exact route. Project conversation text only from the
  actual Agent Zero `input`, `user`, and `response` log types; all other known
  log types may contribute only an allowlisted activity/status classification,
  and unknown structures are dropped. Never project Browser/tool result
  content, headings, kvps, scripts, selectors, paths, raw errors, page data, or
  attachments. Keep pages bounded while preserving cursor, history pagination,
  and completion state, and reject any nonempty source page that cannot advance
  its cursor. The default route authorizer remains fail-closed; production
  composition supplies registry authority and the separate context controller.
  This access helper neither changes legacy projection nor grants runtime readiness.
- The Browser bridge runtime registry is composed by the normal server-owned
  production bootstrap only under available rollout and a pinned extension.
  Normalize only the exact bounded v1 extension hello, and
  treat its browser label, capabilities, versions, limits, installation, and
  load generation as untrusted claims. Route admission requires a current
  companion stable semantic version at or above the independent `2.12.0`
  security floor (never a CLI-version equality or preview-version bypass), a
  server-instance-scoped immutable principal verification and an independent
  exact typed attestation that release trust, activation, legacy isolation,
  operation/control/context/event/artifact/approval transports, session
  lifecycle, and policy enforcement are all complete; both checks default
  closed and are repeated during route resolution, broker authorization, and
  result settlement. Bind one bounded route per server-derived bridge identity,
  replace reconnects or generation changes only for the same principal
  authority, remove old state before running fail-isolated exact-principal/SID/
  generation cleanup, and never consult the legacy connector registry. Context
  plus explicit `extension:<bridge_id>` selection must resolve before returning
  `ValidatedExtensionRoute`. The broker sender may emit only Browser operation
  and control events through shared `WsManager.emit_to` with the exact restricted
  handler and expected principal; it never broadcasts or supplies a fallback.
  Keep route admission and readiness denied while any complete-runtime
  boundary or production attestation remains unavailable. Server release
  approval requires the independently signed, bounded local policy and pinned
  public root; presentation catalog metadata never supplies release trust.
- Browser bridge text delivery targets only an existing context advertised to
  the exact current principal, SID, and load generation. Persist a hash-only,
  server/bridge/subject/context/client-message-bound hash reservation before
  any log or model effect, recheck authority immediately before delivery, and
  persist acceptance afterwards. Identical accepted reconnect replays return
  the original acknowledgement without another effect; changed payloads
  conflict, and reserved or uncertain delivery never retries automatically.
  Durable records contain hashes and timestamps, not conversation text.
  AgentContext owns the resulting task independently of presentation sockets;
  no attachment paths, global context switch, or legacy connector fallback is
  accepted. Message and queue receipts share `browser_bridge_journal`: new
  records use individually indexed atomic KVP writes, with the bounded original
  v1 records retained read-only as a fallback. Before the first indexed write,
  atomically mark that journal schema v2 without altering its receipts; older
  builds must reject it instead of overlooking new records during a downgrade.
  Existing receipts are never
  evicted; uncertain reservations never become fresh work. Disk use grows with
  distinct request IDs, but lifetime count does not block new messages. Store
  failures and malformed receipts remain fail-closed. Callers retain their lane
  lock across reservation, effect and settlement; no cross-process transaction
  or multi-worker ownership is introduced.
  Injected journal adapters use KVP-shaped `load(key, default)` / `save(key,
  value)` callbacks, including exact missing-default identity. Tests exercise
  the same indexed writes and downgrade fence as production, not a second
  whole-document storage implementation.
- `browser_bridge_application` composes the implemented current-route registry,
  exact context controllers, once-only messages, critical-event receiver, and
  Browser lifecycle/broker services under one explicit server owner. Its
  dispatcher resolves the retained generation from the exact principal/SID,
  never a client-selected route; unsupported event lanes fail closed and never
  enter legacy connector handlers. Route retirement removes lookup authority
  before negative lease/projection cleanup, and explicit disconnect awaits only
  presentation and artifact teardown. Artifact frames resolve only an exact
  pending operation whose action matches the output purpose, and private spool
  access additionally requires the same still-active turn and current route.
  Verified output consumption may outlive operation settlement, never turn or
  route authority. Construction does not broaden authentication, install
  the Browser factory, advertise capabilities, or attest missing transports.
- Restricted queue dispatch reuses Core message_queue only for exact owned
  text entries, with advertise-before-message checks, hash-only durable
  reservations, bounded projections and no global queue clear. Local approval
  dispatch derives the current route and subject, then requires exact retained
  principal/SID/load/profile inside the site/action repository lock. Their
  helper sidecar DOX defines the strict bodies and uncertain outcome behavior.
  Neither lane enters legacy connector handlers. runtime_boundaries reports
  only implemented owned lanes; artifact requires output plus the concrete
  input source/sender/ACK/consent/sink composition, not output support alone.
- `browser_bridge_bootstrap` is the only optional process-global owner for a
  fully composed Browser bridge application. Importing it installs nothing.
  The enabled connector's `webui_server_start` hook installs the configured
  owner inside each ASGI lifespan before serving requests and registers
  manager-qualified retirement on that lifespan's shutdown stack. Startup
  retries install afresh only after the prior owner retires. Core retains the legacy
  HTTP retirement guard regardless of connector enablement.
  Without an explicit binding, newly authenticated principals remain
  hello-only and the existing unavailable response is unchanged. With a
  binding, freeze the full bridge-only inbound/outbound event sets into the
  immutable principal, atomically register exact hello through that owner, and
  route every other restricted event only to its dispatcher. Missing owners,
  stale principals, and unadmitted SIDs fail closed without legacy fallback.
  Successful hello returns negotiated capabilities, exact typed activation
  evidence, and a transport-private server/bridge/SID/key/load binding only
  after current admission. It never returns exec configuration, context state,
  proof/key material, raw claims, or subject identity. Do not expose the
  connector binding in WebUI/status. Replacement or removal must use the exact
  async owner-retirement path: hide it from new routing, await application
  cleanup, then clear the site API binding. Never synchronously unbind or
  replace an installed owner, construct an application from a request, or treat
  installation as a cutover/activation bypass. Binding additionally requires
  that the application has explicitly acquired its exact Browser factory and
  lifecycle ownership; construction alone is not installation. Retirement
  withdraws only those owned seams before route cleanup. An exact same
  principal/SID/load hello replay refreshes server admission without invoking
  disconnect cleanup. Only successful exact reconciliation promotion may
  schedule already-durable finalizations; neither initial nor provisional
  repeated hello may replay them.
- Runtime admission additionally requires an immutable activation attestation
  from independent server-owned selection, heartbeat, subject/profile and
  legacy-cutover checks, bound to exact principal/server/SID/load/install and
  negotiated features. Aggregate ready flags or client hello fields cannot
  substitute. Evidence is valid for at most 30 seconds, is reevaluated at route
  lookup, and serializes only the frozen activation projection after matching.
- Browser bridge context-event control is an isolated exact-route presentation
  lane. Accept only strict list, subscribe, unsubscribe, and existing-context
  text requests; empty artifact/candidate placeholders convey no authority.
  Emit only bounded projected snapshot, event, and completion frames through
  shared `emit_to` with the exact restricted principal, SID, load generation,
  and handler. Preserve source and history cursors, recheck the current route
  around reads and delivery, and include the source update cursor separately
  from each stable item sequence on live events. Do not publish a page-end
  cursor until its last visible event is emitted. Retain at most one poller per exact
  route/context. Healthy subscriptions remain live until explicit unsubscribe,
  disconnect, route loss, or source failure; cleanup cancels the presentation
  reader only and never the AgentContext task. The production application wires
  this controller only to admitted, reconciled restricted routes; the unbound
  bootstrap remains hello-only.
- Critical Browser bridge events use a separate durable hash-only receipt lane.
  Accept only the exact critical `lease.changed`, `turn.finalized`, and
  `challenge.required` site/action envelopes
  for the current server-owned principal, SID, key/load generation, and
  `browser.operate` scope. Persist event-ID and canonical-event hashes before
  any callback, invoke only idempotent negative lease invalidation or an
  informational finalization observer, or exact site/action-challenge registrar, then
  advance the durable cursor across applied contiguous sequences only. A site
  registration failure is replayable and cannot advance the cursor. Passive lease creation never grants or
  invalidates authority, callback failure never advances the cursor, gaps never
  ACK forward, and old-generation replay cannot replace current state. Emit the
  generation-qualified highest-contiguous ACK only through exact restricted
  `emit_to`; never persist event payloads or treat finalization notice as a
  control-result receipt. Keep unsupported critical kinds and production
  activation fail-closed.
- Consequential click/TYPE authority composes the bounded once-only approval
  receipt only after matching the exact current pending action, canonical
  parameter hash, owned lease digests/origin, semantic document ID/epoch, and
  requested ref. TYPE retains only its verified UTF-8 text digest and binds the
  immutable sensitive-text classification through event, receipt, control, and
  grant; raw text exists only in the transient operation transport.
  The protected API accepts only a context-qualified safe list request or
  challenge ID plus `decline`/`approve_once`; the request context only selects
  current agent0 project/profile configuration, while pending results omit
  context and Browser IDs, and include only the server-owned `click`/`type`
  discriminator. Recheck the server-selected exact extension bridge
  throughout challenge and control lifecycle. Consume the hidden receipt after a final current-route preflight
  and immediately before queuing one exact resolution control. Keep the control
  task process-owned, same-choice replay idempotent, changed-choice replay
  denied, and all authority operation-only and bounded by the live operation,
  challenge, and two-minute ceiling. Do not persist or expose typed text, text
  digests, refs, raw page data, full URLs, target hashes, receipts, or grants,
  and do not infer TYPE or readiness from approval support alone.
- Site-origin runtime authority is separate from durable saved-site policy and
  general consequential-action approval. Register a `site`/`navigate`
  challenge only after matching its exact current broker operation, retained
  canonical parameter hash and destination origin, owned lease-handle digests,
  and recomputed generation/document target fingerprint. The protected site
  decision endpoint derives the subject and accepts only challenge ID plus
  `deny`, `allow_once`, or `allow_turn`; its list exposes only canonical origin,
  action class, server-generated summary, fixed options, and expiry. Retain no
  full URL or extension summary. Mint no grant until the exact correlated
  resolution result arrives. Operation grants authorize only their original
  live ticket. Turn grants require an injected exact live-turn check and current
  server/principal/SID/load/context/session/turn route, expire within two hours,
  and auto-resolve only a fresh challenge that matches that same current grant.
  Finalization, disconnect, revocation, mismatch, and expiry remove authority.
  Keep state and retained resolution tasks bounded, global binding explicitly
  unavailable without its application owner, and responses no-store. Site
  permission never substitutes for production activation.
- Browser companion release metadata is a read-only, normally authenticated and CSRF-protected WebUI projection of server-pinned public catalog data. Advertise only `browser_companion_release_metadata` for endpoint discovery; that feature does not assert installer, pairing, release, or browser-runtime readiness. Use the distinct `a0.browser-bridge.release-metadata.v1` presentation contract, report only `available` or `unavailable`, and keep `install_ready: false` because Core does not verify release bytes. The endpoint is unavailable until canonical catalog URLs, catalog-key fingerprint, protocol/trust compatibility, the independent non-lowerable server companion security floor, and the complete signed delivery artifact matrix validate. Reject malformed/nonempty request bodies and request-supplied URLs, paths, extension IDs, or overrides; never expose raw configuration, signing/private keys, server credentials, or native paths, and never download or install anything in the Agent Zero or Docker runtime. Every projection must identify the user's browser host as the install target. Core validates presentation metadata shape and compatibility only; the browser-host installer/CLI verifies the detached catalog signature against its own pinned public root and verifies artifact bytes before execution.
- Browser reconciliation uses a distinct process-owned binding for the exact
  fixed transport profile, principal object, connector SID, load generation,
  and control ID. Validate the complete bounded extension snapshot, but retain
  only redacted counts; never adopt peer lease/provider claims, settle pending
  actions, apply embedded critical events, or ACK their cursors. Recheck exact
  route authority throughout request and result handling. Atomic route
  promotion must run synchronously inside matching broker settlement before its
  future is delivered, without awaits or blocking and with consistent owner
  lock ordering. A following FIFO event still has no authority unless that
  compare-and-promote succeeded. Caller cancellation does not cancel the owned
  reconciliation task; the production route owner remains responsible for retiring
  provisional routes and disconnecting broker tickets. This helper creates no
  principal, admission, selection, Browser factory, or activation.
- Browser bridge artifacts use a separate bounded, process-memory receiver with
  generated private spools; never reuse the generic connector file assembler.
  Bind every transfer to the exact immutable bridge principal object, connector
  SID, key/load generation, context, browser session, turn, action, operation,
  artifact, direction, and standard purpose. Revalidate the injected current
  route before begin, append, completion, and the single authorized consume;
  authorization loss deletes the exact spool. Require ordered 192 KiB-or-less
  chunks, a declaration no larger than 25 MiB, and exact final byte count and
  SHA-256 before exposing a pathless descriptor. Delete spools on consume,
  abort, expiry, disconnect, revocation, or receiver shutdown. This private
  assembler does not wire transport, materialize chat media, or advertise
  Browser runtime readiness.
- The Browser artifact transport controller accepts only strict output
  `screenshot` and `download` begin/chunk/end/abort frames. Resolve a
  server-owned pending-operation `ArtifactBinding`, then compare the principal
  object and every SID, generation, bridge, context, session, turn, action,
  operation, artifact, direction, and purpose echo before touching a spool.
  Re-resolve that pending binding after each receiver transition and purge the
  exact transfer without acknowledging if operation authority disappeared.
  Decode only canonical standard base64 chunks within the 192 KiB raw and 768
  KiB frame limits. Acknowledge progress, a verified pathless descriptor, or a
  bounded typed abort only through exact-principal `emit_to`; never infer a
  duplicate chunk. One controller-owned expiry task starts on first accepted
  begin and stops when globally idle. Disconnect cleanup targets only the exact
  principal/SID/generation, while controller close owns receiver shutdown.
  The complementary input sender is wired to exact restricted ACK dispatch,
  binds immutable server bytes to a current upload operation and live turn,
  and requires the server-owned source/site preflight. Await the exact broker
  wait_dispatched barrier before the first input frame. It bounds each frame
  and transfer and never retries uncertain sends. Native defers the operation
  until verified input completion; extension one-use external-side-effect
  consent remains required before setting the visible, empty single-file field.
- Model preset definitions exposed through v1 are global; project arguments select scope but never create project-owned definitions. Model switcher state reports the effective main, utility, and embedding models and preserves embedding-change notifications.
- The capability-gated `composer_controls` API is authenticated and CSRF-protected. Dispatch `connector_controls` through the existing agent-scoped extension loader, not a separate registry or arbitrary URL/code dispatcher. Plugins own descriptors, domain validation, revisions, and mutations; Core and the CLI must not name optional plugins. The list/set contract is documented in [README.md](README.md). An absent or scoped-out control returns 404 on set; older clients remain unaffected.
- The protected v1 `agent_editor` route delegates to the bundled Agent Editor
  API and must not define another profile schema or write profile files itself.
- The protected v1 `agents_list` response uses the shared agent presentation
  catalog rather than applying connector-specific visibility rules.
- Computer Use receipts describe transport success unless the connector returns explicit effect evidence. Linux target-bound typing requires a verified active/focused `window_id`; window activation uses focus, never a press action on an application or window node. Do not retry an identical failed Computer Use call.
- Accepted WebSocket user-message replay metadata may include attachment basenames only; strip paths, query strings, fragments, and bytes before logging them in `kvps`.
- Protected Browser bridge inventory uses the normal authenticated and
  CSRF-protected `ApiHandler` boundary and remains available when rollout is
  disabled or the configured extension pin changes, because credential cleanup
  cannot depend on activation. List/detail records only for the current server
  and subject, projecting `bridge_id`, safe display name, state, key generation,
  and creation/authentication/revocation times; never expose public/private key
  material, companion/extension/server identifiers, SIDs, scopes, URLs, or
  browser data. Revoke idempotently under the pairing store lock shared with
  exchange and authentication updates, preserving the first revocation time.
  After durable denial, request exact matching restricted Socket.IO sessions to
  disconnect through the framework callback; a failed callback is reported only
  as pending server-session cleanup. Neither outcome claims native-key deletion,
  browser-action cancellation, lease finalization, or Chrome tab closure.

## Work Guidance

- The protected site-authority API also projects the production Browser
  service's separately owned first-open requests. `open-site-` IDs select that
  server-only lane; no native challenge, resolution control or receipt is
  fabricated. See the API and `extension_first_open` sidecars. Exact route
  retirement withdraws its pending requests and temporary grants before they
  can authorize further work. Only its explicit `allow_site` decision writes
  exact-origin saved policy from retained server/bridge/subject/origin fields;
  successful persistence/readback precedes waiter release. Native navigation
  decision enums remain unchanged.

- Private production handshake/reconciliation diagnostics log only a fixed
  allowlist of stage/failure symbols, at most five entries per symbol per
  process. Never include identities, exception text, peer payloads or paths;
  these logs are diagnostic observations, not readiness authority.

- Production hello transport admission stays provisional until an exact
  process-owned reconciliation promotes the route. The first repeated hello
  starts reconciliation only after the initial native ACK has been consumed;
  initial hello sends no controls. Pending finalizations replay only after
  promotion. Current context/operation/status authority requires promotion,
  whereas exact reconcile settlement is allowed while provisional. Retain no
  peer lease authority; replacement and failed reconciliation fail closed.

- Production selection supports one explicit global default through the
  protected selection API, independent of a loaded chat. Exact previous-default
  fencing, active-pair validation and global-only readback are mandatory;
  project/profile overrides remain untouched. A global default may satisfy
  hello selection evidence, but each context operation still requires its own
  effective selection and existing site/action consent. See selection and
  runtime-owner helper/API sidecars for the strict projection contracts.

- `browser_bridge_setup` is a normally authenticated, CSRF-protected read-only
  WebUI projection of enabled production extension identity and configured
  installer links. See its API/helper sidecars. Release presentation input v1
  requires all nine artifacts; v2 requires sorted unique nonempty known platforms
  and the exact union of complete groups. Neither is catalog-signature proof;
  host verification remains mandatory and unsupported OS links remain absent.

- `browser_bridge_credentials` owns interruption-safe public-key generation
  rotation under the pairing lock; its sidecar documents exact-key CAS and
  expiry. `browser_bridge_credential_control` owns current-production-principal
  rotation/status/self-revoke dispatch, durable denial before process-owned
  negative socket cleanup. The native private-key workflow is independently
  required and neither helper supplies release or activation evidence.

- Coordinate connector runtime changes with API, tools, prompts, and WebUI viewer behavior together.

## Verification

- Run connector-specific tests or smoke-test HTTP and `/ws` integration when changing runtime behavior.
- Run `tests/test_remote_input_policy.py` for default access without editor grants, remote-input authorization, zero dispatch on denial, prompt/schema gating, and preserved host access controls.
- Run `python -m pytest tests/test_a0_connector_chat_search.py plugins/_sidebar_folders/tests/test_search.py -q` for the query branch, unchanged list shape, input validation and shared excerpt behavior.
- Cross-platform first-call session startup and no-retry boundaries are covered in the sibling connector's `tests/test_plugin_backend.py`; Core prompt gating remains covered by `tests/test_a0_connector_prompt_gating.py`.
- Launcher gateway regression coverage lives in
  `tests/test_a0_connector_launcher_gateway.py`.
- Generic composer control dispatch, scope, validation, and security contracts are covered by `tests/test_a0_connector_composer_controls.py`.

## Child DOX Index

No child DOX files.

Host Files forwards Core transfer/text limits without an independent HTTP cap. Older Connector clients retain their existing cap until updated and restarted.

- The host provider implements the same streaming `read(relative, destination, limit)` / `write(relative, source, expected)` contract as the five community providers. HTTP file bodies stay in private temporary files and shared bounded copies; no whole-file bytes return from provider reads.

- Incoming host HTTP transfers pass the upload stream to `file_transfers.write_stream_atomic`, retaining integrity receipts and the operation limit.
