# WebUI Extensions DOX

## Purpose

- Own built-in frontend extension contributions under `extensions/webui/`.
- Keep WebUI extension points compatible with the core loader and plugin extension model.

## Ownership

- Each direct subdirectory is one frontend extension point.
- `.html` files are injected as component references through `<x-extension>`.
- `.js` and `.mjs` files export default functions called by `callJsExtensions`.

## Local Contracts

- HTML contributions must be valid component fragments and include Alpine state only where needed.
- JavaScript extension modules must export a default function.
- Extension code must not assume a plugin is installed unless it guards that dependency.
- Keep extension point names synchronized with `x-extension` IDs and `callJsExtensions()` callers.

## Work Guidance

- Prefer small extension modules that delegate to existing WebUI stores or helpers.
- Use the notification store for user-facing success, warning, or error feedback.
- Avoid global DOM queries when an extension hook provides scoped nodes or context.

## Verification

- Manually load the WebUI or run targeted frontend/WebUI tests after changing visible extension behavior.
- Verify extension cache clearing paths when adding new extension points.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [fetch_api_call_after/AGENTS.md](fetch_api_call_after/AGENTS.md) | Frontend hooks after raw `fetchApi()` calls. |
| [fetch_api_call_before/AGENTS.md](fetch_api_call_before/AGENTS.md) | Frontend hooks before raw `fetchApi()` calls. |
| [get_message_handler/AGENTS.md](get_message_handler/AGENTS.md) | Message rendering handler extensions. |
| [initFw_end/AGENTS.md](initFw_end/AGENTS.md) | Post-WebUI-framework-initialization extensions. |
| [json_api_call_after/AGENTS.md](json_api_call_after/AGENTS.md) | Frontend hooks after `callJsonApi()` calls. |
| [json_api_call_before/AGENTS.md](json_api_call_before/AGENTS.md) | Frontend hooks before `callJsonApi()` calls. |
| [right-canvas-panels/AGENTS.md](right-canvas-panels/AGENTS.md) | Built-in right-canvas panel HTML contributions. |
| [right_canvas_register_surfaces/AGENTS.md](right_canvas_register_surfaces/AGENTS.md) | Built-in right-canvas surface registrations. |
| [set_messages_after_loop/AGENTS.md](set_messages_after_loop/AGENTS.md) | Frontend hooks after message DOM updates. |
| [set_messages_before_loop/AGENTS.md](set_messages_before_loop/AGENTS.md) | Frontend hooks before message DOM updates. |
| [webui_ws_push/AGENTS.md](webui_ws_push/AGENTS.md) | WebUI WebSocket push-event behavior. |
