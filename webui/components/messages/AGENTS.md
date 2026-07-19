# Message Components DOX

## Purpose

- Own message rendering helpers, action buttons, process groups, and resize behavior.

## Ownership

- `action-buttons/` owns simple message action controls.
- `process-group/` owns grouped process-step DOM and styling helpers.
- `resize/` owns message resize state.

## Local Contracts

- Keep message DOM helpers compatible with extension points that modify rendered messages.
- Sanitize or safely render model/user-provided content through shared rendering paths.
- Avoid layout shifts that break long-running message streaming.
- Keep message action chrome out of text selection so copy/paste captures message content without button labels or icons.

## Work Guidance

- Coordinate changes with `webui/js/messages.js` and frontend extension hooks.

## Verification

- Smoke-test message rendering, action buttons, process groups, and resizing after changes.

## Child DOX Index

No child DOX files.
