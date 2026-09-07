# File Browser Modal DOX

## Purpose

- Own the WebUI file browser workflow for modal and right-canvas Files surface entry points.

## Ownership

- `file-browser.html` owns file list markup, path controls, scoped styles, and modal/canvas footer behavior.
- `file-browser-store.js` owns directory loading, remembered-location state, selection, upload/download/delete actions, and surface handoff state.
- `file-tree.js` and `file-tree.html` own the shared lazy directory tree; Files and Editor each retain independent tree state.
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
- Use the shared `surface-workspace` lighter palette, 32px flat toolbar controls, and separators between action groups; the file-tree toggle stays available in the path header.
- The list pane uses `padding: 0 6px`, a borderless list container/header bottom, and square file rows. Folder rows use the same `folder` Material Symbol as the tree; file-type SVGs remain for files. All list icons use a fixed 22px slot, with a 22px folder glyph, so folder and file names align.
- Keep the list compact: 4px vertical header padding and 5px vertical item padding. The path-submit arrow is borderless and transparent, with opacity-only hover feedback.
- Keep New file and New folder controls icon-only across canvas and modal modes while preserving accessible labels.
- Keep Up, path, New file, New folder, and the rightmost tree toggle in one compact row, with equal button heights. Do not add a separate search or totals row.
- Preserve surface actions that route supported files to Browser, Desktop, or Editor.
- Keep native drag moves available outside picker modes: dragging an unselected row moves only that row without changing selection, dragging a selected row moves the selection, folder rows accept drops, and Up moves items to the parent directory. Moves must reject overwrites and self-nesting.

- Tree branches load through the existing authenticated file-list API on expansion; filtering covers loaded folders. Keep only the filter above the raw tree, without path, parent, or refresh controls. Preserve expanded ancestors during navigation within the root and reset when moving outside it.
- Keep the tree on the right in canvas and modal modes; at narrow panel widths it overlays the content below the toolbar. Tree file clicks reuse picker selection or existing file-opening actions.
- Scope unmount cleanup to the owning panel element; destroying an old host must not clean up the active modal.

## Work Guidance

- Share markup and store behavior between modal and canvas modes; branch only on explicit component `mode`.
- Keep modal footer relocation compatible with `data-modal-footer` while allowing canvas mode to render inline controls.

## Verification

- Smoke-test opening Files as a modal and from the right-canvas rail.
- Run targeted file-browser tests after behavior changes.
- Run `tests/test_file_tree.py` for lazy tree loading, path normalization, filtering, errors, and host cleanup.

## Child DOX Index

No child DOX files.
