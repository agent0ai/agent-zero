# Canvas Components DOX

## Purpose

- Own the right-canvas component surface and its state.

## Ownership

- `right-canvas.html` owns the shared tabs, toolbar and retained panels; `canvas-modal.html` supplies their detached host through the standard modal system.
- `right-canvas-store.js` owns canvas state, surface registration, mode transitions and session restoration.
- `right-canvas.css` owns canvas-specific styling.

## Local Contracts

- Keep registered surfaces compatible with WebUI extension hooks.
- Preserve responsive layout and avoid overlapping the chat/sidebar shells.
- External surface actions always open the shared modal. Only right-rail icons explicitly open the sidebar; Desktop on the rail opens detached unless the sidebar is already open. Tabs and navigation within a surface preserve the workspace mode, regardless of per-surface mode history.
- Detach moves the existing shell into one `canvas/canvas-modal.html` entry; attach and close return it before modal removal. Suppress Alpine teardown during moves and use native `moveBefore` to retain iframe contexts. Tab switches reuse mounted panels; explicit navigation payloads still reach their owning surface.
- Detached canvas uses the standard blocking modal backdrop, blur, Escape and outside-click close behavior. One close dismisses the workspace; surface tabs never create or park sibling modals. Nested workflow dialogs retain the ordinary modal stack. Mounted surfaces may veto closure through `canClose`; `whenClosed()` resolves only on workspace dismissal and survives attach/detach. Save As is a separate standard modal without workspace tabs.
- At mobile widths and during Welcome, route non-action opens into that same modal. Keep the rail/sidebar hidden during Welcome; hide Attach when docking is unavailable. Crossing into mobile retains panels and detaches an open sidebar.
- Preserve the active tab, open state and workspace mode across same-tab reloads with session-scoped state, but do not treat open state as durable across sessions.
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
- Run `node --test tests/test_canvas_modes.mjs` for defaults, shared mode, single-modal lifecycle, retained panels, navigation, mobile and reload restoration. Verify actual DOM/iframe continuity, blur, close/Escape/outside click and nested dialogs in a browser.
- Run `node --test tests/test_canvas_rail_drag.mjs` for pointer capture failure, outside release and drag cleanup.
- Run `node --test tests/test_canvas_resize.mjs` for deferred width commits, bounds, pointer isolation and cancellation; verify both directions across an iframe in a real browser.

## Child DOX Index

No child DOX files.
