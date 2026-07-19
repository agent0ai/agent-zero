# WebUI DOX

## Purpose

- Own the Flask-served Alpine.js WebUI shell, frontend modules, components, CSS, static assets, and vendored browser libraries.
- Keep the UI coherent with backend APIs, WebSocket state, plugin extension points, and documented frontend patterns.

## Ownership

- `index.html`, `index.js`, and `index.css` define the main UI shell.
- `components/` owns self-contained Alpine components and component stores.
- `js/` owns shared frontend modules, API clients, WebSocket clients, stores, extension loaders, and utility code.
- `css/` owns shared stylesheet modules.
- `public/` owns first-party static image/icon assets.
- `vendor/` owns vendored third-party browser libraries.

## Local Contracts

- Store-dependent UI must be gated with `x-data` and `x-if="$store.storeName"` before using the store.
- Use `createStore` from `/js/AlpineStore.js` for frontend stores.
- Use `openModal(path)` and `closeModal()` from `/js/modals.js` for modal flows.
- Use `/js/api.js` helpers so CSRF and auth behavior stays consistent.
- Component tags use `<x-component path="...">`; paths are resolved under `webui/components/` when not already prefixed.
- Frontend extension breakpoints use `<x-extension id="...">` and are loaded through `/js/extensions.js`.
- Component HTML loaded by the shared loader may include `<title>`, module scripts, body content, and scoped styles; modal content uses the same loader path.
- Do not bypass WebSocket origin/auth/CSRF assumptions from frontend code.
- Avoid editing vendored files unless intentionally updating the vendor asset.
- Startup scripts in `index.html` must be local and non-parser-blocking: use ES modules, `defer`, or `async` for every script with `src`.
- Rubik (`--font-family-main`) is the default WebUI text and control font; use the code/mono font tokens only for code, logs, paths, and fixed-width data.
- Hover, focus, and active border treatments should follow existing neutral border/background patterns; avoid hard-coded blue border highlights unless matching an established specialized surface.
- Keep transient UI affordances such as Bootstrap tooltips and notification toasts above normal and legacy modal layers while confirmation dialogs remain on top.

## Work Guidance

- Put component-specific markup and styles under `components/`; put reusable frontend infrastructure under `js/`; put shared visual primitives under `css/`.
- Keep UI text and controls consistent with existing components.
- Use notifications for user-facing success, warning, and error feedback where the app already uses notification flows.
- Coordinate API payload changes with backend handlers and tests.

## Verification

- Run targeted WebUI/frontend tests when available.
- Manually smoke-test visible UI changes with `python run_ui.py` when behavior cannot be covered by tests.
- Verify desktop and mobile layout for substantial UI changes.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [components/AGENTS.md](components/AGENTS.md) | Alpine component HTML, component stores, and component-local styles. |
| [css/AGENTS.md](css/AGENTS.md) | Shared WebUI stylesheet modules. |
| [js/AGENTS.md](js/AGENTS.md) | Shared frontend JavaScript modules and client-side infrastructure. |
| [public/AGENTS.md](public/AGENTS.md) | First-party static WebUI images, icons, splash art, and PWA assets. |
| [vendor/AGENTS.md](vendor/AGENTS.md) | Vendored third-party browser libraries. |
