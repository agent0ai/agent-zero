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
