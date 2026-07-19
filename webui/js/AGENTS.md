# WebUI JavaScript DOX

## Purpose

- Own shared frontend JavaScript modules, client-side infrastructure, API helpers, WebSocket clients, stores, extension loaders, and UI utilities.
- Keep frontend contracts stable for core UI and plugin extensions.

## Ownership

- `AlpineStore.js` owns store creation and persistence helpers.
- `api.js` owns CSRF-aware HTTP helpers.
- `websocket.js` owns browser WebSocket client behavior.
- `extensions.js` owns frontend extension loading.
- `components.js` owns `<x-component>` loading, component caching, module injection, nested component processing, and `globalThis.xAttrs`.
- `modals.js` owns the stacked modal shell, `openModal`, `closeModal`, `scrollModal`, footer relocation, backdrop, and modal z-index behavior.
- `surfaces.js` owns shared surface registration, right-canvas/modal mode routing, surface modal action rails, and reusable draggable/focus modal chrome.
- `initFw.js` owns Alpine bootstrap and custom lifecycle directives such as `x-create`, `x-destroy`, and periodic `x-every-*` hooks.
- `messages.js` owns native message/process-step rendering, safe Markdown and HTML conversion, and KaTeX delimiter handling.
- Other modules own focused UI utilities such as modals, messages, safe markdown, shortcuts, TTS/STT, surfaces, and initialization.

## Local Contracts

- Use ES modules and browser-compatible JavaScript.
- Route JSON and fetch calls through `api.js` unless a caller has a specific nonstandard transport contract.
- `callJsonApi()` is for JSON request/response flows and must preserve CSRF/auth behavior.
- `fetchApi()` must continue adding CSRF headers, retrying 403 CSRF refresh paths, and redirecting to `/login` when required.
- `createStore(name, model)` must continue working before and after Alpine boots by proxying to the raw model first and Alpine store later.
- `saveState()` and `loadState()` must not persist functions and should support include/exclude filtering for transient fields.
- `openModal(path)` returns a promise that resolves when that modal DOM node is removed; invalid paths show an in-modal error instead of rejecting.
- Opening the same modal path multiple times must continue creating multiple stack entries; no dedupe is assumed.
- `closeModal()` with no path closes the top modal; `closeModal(path)` closes that path wherever it is in the stack; missing paths are no-ops.
- Modal stack semantics are top-modal-first for Escape, close buttons, z-index, and backdrop placement.
- Restorable modal state is session-scoped and opt-in; surface modals may set `data-modal-restore="surface"` and `modals.js` restores only those path-based surface windows after reload navigation. Browser hard-refresh is still reported to app code as reload, so do not treat this as durable cross-session UI state.
- The modal shell structure is `.modal` > `.modal-inner` > `.modal-header`, `.modal-scroll` containing `.modal-bd`, and `.modal-footer-slot`.
- `data-modal-footer` content is relocated from modal body into `.modal-footer-slot`.
- Click-outside close requires both `mousedown` and `mouseup` on the outer `.modal` container.
- `scrollModal(id)` scrolls inside the top modal's `.modal-scroll`.
- Keep extension loader cache keys and extension point names stable for plugins.
- HTML extension loading turns discovered HTML files into `<x-component>` tags; JavaScript extensions must export a default function.
- Serialize frontend extension-discovery API requests so a page with many extension points cannot exhaust embedded Chromium request resources.
- `<x-component>` loading must process component `style`, `script`, and stylesheet-link assets only once, even when a component keeps its scoped `<style>` inside `<body>`.
- Every `<x-component>` instance must await cached module-load promises before markup is appended so Alpine bindings only run after imported stores exist.
- Every `<x-component>` loading placeholder must be removed after success or failure; a failed asset must never leave a perpetual shimmer.
- Frontend extension hooks such as `confirm_dialog_after_render` and `get_tool_message_handler` must preserve their mutable context contracts.
- Sanitize or safely render user/model-provided HTML and markdown.
- Convert standard TeX delimiters before Markdown parsing without touching inline or fenced code. Keep thought-card math rendering local to the agent-message handler rather than adding math flags to generic process-step or key/value rendering.
- Do not expose secrets in localStorage, console logs, URLs, or WebSocket payloads.
- Full message snapshots that start at backend log `no` 0 must replace the current message DOM before rendering; incremental snapshots should keep patching existing messages.

## Work Guidance

- Prefer small named exports over adding globals.
- Keep frontend API payload assumptions synchronized with backend handlers.
- Use existing modal, notification, cache, device, and surface utilities before adding new infrastructure.
- Check plugin extension callers before changing shared extension behavior.
- Preserve the single shared modal shell and backdrop model; do not add a parallel overlay implementation.
- Preserve modal z-index spacing with a stable base stack and a shared backdrop below the active modal.
- Keep the shared modal stack above the mobile right-canvas rail so blocking modals remain authoritative on small screens.
- If opening a new modal from a close handler, schedule it with `requestAnimationFrame` to avoid stack removal races.
- Keep modal state cleanup explicit because stores can outlive their DOM.
- Device-specific styling may rely on the `device-touch` or `device-mouse` body class set during initialization.

## Verification

- Run targeted frontend/WebUI tests when available.
- For message math changes, smoke-test both response Markdown and agent thought cards with inline and display TeX.
- Manually smoke-test startup, API calls, WebSocket state sync, and affected UI flows after infrastructure changes.
- For modal infrastructure, verify duplicate paths can stack, missing paths stay closable, Escape closes only the top modal, and click-outside requires both mouse down and mouse up on the overlay container.

## Child DOX Index

No child DOX files.
