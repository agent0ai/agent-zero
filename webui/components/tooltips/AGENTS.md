# Tooltip Components DOX

## Purpose

- Own shared tooltip state and behavior for WebUI controls.

## Ownership

- `tooltip-store.js` owns tooltip state, positioning, and actions.

## Local Contracts

- Keep tooltip positioning compatible with desktop and mobile layouts.
- Do not make tooltips required for completing a workflow.
- Cancel Bootstrap tooltip opening when the device reports no hover support; touch-generated hover events must not open a tooltip or interfere with the control's click action. Keep title normalization active to avoid native tooltip fallbacks.
- Finish pending tooltip fade callbacks before disposing detached controls, including rows moved between sidebar sections.
- Tooltip content wraps, including long unbroken strings such as file paths (`overflow-wrap: anywhere` on `.tooltip` in `webui/index.css`, inherited by `.tooltip-inner`); keep that rule when restyling.

## Work Guidance

- Prefer concise tooltip text and stable positioning around icon-only controls.

## Verification

- Smoke-test hover/focus tooltip behavior after changes.

## Child DOX Index

No child DOX files.
