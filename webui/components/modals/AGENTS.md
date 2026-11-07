# Modal Components DOX

## Purpose

- Own WebUI modal component content loaded through the shared modal stack.

## Ownership

- File editing belongs to the `_editor` plugin shared canvas/modal surface; Files routes Edit and New file there.
- Each direct child folder owns one modal workflow and its store.
- Modal HTML files own body content, titles, scoped styles, and `data-modal-footer` content.
- Modal store files own modal-local state and cleanup.
- Task editing modals live in the `_scheduler` plugin (`webui/scheduler/`); this folder does not own scheduler modal content.

## Local Contracts

- Use `openModal(path)` and `closeModal()` from `/js/modals.js`.
- Keep footer content marked with `data-modal-footer` when using pinned modal actions.
- Do not introduce a parallel overlay, backdrop, or teleport modal system.
- `process-step-detail/` keeps its header action buttons at the shared compact `.btn-action-header` size; modal-local styles may align and center them but must not force a taller `min-height`.
- `process-step-detail/` fits the shared modal shell through a `.modal-inner.step-detail-modal`-scoped flex chain reaching `.step-detail-container`, with the pinned header on a fixed shell and `.modal-body` as the modal-local scroller that ends above the shell clip line at any window height; keep every chain level flexed so the panel fills the modal width and height.

## Work Guidance

- Keep modal state cleanup explicit because stores may outlive DOM nodes.
- Preserve stacked modal, Escape, click-outside, scroll, and footer behavior.

## Verification

- Smoke-test open, close, Escape, click-outside, scrolling, stacked modals, and pinned footers after modal changes.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [file-browser/AGENTS.md](file-browser/AGENTS.md) | File browser modal and right-canvas Files surface workflow. |
