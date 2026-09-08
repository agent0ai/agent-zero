# File Browser Modal DOX

## Purpose

- Own the WebUI file browser workflow for modal and right-canvas Files surface entry points.

## Ownership

- `file-browser.html` owns file list markup, path controls, scoped styles, and modal/canvas footer behavior.
- `settings.html` uses shared settings fields in a two-column desktop/one-column mobile layout for default sort, list/icon view, and tree visibility; it also owns the saved remote connection list/form and per-connection permissions.
- `file-browser-store.js` owns directory loading, remembered-location state, selection, upload/download/delete actions, and surface handoff state.
- `file-tree.js` and `file-tree.html` own the shared lazy directory tree; Files and Editor each retain independent tree state.
- `rename-modal.html` owns rename and create-folder prompts that reuse the file-browser store.

## Local Contracts

- Keep `open(path)` as the modal entry point for workflows that await browser close.
- Keep `openSurface(path)` as the right-canvas entry point; it must load files without opening or awaiting a modal.
- The floating file-browser modal must use the shared surface modal chrome so it remains draggable/resizable and exposes Focus mode.
- Preserve remembered-directory behavior: explicit paths win, then remembered path, then `$WORK_DIR`.
- Empty mounted startup states must self-heal to the `$WORK_DIR` default instead of rendering a blank path and empty list.
- Preserve picker modes for Editor Open and Save As: Editor Open selects one or more text or code files with a pinned primary action, and Save As selects the current folder plus a text-file name (including extensionless names).
- Editor Open omits folder checkboxes while retaining folder navigation. Save As uses a plain filename input filling the footer space before its action buttons.
- Row actions are ordered More actions, Download, then Delete.
- `file-browser-actions-menu` is the HTML extension point after the built-in dropdown entries, mounted only while the menu is open. Plugins contribute `extensions/webui/file-browser-actions-menu/*.html`; an `x-data` root inherits the row `file` (`name`, `path`, `is_dir`, etc.) and `$store.fileBrowser`. Use `.dropdown-item` buttons; ordinary clicks bubble to close the menu.
- Keep Edit inside the overflow menu for editable text/code files, using the same `.dropdown-item` styling as other entries.
- File Browser settings owns the instance-wide maximum editable file size (default 10 MiB, 1–100), since Editor has no plugin config page. Persist through the scoped settings API, update shared limits immediately, and refresh limits when reopening settings; no agent restart or unrelated setting replacement.
- Load file and text limits from the directory API (`?limits=1` for metadata only). Edit eligibility and upload checks use these backend-owned constraints; Editor tree actions reuse this store. The separate transfer setting defaults to 100 MiB and accepts positive integer MiB without a ceiling. It includes local archive uploads and remote transfers; Backup & Restore remains separate. Files POSTs download preparation and follows the returned single-use URL natively, avoiding JavaScript file Blobs. Generic Connector downloads retain their own route. Preserve remote permission checks.
- Keep Extract available for supported archive files; extraction must create a new sibling folder and reject unsafe member paths and links.
- The dropdown tracks its originating `.file-actions` row, so hidden canvas/modal copies cannot open duplicate teleported menus or plugin entries.
- Settings grids use token gaps instead of stacking the shared field margins. Permission controls reuse `.toggle`/`.toggler`. Protocol-specific controls belong in plugin-owned HTML extensions: `file-browser-connection-fields` renders inside the active draft before Save/Cancel; `file-browser-settings` renders independently of the draft. Extensions reuse `.files-connection-actions` and `.files-settings-actions` spacing. SSH key visibility and fingerprint verification are owned by the SSH plugin.
- Settings action groups use the shared small spacing token, wrap whole buttons on narrow screens, and keep table-row actions free of extra vertical margins.
- Managed live connections appear automatically in Remote folders with Open/Test and optional status text. Hide Edit/Remove and omit managed providers from the connection form; CLI/Launcher retain ownership of host paths and scopes.
- The Add connection dropdown floats outside the modal scroll container using shared viewport positioning, without shifting the form; close it on outside click, Escape, resize, and surrounding scroll.
- Add connection stays available with zero installed providers and opens the shared-style thumbnail dropdown. Missing plugins use Install shortcuts that open their actual Plugin Hub Index detail page by key, with a forced Index refresh if a cached entry is missing. Never install directly from Files: users review the plugin page and initiate installation there. Enabled installed plugins show their names without a prefix and open their connection form. Installed-but-disabled entries are disabled with an enablement hint, never offered for reinstallation. Determine installation from `plugins_list`, not enabled provider discovery. Keep plugin management outside this dropdown.
- The footer settings gear is available outside picker modes. Persist validated preferences in `fileBrowser.preferences`; defaults are name/ascending, list view, and a hidden tree. Apply defaults on opening and settings changes, while header sorting and tree toggles remain temporary overrides.
- Remote paths use `/@connections/<provider>/<id>/...` (legacy `/@ssh` is accepted); list via the shared directory API and perform remote actions through `file_browser_connections`. Enabled community providers supply fields and supported permissions to one shared settings UI. Clear connection drafts on modal teardown. Reflect stored permissions in file actions and never route remote paths into local file mutations or Browser/Desktop previews. For SSH, require an explicit username and fingerprint trust and keep private keys/passwords out of responses.
- Icon view reuses list entries and their action/selection/navigation handlers, with token-based grid styling; do not fork file behavior into a second renderer.
- Keep row action menus visible without disabling file-list scrolling; menus may float outside the scroll container but must still close on outside click, Escape, action click, and list scroll.
- The selection toolbar provides Download ZIP, an icon-only Delete action, and a borderless/backgroundless Clear selection close button before the selection count. The toolbar spans the full width below the path header and above the list/tree split. Keep the count and each button label on one line; wrap whole controls with explicit horizontal and vertical gaps on narrow panels.
- Keep the file list readable in narrow canvas/modal containers by hiding the Modified date column before sacrificing the Name or Size columns.
- Use the shared `surface-workspace` lighter palette, 32px flat toolbar controls, and separators between action groups; the file-tree toggle stays available in the path header.
- The list pane uses `padding: 0 6px`, a borderless list container/header bottom, and square file rows. Folder rows use the same `folder` Material Symbol as the tree; file-type SVGs remain for files. All list icons use a fixed 22px slot, with a 22px folder glyph, so folder and file names align. Folder glyphs match the muted gray in `webui/public/file.svg`.
- Keep the list compact: 4px vertical header padding and 5px vertical item padding. The path-submit arrow is borderless and transparent, with opacity-only hover feedback.
- Keep New file and New folder controls icon-only across canvas and modal modes while preserving accessible labels.
- Keep Up, path, New file, New folder, and the rightmost tree toggle in one compact row, with equal button heights. Do not add a separate search or totals row.
- New file uses the existing Save As picker and creates an empty file in the shared Editor; existing names must never be overwritten. HTML/XML/SVG retain Browser preview in their action menu and use the same dropdown Edit entry as other editable files.
- Preserve surface actions that route supported files to Browser, Desktop, or Editor.
- Keep native drag moves available outside picker modes: dragging an unselected row moves only that row without changing selection, dragging a selected row moves the selection, folder rows accept drops, and Up moves items to the parent directory. Moves must reject overwrites and self-nesting.

- File and folder entries in the shared tree must not have native or Bootstrap tooltips.
- Folder names and chevrons both toggle expansion; name clicks navigate only when expanding. Indent branch status messages to the child-name column at each depth.
- Tree branches load through the existing authenticated file-list API on expansion; filtering covers loaded folders. Keep only the filter above the raw tree, without path, parent, or refresh controls. Preserve expanded ancestors during navigation within the root and reset when moving outside it.
- Keep the tree on the right in canvas and modal modes; at narrow panel widths it overlays the content below the toolbar. Tree file clicks reuse picker selection or existing file-opening actions.
- Scope unmount cleanup to the owning panel element; destroying an old host must not clean up the active modal.

- Display a dash for folder sizes; only files show byte sizes. Do not recursively scan folders for list metadata.

## Work Guidance

- Share markup and store behavior between modal and canvas modes; branch only on explicit component `mode`.
- Keep modal footer relocation compatible with `data-modal-footer` while allowing canvas mode to render inline controls.

## Verification

- Smoke-test opening Files as a modal and from the right-canvas rail.
- Run targeted file-browser tests after behavior changes.
- Run `tests/test_file_tree.py` for lazy tree loading, path normalization, filtering, errors, and host cleanup.

## Child DOX Index

No child DOX files.

- All local/remote uploads use multipart `upload_work_dir_files`; shared helpers enforce transfer policy and archive byte/count budgets.
