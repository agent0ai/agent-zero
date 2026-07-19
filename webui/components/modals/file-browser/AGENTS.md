# File Browser Modal DOX

## Purpose

- Own the WebUI file browser workflow for modal and right-canvas Files surface entry points.

## Ownership

- `file-browser.html` owns file list markup, path/search controls, scoped styles, and modal/canvas footer behavior.
- `file-browser-store.js` owns directory loading, remembered-location state, selection, upload/download/delete actions, and surface handoff state.
- `rename-modal.html` owns rename and create-folder prompts that reuse the file-browser store.

## Local Contracts

- Keep `open(path)` as the modal entry point for workflows that await browser close.
- Keep `openSurface(path)` as the right-canvas entry point; it must load files without opening or awaiting a modal.
- The floating file-browser modal must use the shared surface modal chrome so it remains draggable/resizable and exposes Focus mode.
- Preserve remembered-directory behavior: explicit paths win, then remembered path, then `$WORK_DIR`.
- Empty mounted startup states must self-heal to the `$WORK_DIR` default instead of rendering a blank path and empty list.
- Preserve picker modes for Editor Open and Save As: Editor Open selects one or more Markdown or plain text files with a pinned primary action, and Save As selects the current folder plus a `.md` or `.txt` file name.
- Keep the row-level Open in Editor action visible outside the overflow menu for Editor-owned `.md` and `.txt` files.
- Keep Extract available for supported archive files; extraction must create a new sibling folder and reject unsafe member paths and links.
- Keep row action menus visible without disabling file-list scrolling; menus may float outside the scroll container but must still close on outside click, Escape, action click, and list scroll.
- Keep the file list readable in narrow canvas/modal containers by hiding the Modified date column before sacrificing the Name or Size columns.
- Keep New file and New folder controls icon-only across canvas and modal modes while preserving accessible labels.
- Keep narrow mobile controls compact: Up shares the path row, and New file/New folder share the search row.
- Preserve surface actions that route supported files to Browser, Desktop, or Editor.

## Work Guidance

- Share markup and store behavior between modal and canvas modes; branch only on explicit component `mode`.
- Keep modal footer relocation compatible with `data-modal-footer` while allowing canvas mode to render inline controls.

## Verification

- Smoke-test opening Files as a modal and from the right-canvas rail.
- Run targeted file-browser tests after behavior changes.

## Child DOX Index

No child DOX files.
