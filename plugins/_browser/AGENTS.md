# Browser Plugin DOX

## Purpose

- Own the built-in Playwright browser tool and WebUI browser viewer.
- Bridge browser automation, page inspection helpers, and browser panel UI.

## Ownership

- `plugin.yaml` and `default_config.yaml` own metadata and browser settings defaults.
- `tools/browser.py` owns the agent-facing browser tool.
- `helpers/` owns Playwright runtime, selectors, URL helpers, extension management, and connector runtime logic.
- `api/` owns status, extension, and browser WebSocket handlers.
- `assets/`, `prompts/`, `skills/`, `extensions/`, and `webui/` own browser scripts, prompts, skill guidance, hook contributions, and UI.

## Local Contracts

- Keep browser actions safe around external pages, credentials, and user data.
- Preserve Playwright lifecycle cleanup and WebSocket viewer compatibility across regular host browsers and Electron WebContentsView embedding.
- Keep the WebUI Browser inside its own modal/canvas affordance; do not replace it with page-level navigation.
- Default the visible WebUI Browser to live CDP screencast for responsiveness. Keep lightweight CDP/DOM state snapshots as the fallback transport.
- Paint live screencast frames through the Browser panel canvas/ImageBitmap path when available; keep the `<img>`/data URL path for snapshots and fallback rendering.
- Push internal screencast frames from the runtime to the WebSocket consumer after subscription; keep `read/pop_screencast_frame` as fallback/tooling APIs, not the WebUI hot path.
- Keep Browser viewer frame transport capability-negotiated: updated clients may request binary/slim screencast frames, while older clients must keep the base64/full-metadata fallback. Do not let the WebUI advertise binary frames unless its Socket.IO client reconstructs attachments as real `Blob`, `ArrayBuffer`, or typed-array values.
- Keep WebUI Browser tabs scoped to the active chat context by default; aggregate tabs from other AgentContext runtimes only when the Browser settings tab scope is `shared`.
- Keep narrow WebUI Browser controls usable by grouping navigation with Annotate/settings above a full-width address bar.
- For Bring Your Own Browser with an existing host profile, `host_browser_selection` may target automatic CLI selection, a browser family/id, an HTTP CDP discovery address, or a full DevTools WebSocket endpoint and must be forwarded to the connector runtime as `browser_selection`.
- Browser Settings must refresh connected A0 CLI host-browser inventory while the settings view is open so newly authorized endpoints appear without saving or reopening.
- Browser Settings keeps the Host browser dropdown focused on automatic selection, advertised debug endpoints, and a validated Custom endpoint field instead of listing every installed local profile. Preserve endpoint path/query case and let A0 CLI resolve discovery addresses on the host.
- Browser URL-intent handling must only claim web URL schemes and leave custom Agent Zero schemes to their owning surfaces.
- Prefer DOM/CDP browser actions with refs, selectors, frame-chain refs, and screenshots over viewport coordinate input. Coordinates remain a visual fallback.
- Do not hardcode user-specific browser paths or secrets.
- Browser model-preset selection resolves omitted preset fields from `_model_config`'s global `Default` preset, not from an unrelated currently scoped model selection.

## Work Guidance

- Coordinate tool, helper, and panel changes so browser state shown in the UI matches tool behavior.
- Do not depend on nested Electron `<webview>` support or launcher-specific preload bridges unless the launcher exposes that bridge as an explicit contract.
- Keep `prompts/agent.system.tool.browser.md` as a compact callable contract; move detailed browser workflows into `skills/browser-automation/SKILL.md`.
- Keep `skills/browser-automation/SKILL.md` frontmatter triggers current with rendered browsing, host-browser, screenshot, and web-interaction user phrasing so relevant-skill recall can surface the skill before the full browser workflow is needed.
- Keep fragile form guidance progressively disclosed through `skills/browser-form-workflows/SKILL.md`, linked from the browser prompt through `browser-automation`.

## Verification

- Smoke-test browser launch, navigation, DOM capture, and WebUI viewer after runtime changes.
- For viewer render-path changes, verify the live Browser panel paints a screencast frame on canvas with `frameSrc` empty and snapshots still falling back to the image path.
- Run browser prompt/skill regression tests after changing browser prompt or Browser plugin skills.

## Child DOX Index

No child DOX files.
