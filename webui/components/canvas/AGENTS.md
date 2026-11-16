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
- Width drags move a highlighted separator over a temporary viewport input shield; keep surface sizes unchanged until release, then commit/persist once without a width transition. Capture the initiating pointer and track it at window capture phase so iframe surfaces cannot steal either drag direction. Cancellation, lost capture, Escape, blur, viewport resize, close and unmount remove the preview/listeners without committing.

- Rail icons open their respective surfaces directly; keep the rail free of a separate Show/Hide toggle and keep the grip free of a tooltip.
- The rail grip moves vertically with pointer capture or arrow/Home/End keys; its local position persists with canvas state and is clamped to the available height. Track the active pointer at window capture phase so movement and release outside the grip still work if pointer capture fails. End on release, cancellation, lost capture, blur, released-button movement or unmount; disconnect its size observer and drag listeners on unmount.
- Register each surface as `canvas:<surface-id>` in shared Interface visibility. Filter rail icons and tabs by device; hidden panels requested elsewhere open as windows. Customize opens Settings at Interface.

## Work Guidance

- Use existing surface and extension helpers before adding new canvas infrastructure.

## Verification

- Smoke-test right-canvas open, close, resize, and registered surfaces after changes.
- Run `node --test tests/test_canvas_rail_drag.mjs` for pointer capture failure, outside release and drag cleanup.
- Run `node --test tests/test_canvas_resize.mjs` for deferred width commits, bounds, pointer isolation and cancellation; verify both directions across an iframe in a real browser.

## Child DOX Index

No child DOX files.
