# Editor Plugin DOX

## Purpose

- Own the native Markdown and plain text editor surface for canvas and floating modal workflows.

## Ownership

- `api/` owns editor session and WebSocket handlers.
- `helpers/` owns editor text session and open-file context helpers.
- `prompts/` owns agent-visible open-file context.
- `webui/` owns editor panel, preview, store, and main surface.
- `extensions/` owns editor hook contributions.

## Local Contracts

- Keep editor session state synchronized across API, WebSocket, and WebUI panel behavior.
- Do not expose unsaved content or local paths beyond intended chat/context surfaces.
- Keep the floating Editor modal on the shared surface modal chrome so the header remains draggable while existing Focus mode continues to work.
- Keep Editor Open wired through the File Browser text picker so users can open one or more Markdown or plain text files with an obvious confirmation action.
- Keep Download in the Editor file-actions menu and save dirty text before downloading it.
- Keep Save As distinct from Rename: Save As writes the current editor text to a chosen `.md` or `.txt` path and retargets the active session without removing the original file.
- Keep Markdown and plain text on the same toolbar, with full-document source and preview modes plus shared Undo/Redo buttons and keyboard shortcuts.
- Preserve source chat context ids when opening Markdown files from tool-result canvas handoffs.

- The tab header owns a persistent file-tree toggle, including the empty Editor state. Reuse the shared Files tree component with Editor-owned state, seeded from the active document directory or Files fallback.
- Opening an already-open document from the tree selects its tab without reloading unsaved text. Unsupported editor formats retain the existing Files surface/editor routing.
- The right-hand tree uses the same content in canvas/modal hosts and overlays the document at narrow panel widths.
- Mount cleanup is host-specific: canvas close passes its panel element so a late canvas close cannot tear down the active modal.

- Use shared `surface-workspace`, toolbar/control, and separator styles from `webui/css/surfaces.css`; match the lighter Files/Browser panel palette and preserve disabled, active, and keyboard focus states.

## Work Guidance

- Coordinate editor preview and session changes with canvas surface registration.

## Verification

- Smoke-test opening, editing, previewing, and reconnecting editor sessions after changes.
- Run `tests/test_file_tree.py` for tree navigation and host cleanup; verify desktop-to-mobile resizing after canvas/modal handoff.

## Child DOX Index

No child DOX files.
