# Canvas Components DOX

## Purpose

- Own the right-canvas component surface and its state.

## Ownership

- `right-canvas.html` owns canvas markup.
- `right-canvas-store.js` owns canvas state, surface registration, and actions.
- `right-canvas.css` owns canvas-specific styling.

## Local Contracts

- Keep registered surfaces compatible with WebUI extension hooks.
- Preserve responsive layout and avoid overlapping the chat/sidebar shells.
- Right-canvas rail and tab buttons are explicit canvas entry points above the mobile breakpoint; at mobile widths, keep the rail visible but route non-action surfaces into floating modals instead of the side canvas shell.
- Keep the right-canvas rail and docked shell hidden while the welcome screen is active; non-action surface opens during welcome must route into floating/modal surfaces instead of docking beside the welcome screen.
- Preserve docked canvas open state across same-tab reloads with session-scoped state, but do not treat it as durable cross-session UI state.
- In mobile mode, keep the rail below blocking modal layers and compact it on very narrow screens instead of letting it cover modal content.
- Keep the canvas shell functional when the instance-level visibility preference hides only the right-canvas rail.

## Work Guidance

- Use existing surface and extension helpers before adding new canvas infrastructure.

## Verification

- Smoke-test right-canvas open, close, resize, and registered surfaces after changes.

## Child DOX Index

No child DOX files.
