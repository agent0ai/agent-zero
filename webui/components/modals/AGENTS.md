# Modal Components DOX

## Purpose

- Own WebUI modal component content loaded through the shared modal stack.

## Ownership

- File editing belongs to the `_editor` plugin shared canvas/modal surface; Files routes Edit and New file there.
- Each direct child folder owns one modal workflow and its store.
- Modal HTML files own body content, titles, scoped styles, and `data-modal-footer` content.
- Modal store files own modal-local state and cleanup.
- `scheduler/` owns task editing: both prompt fields use full-width resizable textareas, with a shared expanded prompt modal bound to the same draft. Closing the expanded view retains draft edits; only a successful task save clears the draft. API error bodies must be treated as failures even with HTTP 200.
- Scheduler actions live in the pinned footer. New tasks offer idle/disabled initial states and inherit only the active chat's project, otherwise defaulting to no project.

## Local Contracts

- Use `openModal(path)` and `closeModal()` from `/js/modals.js`.
- Keep footer content marked with `data-modal-footer` when using pinned modal actions.
- Do not introduce a parallel overlay, backdrop, or teleport modal system.

## Work Guidance

- Keep modal state cleanup explicit because stores may outlive DOM nodes.
- Preserve stacked modal, Escape, click-outside, scroll, and footer behavior.

## Verification

- Smoke-test open, close, Escape, click-outside, scrolling, stacked modals, and pinned footers after modal changes.
- For scheduler editing, run `pytest tests/test_scheduler_editor.py` and check prompt expansion, draft retention, and save/reopen on desktop and mobile.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [file-browser/AGENTS.md](file-browser/AGENTS.md) | File browser modal and right-canvas Files surface workflow. |
