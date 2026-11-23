# Browser Plugin DOX

## Purpose

- Own the built-in Chromium CDP browser tool and WebUI browser viewer.
- Bridge browser automation, page inspection helpers, and browser panel UI.

## Ownership

- `plugin.yaml` and `default_config.yaml` own metadata and browser settings defaults.
- `tools/browser.py` owns the agent-facing browser tool.
- The tool logs its message with an `icon://captive_portal` gerund headline naming the action and target URL, such as `Browser: Opening <url>`; `extensions/webui/get_tool_message_handler/` owns the `WWW` badge presentation.
- `helpers/` owns the guest runtime client, private interactive display, selectors, URL helpers, extension management, and connector runtime logic.
- `api/` owns status, extension, and browser WebSocket handlers.
- `assets/`, `prompts/`, `skills/`, `extensions/`, and `webui/` own browser scripts, prompts, skill guidance, hook contributions, and UI.

## Local Contracts

- Both canvas registration hooks share the implementation in `right_canvas_register_surfaces/`.

- With the Tuxee base, mount only the upstream display binaries and private audio runtime read-only. Trixie guests use these with their own Debian runtime packages and XKB data. Bookworm guests use the portable build fallback and keep their pinned image and profile.

- Route plain web research to the `web-search` skill; search has no dedicated agent tool.
- The internal browser stages uploads from the named file destination. On a connected host, uploads require Files read access to the shared folder and explicit host screenshot paths require write access. A plain screenshot uses Browser access. A named file destination determines the capture format independently of its write path. Closing a host tab returns only its acknowledgement.
- DOM-helper messaging accepts only non-opaque same-origin documents, uses exact target origins, and binds responses to the requested child window and operation. Use the effective Window origin so inherited-origin `about:blank` and `srcdoc` frames work; cross-origin frame RPC fails closed while direct automation entry points remain available.
- Captured references keep their frame chain. Resolve top-level form and pointer targets by node identity in the isolated world.
- DOM helper v2 and internal runtime readiness checks reject in-place upgrades: reload existing pages to remove legacy anonymous message listeners. Host connectors receive the helper source through its existing SHA-256 update path; restart existing host browsers and reconnect before reloading restored tabs to discard old initialization scripts.
- Preserve Chromium process and session cleanup and WebSocket viewer compatibility across regular host browsers and Electron WebContentsView embedding.
- Failed or cancelled internal startup closes both Chromium and its sandbox display before retry. Shutdown gives Chromium a bounded grace period after termination, then kills and reaps an unresponsive owned process before releasing its profile.
- Keep the WebUI Browser inside its own modal/canvas affordance; do not replace it with page-level navigation. Initialize a canvas Browser panel only when the canvas marks Browser active and visible, even if an inactive panel briefly has layout during mount.
- Default the visible WebUI Browser to the authenticated noVNC viewer for its existing Chromium window. Keep live CDP screencast and lightweight snapshots as automatic fallbacks.
- Do not block an available interactive viewer on a redundant Chromium screenshot; capture initial snapshots only for fallback transports.
- Display the entire native Chromium window at the private display bounds. Chromium owns tabs, address, navigation and settings. Each header window button shows its selected tab’s title and the window’s tab count. The A0 header retains New window, Annotate, volume and plugin settings.
- Store the Chromium profile under `usr/plugins/_browser/profile` so user-data mounts and backups retain browser logins. On first use, adopt the old `tmp/browser/sessions/shared` profile, falling back to the requesting legacy chat profile. Preserve an existing destination; stage a complete symlink-preserving copy before publishing across filesystems and removing the source contents. Keep an empty legacy shared mount directory during startup so existing worker metadata remains valid until its mounts are replaced.
- Chromium restores its native session from the shared profile. Import a legacy KVP URL list once on upgrade. Seed DuckDuckGo as homepage only if the profile has no homepage preference.

- Let the native Chromium viewport follow actual surface dimensions with throttled resize updates. Canvas divider drags preview without changing those dimensions until release; floating-window resizes continue updating live.
- Reuse the private display's native dimensions when interactive-viewer requests omit a size. Page CSS viewport dimensions change with zoom and must not resize the display during navigation or tab switching.
- Keep exactly one interactive viewer iframe connected during canvas/modal handoff so hidden surfaces cannot compete to resize the same display.
- Complete tab switching when the viewer subscription succeeds and reuses the interactive viewer URL; the shared iframe does not reload for each tab. New viewer URLs and fallback frames retain their load/render completion path.
- Agent Zero owns display resizing and Chromium window fitting. noVNC scales the framebuffer but must not independently resize the server; preserve one iframe through canvas/modal handoff.
- Keep one browser guest per Agent Zero process. The framework sends operations over its cancellable RPC pipe. Inside the guest, `sandbox/cdp.py` owns Chromium and its private DevTools pipe, targets and sessions. `sandbox/runtime.py` owns shared browser actions and the viewer. Keep the DevTools connection off the network.
- The guest image's Python runs RPC and audio directly. Chromium launches through the guest's stable `/opt/runtime/bin/a0-chromium` entry point. Keep the browser installation independent of the Python runtime.
- Agent `cdp` calls send opaque Chromium methods and parameters through a dedicated browser-target session per chat on the same pipe. Route tab and nested target sessions and their bounded, drainable events to that client. Keep framework sessions independent. Reset/removal detaches only that client's session tree. On Host Chromium the existing Browser grant covers the same contract.
- Browser startup has six reported stages: sandbox, dependencies, Chromium installation, display, Chromium launch, and tabs/viewer. Cached installation stages may be skipped. Guest RPC reports real display/Chromium/tab transitions; worker readiness alone never means Chromium is running. Session checks must say they are checking, not starting Chromium. Show a first-run dependency-installation subtitle instead of an elapsed timer; connection-recovery notices take precedence. Internal tool calls expose the same explanation as a Browser setup KVP while startup is active, without changing agent-facing results or starting a guest just to check status.
- Repeated private-display sizes are no-ops: A0 owns display geometry. Update cached dimensions and GTK chooser settings only after a successful resize; failed resizes must remain retryable.
- Synchronous context cleanup shares the named BrowserCleanup event loop. Cancel only the cleanup task on completion/timeout; an individual context must not terminate the shared thread used by concurrent resets.
- Bind VNC to IPv4 loopback with fresh VncAuth credentials and a private Xauthority cookie. `helpers/viewer_gateway.py` serves only owned sessions at `/browser/vnc/`, with A0 authentication, same-origin checks, bounded binary input and private no-store credentials. No extra HTTP daemon or published port.
- `webui/clipboard.js` bridges focused host text paste events and guest clipboard updates over the authenticated noVNC session. Translate Apple Command copy/cut/paste to the guest and initiate host writes during the gesture.
- Browser audio uses Tuxee's stripped PulseAudio bundle read-only in the guest, with a private cookie/socket and a null sink for the shared Chromium runtime. `sandbox/audio.py` owns sink lifetime and capture; closing a capture's control pipe stops its process even during silence. The existing viewer gateway authenticates `/audio` before executing capture. PCM is 48 kHz stereo s16le in 960-frame packets with a little-endian 64-bit sample position; silent packets are omitted. `webui/audio.js` owns bounded Web Audio playback, gain and gesture unlocking. The Browser header places the volume slider before settings and reapplies its level to each interactive viewer. Zero or disconnect stops capture, and unmuting restores the last nonzero level. Audio mixes all tabs in the shared browser, independently of the visible tab. Keep build dependencies in disposable builders or the source-install guest, with no hardware sound device or public audio port.
- Paint live screencast frames through the Browser panel canvas/ImageBitmap path when available; keep the `<img>`/data URL path for snapshots and fallback rendering.
- Push internal screencast frames from the runtime to the WebSocket consumer after subscription; keep `read/pop_screencast_frame` as fallback/tooling APIs, not the WebUI hot path.
- Keep Browser viewer frame transport capability-negotiated: updated clients may request binary/slim screencast frames, while older clients must keep the base64/full-metadata fallback. Do not let the WebUI advertise binary frames unless its Socket.IO client reconstructs attachments as real `Blob`, `ArrayBuffer`, or typed-array values.
- All chats share the internal Chromium workspace. The tool’s `list` groups live tabs by Chromium window ID, including tabs opened directly in the viewer. `open` and `set_active` accept window IDs. Resolve tab IDs again after restart.
- Chat context handles attribute screenshots and annotations to the requester. Chat resets and removals release the handle and preserve all windows.

- Empty viewer subscriptions and closing the last tab clear page and viewer state. Context changes invalidate late commands and subscriptions while retaining the shared browser.
- Show an accessible in-panel startup state while the on-demand shared Browser runtime is cold-starting; keep that one runtime warm until Browser configuration changes or Agent Zero shuts down.
- Poll authenticated `browser_startup_status` with the current context; HTTP status exposes the same `startup` snapshot. Reads never start a guest or wait for the setup lock. Include `state`, `stage`, `message`, `step`, `steps`, and context-scoped `pending` for open/subscription requests, including the viewer handoff. Never expose raw logs. Invalidate late polls and recovery on context changes/cleanup.
- Keep the first-launch/subscription busy state through completion, including nested requests and transport timeouts. A lost acknowledgement is an unknown outcome: poll until the original server request finishes, then attach without repeating `open`. Confirmed errors allow retry; a lost status connection stays in reconnecting state. Reject duplicate first-launch clicks. The startup deadline covers both installation and browser launch even with cached dependencies; ordinary warm commands retain shorter deadlines. The iframe reports the final connection stage until VNC is connected.
- Listing must not cold-start Chromium when there is no session to restore.
- Navigation waits only for the requested readiness: agent tools default to `domcontentloaded`, while WebUI navigation/new tabs and restored tabs use `commit`. Do not follow navigation with another load wait or fixed settle delay; retain settling for interaction actions. Read title, back-navigation availability, and loading state in one page evaluation. Back and Forward use Chromium’s tab history. Follow the traversing frame across renderer changes until it reaches the requested readiness or the page removes it. If navigation interrupts a reference click or submit result, return the new tab state and a warning only after confirming a replacement document. Dispatch the action once.
- Let header window buttons scroll horizontally on narrow surfaces. Keep the icon actions outside the scroll strip at their full size, with an accessible name and pressed state for Annotate. Show its tooltip on hover and focus, and dismiss it when the button is activated.
- For Bring Your Own Browser with an existing host profile, `host_browser_selection` may target automatic host selection, a browser family/id, an HTTP CDP discovery address, or a full DevTools WebSocket endpoint and must be forwarded to the connector runtime as `browser_selection`.
- Browser Settings must refresh connected host-browser inventory while the settings view is open so newly authorized endpoints appear without saving or reopening.
- Browser Settings keeps the Host browser dropdown focused on automatic selection, stable IDs for advertised debug endpoints, and advertised Safari WebDriver targets instead of listing every installed local profile. Describe host access as available through Launcher or A0 CLI without presenting the CLI as the only runtime. Present host-browser setup without an outer container treatment: Chromium-family guidance comes first on the left and Safari/macOS second on the right, with narrow layouts stacking naturally and manual endpoint fallback progressively disclosed. Chrome, Opera, and Edge setup buttons appear only when a compatible connected host advertises that installed browser, then use the authenticated connector bridge to open its fixed internal inspect page; mention Brave, Vivaldi, and Chromium without adding more primary buttons. Safari guidance must name Safari Settings > Advanced > Show features for web developers and Developer > Allow remote automation, and explain its dedicated automation window. Use the advertised ID for a discovered browser and the exact address for a custom endpoint. Preserve endpoint path/query case and let the connected host resolve discovery addresses.
- Browser URL-intent handling must only claim web URL schemes and leave custom Agent Zero schemes to their owning surfaces.
- Prefer DOM/CDP browser actions with refs, selectors, frame-chain refs, and screenshots over viewport coordinate input. Coordinates remain a visual fallback.
- Do not hardcode user-specific browser paths or secrets.
- Host Browser access is granted by the connected host. Its page content and screenshots are available to the selected model.
- Browser model-preset selection resolves omitted preset fields from `_model_config`'s global `Default` preset, not from an unrelated currently scoped model selection. After the first Browser tool call, use the selected preset for subsequent model turns in that monologue and clear it at monologue end.
- Read tab listings and page content on explicit Browser requests. Ordinary model turns must not query the browser or inject its state.
- Browser tool results serialize minified JSON for agent history; any JSON beautification for display stays plugin-local in the WebUI tool handler (`browser-tool-handler.js`), never in shared `helpers/tool.py` where it would apply to every tool.
- History screenshot capture skips `list`, `state`, `content`, `detail`, `evaluate`, `cdp`, closing actions, and batches containing only those actions. Preserve history previews for other actions and reuse explicit screenshot results without capturing again.
- `evaluate` requires a non-empty `script` string in single and multi calls. Reject missing input instead of evaluating `undefined`; preserve legitimate JavaScript null/undefined results. CDP evaluation preserves BigInt values as exact integers in returned arrays and objects.
- `evaluate_timeout_seconds` is a Browser setting (default 30, finite range 0.1–60 seconds, invalid values rejected), resolved for the requesting chat/project; never accept a model-facing timeout override. It bounds user evaluation and result-state collection. Serialize evaluates per page and interrupt with CDP `Runtime.terminateExecution`. Preserve the document when the original request settles within a 250 ms response grace; reload to commit only for unresolved execution (such as awaited promises). Report any reload or fallback closure in the timeout error. Recovery, fallback page closure, and protocol detachment each have a 5-second bound; report recovery failure rather than success. Never reset the shared browser for an evaluate timeout. Caller cancellation must reach the Browser worker and await its cleanup without stopping the shared thread.
- Core supplies the settings deadline, dispatches multi calls through the same per-browser grouping as Internal Browser, and waits for `cancel_evaluate` acknowledgement on caller/transport cancellation. The companion connector owns browser-side interruption/recovery and rejects Safari evaluate. A lost acknowledgement is an unconfirmed cancellation error, never proof that JavaScript stopped.
- Clipboard `clipboard_action` reads legacy aliases `operation` and `event_type`; `a0_path` and `context_id` are screenshot result fields, not tool args. Document only canonical args in model-facing prompts.
- Browser action values accept legacy spellings `setactive`/`activate`/`focus` for `set_active`, `typesubmit` for `type_submit`, and `keychord` for `key_chord`; prompts document only canonical action values.
- Annotation mode highlights the DOM element under the pointer, keeps saved overlays page-local, and may batch annotated pages only within the active chat context.
- Quick settings contains model preset, scoped Host / Container agent tool routing, and plugin settings. The embedded viewer displays the shared Container browser used by all Browser actions, including `cdp`.
- Plugin settings own unpacked extension creation, installation and agent review. Native browser preferences live in Chromium.
- Annotation screenshots default off. Capture only explicit annotation selections when the saved scoped preference allows it, never pointer hover; attach images through the chat attachment store only for the current chat, for both typed and voice workflows.
- Native zoom sends only allowlisted shortcuts to Chromium's private display; report the actual device-pixel ratio as the zoom percentage. Chromium retains its native zoom limits and per-site settings.
- Container downloads honor Chromium's native folder and save-dialog preferences. Seed the existing Browser download directory only when no folder is configured, preserve other profile preferences and let Chromium handle the download.
- Annotation voice input reuses Whisper STT's configured draft/send delivery mode and shared microphone state.
- Proxy settings apply to the internal runtime. Restart it on changes. Enable browser-wide CDP authentication before target discovery, including native session restore. Provide credentials only for challenges from the configured proxy.
- Launch full Chromium headful on the private display with the Chrome for Testing infobar hidden. Chromium supplies its own identity, headers and native window focus.
- Use Chromium's AutomationControlled launch setting to preserve the pre-CDP value of `navigator.webdriver` without page-script overrides.
- Browser keyboard layout settings (`keyboard_layout`/`keyboard_variant`, e.g. `de`/`mac`) apply the configured XKB layout to the private browser display with setxkbmap so non-US keyboards type their printed characters; layout changes flow through `browser_runtime_config` and restart internal runtimes. Fallback canvas input forwards AltGraph and macOS Option text without converting ordinary Alt shortcuts into text.
- Install the managed command-line warning policy for Chrome for Testing and Debian Chromium inside the Browser guest. Verify its effective value at `chrome://policy` and check browser chrome through Xvnc after a worker upgrade.
- `sandbox/install.sh` reuses the stable entry point. For earlier v3 guests it adopts a single completed full build in the guest cache before looking on `PATH`; multiple cached builds require an explicit selection. An empty guest provisions Debian’s full `chromium` package. The package manager selects the architecture. Setup must resume on the same guest after an interrupted APT refresh.
- The same installer provides international fonts, GTK dialogs, XKB data and the private Tuxee viewer and audio tools. Use the v3 image’s read-only tools when available. Source installs can build the portable bundles inside the guest. Framework startup only registers viewer routes.
- Browser startup must install the shared virtual-desktop route hook itself; do not make Browser depend on the Desktop plugin being enabled.
- Use shared `surface-workspace`, toolbar/control, and separator styles from `webui/css/surfaces.css`; match the lighter Files/Browser panel palette and preserve disabled, active, and keyboard focus states.
- Expose only the persistent browser profile, browser downloads and explicitly enabled extension directories to the guest. Uploads cross as selected file bytes; screenshots return through CDP. Never signal host PIDs from guest Chromium singleton files.

- Create missing profile and download bindings with the Browser worker group. Publish a complete legacy profile before removing its source.

## Work Guidance

- Container uses CDP by default. Container and Host Chromium share the same Browser action vocabulary. Keep the nine actions in `helpers/config.py:model_actions` in sync with the Browser skill. Both model transports use this projection. The viewer and Agent Editor use canonical action IDs. Put WebDriver workflows and guidance for when direct `cdp` calls are disabled in the skill’s browser controls reference.
- Keep response-body diagnostics in the Browser skill. Durable response storage is an explicit Chromium CDP option on the capturing session.

- Coordinate tool, helper, and panel changes so browser state shown in the UI matches tool behavior.
- Do not depend on nested Electron `<webview>` support or launcher-specific preload bridges unless the launcher exposes that bridge as an explicit contract.
- Keep `prompts/agent.system.tool.browser.md` as a compact callable contract; move detailed browser workflows and host setup/remote-tool fallback guidance into `skills/browser-automation/SKILL.md` so the default system prompt does not name unavailable remote tools.
- Keep `skills/browser-automation/SKILL.md` frontmatter triggers current with rendered browsing, host-browser, screenshot, and web-interaction user phrasing so relevant-skill recall can surface the skill before the full browser workflow is needed.
- Keep fragile form guidance progressively disclosed through `skills/browser-form-workflows/SKILL.md`, linked from the browser prompt through `browser-automation`.

## Verification

- Smoke-test browser launch, navigation, DOM capture, and WebUI viewer after runtime changes.
- Run `python -m unittest discover -s tests -p test_browser_audio.py`, `node --test tests/test_browser_audio.mjs`, and the audio gateway cases in `tests/test_browser_vnc.py`; native audio changes also require a real Chromium-to-PCM capture check.
- Run `pytest tests/test_browser_dom_security.py` for real-Chromium origin isolation, parent/frame/opener attacks, response binding, same-origin frame actions, and legacy-helper upgrades. Run `pytest tests/test_browser_agent_regressions.py tests/test_host_browser_connector.py` for internal runtime and distributed helper compatibility.
- For viewer changes, verify native tabs opened by a user appear under the correct window in another chat’s agent tool, annotations target page content, and screencast/snapshot fallback still works.
- Run browser prompt/skill regression tests after changing browser prompt or Browser plugin skills.

## Child DOX Index

- [webui/vendor/novnc/AGENTS.md](webui/vendor/novnc/AGENTS.md): pinned noVNC sources, local fixes and licenses.
