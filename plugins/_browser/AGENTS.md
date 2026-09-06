# Browser Plugin DOX

## Purpose

- Own the built-in Patchright browser tool and WebUI browser viewer.
- Bridge browser automation, page inspection helpers, and browser panel UI.

## Ownership

- `plugin.yaml` and `default_config.yaml` own metadata and browser settings defaults.
- `tools/browser.py` owns the agent-facing browser tool.
- `helpers/` owns the Patchright runtime, private interactive display, selectors, URL helpers, extension management, and connector runtime logic.
- `api/` owns status, extension, and browser WebSocket handlers.
- `assets/`, `prompts/`, `skills/`, `extensions/`, and `webui/` own browser scripts, prompts, skill guidance, hook contributions, and UI.

## Local Contracts

- Extension target origins come from a bounded process-only index populated by
  exact correlated successful open results, not caller handles or URL guesses.
  Require distinct lease and tab identities, the requested granted origin, and
  the expected disposition; bind entries to the exact current principal, SID,
  generation, context, and browser session. Do not retain titles, full URLs,
  page payloads, or provider IDs. Withdraw entries when finalization begins or
  authority is invalidated; the extension independently verifies every live
  lease/document. Reconnect recovery cannot silently restore target authority.

- Keep browser actions safe around external pages, credentials, and user data.
- Preserve Patchright lifecycle cleanup and WebSocket viewer compatibility across regular host browsers and Electron WebContentsView embedding.
- Keep the WebUI Browser inside its own modal/canvas affordance; do not replace it with page-level navigation.
- Default the visible WebUI Browser to the authenticated Xpra HTML5 viewer for its existing Patchright page. Keep live CDP screencast and lightweight snapshots as automatic fallbacks.
- Do not block an available interactive viewer on a redundant Chromium screenshot; capture initial snapshots only for fallback transports.
- Keep headful Chromium in a normal window with its own toolbar clipped above the private display; do not use browser fullscreen, which shows Chromium's exit warning.
- Persist open-tab ownership and URLs through the shared KVP store; automatically restore the current chat when its Browser surface opens in per-chat mode and every saved chat in shared mode, then hide Chromium's redundant crash-restore advisory.
- When no Browser tab manifest exists yet, use Chromium's last session once to migrate open tabs into the owned manifest.
- Throttle interactive resize updates throughout a drag and let the native-sized Chromium viewport follow the private display; do not defer all layout updates until resizing stops.
- Keep exactly one interactive viewer iframe connected during canvas/modal handoff so hidden surfaces cannot compete to resize the same display.
- Notify the active Xpra client of its new frame geometry before resizing the backing display; after an interactive canvas/modal handoff, reconcile once after Xpra's deferred resize so Chromium cannot retain the previous surface size.
- Present the Xpra shadow window as the raw browser canvas: remove its HTML decoration and shadow pointer while preserving exact viewport geometry.
- Keep one internal Chromium, Xvfb, and Xpra runtime per Agent Zero process with one unguessable gateway token.
- Bind Browser Xpra endpoints to loopback, route them through the authenticated virtual-desktop gateway, and keep file transfer, URL opening, printing, and audio disabled.
- Paint live screencast frames through the Browser panel canvas/ImageBitmap path when available; keep the `<img>`/data URL path for snapshots and fallback rendering.
- Push internal screencast frames from the runtime to the WebSocket consumer after subscription; keep `read/pop_screencast_frame` as fallback/tooling APIs, not the WebUI hot path.
- Keep Browser viewer frame transport capability-negotiated: updated clients may request binary/slim screencast frames, while older clients must keep the base64/full-metadata fallback. Do not let the WebUI advertise binary frames unless its Socket.IO client reconstructs attachments as real `Blob`, `ArrayBuffer`, or typed-array values.
- Keep WebUI Browser tabs scoped to the active chat context by default; aggregate tabs from other context handles only when the Browser settings tab scope is `shared`.
- Share one persistent internal-Browser sign-in profile across chats while enforcing tab ownership through context-bound runtime handles; resetting or removing a chat closes only its tabs and never deletes the shared profile.
- On first shared-profile use after an upgrade, adopt the first requesting chat's legacy Browser profile when one exists.
- Show an accessible in-panel startup state while the on-demand shared Browser runtime is cold-starting; keep that one runtime warm until Browser configuration changes or Agent Zero shuts down.
- Keep narrow WebUI Browser controls usable by grouping navigation with Annotate/settings above a full-width address bar.
- For Bring Your Own Browser with an existing host profile, `host_browser_selection` may target automatic host selection, a browser family/id, an HTTP CDP discovery address, or a full DevTools WebSocket endpoint and must be forwarded to the connector runtime as `browser_selection`.
- Reserve `host_browser_selection=extension:<bridge_id>` for the typed Chrome-extension backend. Preserve an already-stored valid selection exactly; new selections require the protected production selection API, active paired record and project-scoped readback, never generic config writes. Allow clearing or switching to `container`. A change retires the exact former bridge route before writing shared config. Reject malformed reserved values. When `host_required` activates an extension selection, never route it through the internal browser or a legacy A0 CLI candidate; until the extension runtime is available and enabled, fail with repair guidance and no browser mutation. The top-level `container` backend continues to ignore host-browser selection.
- Keep the instance-scoped `A0_BROWSER_BRIDGE_ROLLOUT` gate limited to `disabled`, `preview`, and `available`, with missing or invalid values failing closed to `disabled`. Never persist this gate in per-project Browser settings, and gate configuration never selects a browser. Browser status adds a versioned, identifier-redacted `extension_bridge` scope without changing or removing existing status keys; the additive scope must report unavailable project or remote evidence as `not_checked` or `unknown` rather than inferring health.
- MV3 discovery preserves the runtime, adapter and protocol identifiers and its
  disabled response shape. Its validation flags are false: actual lease and
  finalization validation belongs to `extension_sessions`, `extension_leases`
  and the operation broker, not duplicate discovery-only types. This static
  metadata is not connection status. The native runtime stays on the browser
  host, never in Docker.
- Browser status may project the `a0.browser-bridge.trust.v1` pairing foundation and whether its server-side create/exchange gate is configured, but it must not project the pinned extension ID or any pairing code, public key, bridge identity, session proof, or remote-health inference. Pairing availability never makes connector-session or browser-control readiness true.
- The extension-browser lifecycle registry is created only for an explicit
  `host_required` plus exact `extension:<bridge_id>` selection with a current
  restricted route. Keep its KVP state bounded to opaque context/session/turn
  IDs, the selected browser/bridge, lease dispositions, lifecycle tombstones,
  an event cursor, and timestamps; never persist route authority, SID/load
  generation, Chrome IDs, URLs, page content, selectors, scripts, or typed
  input. A session stays pinned to one bridge, while each monologue gets a
  fresh turn.
- Extension turn finalization is process-owned, idempotent, and exact-bound.
  Missing authority leaves a durable pending intent, transport uncertainty is
  retained as `outcome_unknown`, and even a successful control receipt must
  not be presented as proof that remote tabs were closed. Lifecycle hooks stay
  inert until the restricted route resolver and broker-backed sender are
  explicitly injected; container and legacy browser behavior is unchanged.
- Browser Settings may create, poll, cancel, regenerate, and explicitly copy a five-minute pairing code through the protected pairing API. Keep the code only in the open Alpine panel, clear it on cancel, expiry, replacement, and teardown, and never write it to project config, local/session storage, URLs, logs, or the public exchange endpoint. Status is an allowlisted redacted projection, and the panel must state that the companion/private key belong on the browser computer rather than in Agent Zero's Docker container.
- Browser Settings recognizes production `extension:` selections independently
  of legacy A0 CLI/CDP settings; never ask production users to enable remote
  debugging or keep CLI open. Pairing is saved, but authoritative current-chat
  readiness remains separate. While the panel is mounted and visible, refresh
  pairing, paired inventory and selection read-only; preserve typed site drafts,
  exact context/generation fences, explicit selection and site consent. A single
  Check connection action refreshes all production setup projections. Setup links
  come only from the protected public setup API; OS suggestions use the visiting
  browser, not Docker. Missing OS artifacts have no download fallback.
- Browser Settings must refresh connected host-browser inventory while the settings view is open so newly authorized endpoints appear without saving or reopening.
- Browser Settings keeps the Host browser dropdown focused on automatic selection, stable IDs for advertised debug endpoints, and advertised Safari WebDriver targets instead of listing every installed local profile. Describe host access as available through Launcher or A0 CLI without presenting the CLI as the only runtime. Present host-browser setup without an outer container treatment: Chromium-family guidance comes first on the left and Safari/macOS second on the right, with narrow layouts stacking naturally and manual endpoint fallback progressively disclosed. Chrome, Opera, and Edge setup buttons appear only when a compatible connected host advertises that installed browser, then use the authenticated connector bridge to open its fixed internal inspect page; mention Brave, Vivaldi, and Chromium without adding more primary buttons. Safari guidance must name Safari Settings > Advanced > Show features for web developers and Developer > Allow remote automation, and explain its dedicated automation window. An exact legacy endpoint advertised by a connected host migrates to that browser's stable ID in both settings and runtime operations; unmatched custom endpoints remain exact and fail closed. Preserve endpoint path/query case and let the connected host resolve discovery addresses.
- Browser URL-intent handling must only claim web URL schemes and leave custom Agent Zero schemes to their owning surfaces.
- Prefer DOM/CDP browser actions with refs, selectors, frame-chain refs, and screenshots over viewport coordinate input. Coordinates remain a visual fallback.
- Do not hardcode user-specific browser paths or secrets.
- Browser model-preset selection resolves omitted preset fields from `_model_config`'s global `Default` preset, not from an unrelated currently scoped model selection. After the first Browser tool call, use the selected preset for subsequent model turns in that monologue and clear it at monologue end.
- Do not inject open-browser state into the system prompt when profile policy
  blocks the Browser tool.
- Annotation mode highlights the DOM element under the pointer, keeps saved overlays page-local, and may batch annotated pages only within the active chat context.
- Annotation voice input reuses Whisper STT's configured draft/send delivery mode and shared microphone state.
- Internal-browser proxy settings map directly to Playwright's persistent-context proxy option, never to Bring Your Own Browser, and changes must restart active internal runtimes.
- Run internal Chromium headful through Patchright on the private virtual display; do not add user-agent or header spoofing on top of the patched driver.
- Browser keyboard layout settings (`keyboard_layout`/`keyboard_variant`, e.g. `de`/`mac`) apply the configured XKB layout to the private browser display with setxkbmap and pin it on the Xpra shadow server so non-US keyboards type their printed characters; layout changes flow through `browser_runtime_config` and restart internal runtimes. Fallback canvas input forwards AltGraph and macOS Option text without converting ordinary Alt shortcuts into text.
- Browser startup and on-demand launch must converge on the Chromium revision declared by Patchright; let its installer select the host architecture rather than hardcoding x64 or ARM downloads.
- `hooks.prepare_playwright_cache()` owns reconciliation of the pinned Patchright package and Chromium binary so repository self-updates and fresh images use the same setup path.
- Browser startup must install the shared virtual-desktop route hook itself; do not make Browser depend on the Desktop plugin being enabled.

## Work Guidance

- The existing server-resolved `autofocus_active_page` setting also requests
  foreground display for production Chrome open/hover/click/type/scroll/upload
  operations. Read the current agent-scoped setting after any site-approval
  wait; missing or failed settings evidence leaves foreground false. This is
  presentation only: existing route, lease, site and action checks still gate
  dispatch. Never accept a foreground override from tool arguments or focus
  tabs for passive events, list/state/content/navigation or status.

- Production selector acquisition may wait up to 25 seconds for the exact
  already-installed factory owner and unchanged current selection to obtain a
  verified reconciled route after reconnect. Recheck gate, owner and selection
  at every bounded poll; withdrawal, replacement and cancellation stop the
  wait. No operation or consent request is sent or replayed by acquisition.
  Missing factory returns immediately. Failure guidance must describe an
  unverified connection, never falsely claim this release lacks the runtime or
  recommend another browser/tool to bypass the selected host. An earlier
  unknown-effect operation remains unknown and must not be repeated.

- `extension_first_open` owns a separate production-only, process-memory
  approval before an owned tab exists. Its sidecar defines exact request/turn
  fences, bounded waiting and resulting-lease access. Never invent a native
  navigation challenge. Only the explicit production first-open `allow_site`
  choice persists exact-origin saved policy, with successful readback before
  dispatch; once/turn decisions stay temporary. Its primary UI control says
  “Always allow site” and explains that access is remembered across chats.
  Keep consent in a compact theme-native strip: exact origin and scope beside
  the primary choice and Deny; put once/turn alternatives and settings-based
  removal under More options. Do not hide the origin or saved-scope meaning.
  The protected site inbox accepts production `open` and `navigate` requests;
  Permission denial or expiry must give
  explain-to-user guidance, never suggest curl, code_execution_tool, another
  browser or another tool as a way around consent.

- `extension_uploads` and the user_message_ui source hook own the bounded
  current-chat attachment registry and immutable source-byte check. The sidecar
  defines the no-arbitrary-path rule, per-context metadata, no-follow reads and
  upload permit lifetime. Runtime/services send only opaque descriptors after
  exact operation dispatch; staging is not the separate site-upload approval.

- `helpers/extension_runtime.py` is a separate canonical Browser-tool codec, not
  a subclass of the legacy CDP runtime. It currently supports the negotiated
  open/list/state/content/navigate/ref-scroll/ref-hover/viewport-screenshot/ensure/status subset, rejects
  selectors, scripts, caller policy IDs, numeric provider IDs, unsupported
  actions and unverified artifacts/receipts. Cross-origin navigation requires
  an explicitly composed site challenge lane; the source-origin permission
  can only start that wait, never approve the destination. Exact
  route/session/turn bindings and target origins are injected server-owned
  services; persistent exact-origin policy is rechecked at queued dispatch.
  Cancellation schedules an exact bounded broker control without claiming
  rollback. The selector can use only an explicitly bootstrapped factory under
  the available instance gate, with exact context/bridge readback. Its default
  is unconfigured and unavailable; importing this adapter never activates or
  selects the extension or falls back to another browser.
- The negotiated semantic-ref click codec always supplies expected risk `unknown`,
  rejects caller risk downgrades/modifiers/coordinates, and requires a composed
  action authority before initial and queued dispatch. Its three transport
  layers and protected decision UI are composed; full activation is separate.
  Correlated content results alone may populate the bounded process-local
  lease document index with document ID, epoch, and opaque refs; no labels,
  page text, or challenge-supplied identities enter that index. Navigation,
  successful click, lease invalidation, and turn retirement withdraw cached
  document authority. A click receipt never authorizes a second click.
- `extension_artifacts` consumes one exact screenshot descriptor from the private
  verified receiver, rechecks the retained lease and active turn/current route,
  validates bounded JPEG/PNG bytes, and uses the existing Core-owned chat media
  destination. Peer paths, additive result fields, mismatched descriptors and
  raw image bytes never enter tool results. The `screenshot_file` codec maps
  explicit bounded JPEG quality, rejects full-page/custom-path requests, and
  requires an installed materializer before sending. No production capability
  is inferred merely from this composition seam.
- `helpers/extension_services.py` composes that codec with the hook-owned
  lifecycle and restricted broker. Direct calls get an exact synthetic turn
  finalized in `finally`; monologue calls keep their existing turn. Production
  bootstrap must supply `get_extension_session_lifecycle()`, not
  a separate instance invisible to monologue hooks. Successive tool calls in
  one monologue share the exact turn/session and retain its owned lease until
  real monologue finalization; direct calls remain independently finalized.
  Revalidate real/synthetic ownership at dispatch. Finalization cancels only pending
  operations from the same principal/SID/generation/session/turn, then waits for
  the exact control acknowledgement; transport errors or per-lease errors
  persist uncertainty, not a tab-closure claim. This explicit bootstrap seam is
  not installed by configuration, imports, or client hello metadata. Runtime
  factory and lifecycle installation are exact-object-owned and reject a
  competing owner; uninstall withdraws only that service's factory, makes new
  hooks inert, and durably stages tracked cleanup with the established
  `restarted` reason before configuration can be reused. It never cancels an
  in-flight finalizer or converts missing-route cleanup into `not_applied`.
- Only the fixed production transport owns Browser factories and lifecycle.
  Monologue, direct-call and context cleanup hooks delegate directly to the
  same `_lifecycle` singleton; do not reintroduce multi-channel fan-out.
  The retired `development-extension:` namespace remains reserved solely to
  reject stale settings without CLI/CDP or container fallback. No old keys or
  site grants transfer into production; users must explicitly pair and select
  the production extension. The production unpacked build uses this same path.

- The extension Browser panel's `browser-site-requests` component presents
  exact server-listed pending site requests as plain canonical origins, never
  page-provided descriptions. Send only challenge ID and explicit user decision;
  receipt acceptance is not navigation success. Poll only while mounted, fence
  asynchronous responses by generation, reject expired decisions, and destroy
  timers/view state on teardown. Never persist grants or infer runtime readiness.
  Normal decision acknowledgements disappear after three seconds using the
  existing polling clock; uncertain decisions retain their bounded warning.
- Composer approval inboxes stay visually absent when empty, including the
  pending site and action lanes. Successful decision notices expire after three
  seconds on the existing poll clock; uncertain decisions remain visible until
  their request expires. Both request stores retain known unexpired
  current-chat prompts on list failure, with decisions disabled until a valid
  list succeeds. One presentation-only coordinator reports a shared outage
  through the A0 notification center once per chat/outage, without a composer
  recovery control or toast. Existing read-only polling recovers automatically.
  It never filters pending consent by connection-status guesses,
  grants authority, or retries an uncertain decision.
- `browser-bridge-access-store.js` owns the replaceable WebUI view of paired
  browsers and saved exact-origin permissions. It uses protected bridge/policy
  APIs, keeps drafts and IDs only in the mounted panel, drops stale responses
  after teardown or host selection, and confirms revocation before sending.
  Inventory remains usable when rollout is disabled. Revoke/allow responses
  never imply native-key deletion, tab closure, or runtime readiness. Transient
  outcomes use frontend-only Agent Zero notifications, not inline alert boxes.
- Its production All websites control requires explicit confirmation, sends
  only selected bridge and bounded site mode to the protected policy endpoint,
  and updates from exact readback. Fence confirmation/replies on mounted bridge
  generation. Explain persistent across-chat browsing and separate action
  approvals. Turning it off preserves individually saved sites. First-open
  uses the repository's exact-origin derived grant before creating a prompt;
  no site request is necessary while that explicit mode is current.
- `browser-bridge-selection-store.js` owns explicit production Use this Chrome
  browser and confirmed internal-browser default actions, including without a
  chat. The protected default-selection contract checks the previous global
  bridge as a compare-and-swap precondition. Existing project/profile overrides
  stay unchanged and appear as a separate current-chat projection. It uses only the
  protected selection API, fences replies by chat/mount generation, and refreshes
  the modal's own settings scope after authoritative readback. Selection is not
  readiness and never creates a new pairing or site/action grant.

- Coordinate tool, helper, and panel changes so browser state shown in the UI matches tool behavior.
- Do not depend on nested Electron `<webview>` support or launcher-specific preload bridges unless the launcher exposes that bridge as an explicit contract.
- Keep `prompts/agent.system.tool.browser.md` as a compact callable contract; move detailed browser workflows into `skills/browser-automation/SKILL.md`.
- Keep `skills/browser-automation/SKILL.md` frontmatter triggers current with rendered browsing, host-browser, screenshot, and web-interaction user phrasing so relevant-skill recall can surface the skill before the full browser workflow is needed.
- Keep fragile form guidance progressively disclosed through `skills/browser-form-workflows/SKILL.md`, linked from the browser prompt through `browser-automation`.

## Verification

- Smoke-test browser launch, navigation, DOM capture, and WebUI viewer after runtime changes.
- For viewer render-path changes, verify direct iframe interaction reaches the same page controlled by Patchright, separate contexts use separate displays, and an unavailable Xpra runtime falls back to CDP screencast/snapshot rendering.
- Run browser prompt/skill regression tests after changing browser prompt or Browser plugin skills.

## Child DOX Index

No child DOX files.
