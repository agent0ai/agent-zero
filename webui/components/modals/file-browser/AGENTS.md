# File Browser Modal DOX

## Purpose

- Own the shared WebUI file browser for modal, right-canvas and embedded welcome entry points.

## Ownership

- `file-browser.html` owns file list markup, path controls, scoped styles, and modal/canvas footer behavior.
- `../../settings/file-browser/file-browser-settings.html` owns the shared Settings fields for default sort, list/icon view, tree visibility and starting folder, plus the saved remote connection list/form and per-connection permissions.
- `file-browser-store.js` owns the reusable view factory, shared configuration, directory loading, remembered locations, selection, file actions and surface handoff. Its `fileBrowser` facade preserves existing callers while selecting the active chat view.
- `file-gestures.js` owns internal pointer dragging, marquee and checkbox sweep selection, touch hold and device drops. Releasing a touch hold keeps focus in the open menu. Mount it once per host, resolve the current view on each gesture and tear it down with the host.
- `file-preview.js` opens supported images, video and audio through the bounded Files download route. Preview follows visible sort order, aborts on close or navigation, and revokes object URLs on disposal. Dialog close events can arrive after reopening; only clear a dialog while it is closed. Browser and Editor remain available through their existing actions.
- `file-tree.js` and `file-tree.html` own the shared lazy directory tree; Files and Editor each retain independent tree state.
- `save-as-modal.html` owns the dedicated Save As dialog, reusing the Files component with an independent `fileBrowserSaveAs` view, standard backdrop and pinned footer, without canvas tabs.
- `rename-modal.html` owns the rename and create-folder prompt for external callers (Editor, Desktop) that have no live browser footer; inside the browser both flows use the shared footer input.

## Local Contracts

- `createFileBrowserView(name, { embedded, rememberKey })` returns one stable view per name. The existing `fileBrowser` store forwards actions to its `current` view with methods bound before asynchronous work. Chat views are independent by default; `preferences.independent = false` selects the shared primary view. Current directories, entries/selection, history, requests, menus, inline actions and trees are view-local. Uploads capture their destination before awaiting limits and update only a matching current folder. Appearance/defaults, limits and remote connection settings remain shared.
- The browser-local **Separate browsing per chat** setting switches between retained chat views and one shared session. Remembered chat paths use `fileBrowser.lastDirectory.<context>`; the existing shared key remains compatible. The server's remember-location setting controls all views. Welcome uses its own remembered key and stays independent in either chat mode.
- `file-browser.html` accepts an `owner` store name and `mode="embedded"` for plugin cards. Its local `fb` binding tracks the current primary view or the explicit embedded owner, and the relocated footer owns its own binding. Embedded markup uses the real path/list/tree/actions/footer; `.is-surface` remains canvas-only. Never embed the old singleton template without feature-detecting the factory.
- Editor Open pickers and external rename prompts retain their originating view across chat changes. Save As uses an isolated view and preserves the caller callback. Embedded New file still uses its own inline creation state. Embedded file opening/cancel/teardown must not close or reset another browser.
- Legacy `file-browser-actions-menu` extensions remain primary-only because they may explicitly target `$store.fileBrowser`. Embedded views retain built-in actions and remote providers, but do not run unsafe singleton-bound third-party row handlers. Settings and connection-field extensions keep their existing shared owner.

- Keep `open(path)` as the shared canvas-modal entry point for workflows that await workspace close; attach/detach must not resolve these waiters.
- Directory path links, Quick Actions, settings and other external Files actions use the shared modal. File clicks originating in Files preserve the canvas host; embedded Welcome file clicks open the modal.
- Editor Open reuses the Files tab in its existing host and returns to the prior tab/listing on completion or cancellation. Explicit external navigation cancels an old picker without restoring its location. Workspace closure retains Files state.
- Keep `openSurface(path, options)` as the retained Files panel entry point; it must load files without opening or awaiting a modal. Reopening during loading, rename/create, or bulk operations must preserve pending state without starting another load.
- Preserve remembered-directory behavior: explicit paths win, then remembered path, then `$WORK_DIR`.
- Empty mounted startup states must self-heal to the `$WORK_DIR` default instead of rendering a blank path and empty list.
- Preserve picker modes for Editor Open and Save As: Editor Open selects one or more text or code files with a pinned primary action, and Save As selects the current folder plus a text-file name (including extensionless names).
- Editor Open omits folder checkboxes while retaining folder navigation. Save As uses a plain filename input filling the footer space before its action buttons.
- Single-entry extensions mount only for one selected item. Built-in batch actions apply to the full selection. Each row exposes one More actions button and the same menu on right-click or Shift+F10. Keep the filename wide on compact screens.
- `file-browser-actions-menu` is the HTML extension point after the built-in dropdown entries, mounted only while the menu is open. Plugins contribute `extensions/webui/file-browser-actions-menu/*.html`; an `x-data` root inherits the row `file` (`name`, `path`, `is_dir`, etc.) and `$store.fileBrowser`. Use `.dropdown-item` buttons; ordinary clicks bubble to close the menu.
- Keep Edit inside the overflow menu for editable text/code files, using the same `.dropdown-item` styling as other entries.
- File Browser settings owns the instance-wide maximum editable file size (default 10 MiB, 1–100), since Editor has no plugin config page. Persist through the scoped settings API, update shared limits immediately, and refresh limits when reopening settings; no agent restart or unrelated setting replacement.
- Load file and text limits from the directory API (`?limits=1` for metadata only). Edit eligibility and upload checks use these backend-owned constraints; Editor tree actions reuse this store. The separate transfer setting defaults to 100 MiB and accepts positive integer MiB without a ceiling. It includes local archive uploads and remote transfers; Backup & Restore remains separate. Files POSTs download preparation and follows the returned single-use URL natively, avoiding JavaScript file Blobs. Generic Connector downloads retain their own route. Preserve remote permission checks.
- Keep Extract available for supported archive files; extraction must create a new sibling folder and reject unsafe member paths and links.
- The dropdown tracks its originating `.file-actions` row, so hidden canvas/modal copies cannot open duplicate teleported menus or plugin entries.
- Settings content lives under `settings/file-browser/`; `openSettings(providerId)` targets the general Settings category and preserves plugin-selected connection drafts.
- Settings sections are ordered Appearance and defaults, Remote folders (including plugin controls), File size limits, then Archives.
- Settings use standard stacked field rows; full-width plugin controls and connection actions use token spacing. Permission controls reuse `.toggle`/`.toggler`. Protocol-specific controls belong in plugin-owned HTML extensions: `file-browser-connection-fields` renders inside the active draft before Save/Cancel; `file-browser-settings` renders independently of the draft. Extensions reuse `.files-connection-actions` and `.files-settings-actions` spacing. SSH key visibility and fingerprint verification are owned by the SSH plugin.
- Settings action groups use the shared small spacing token, wrap whole buttons on narrow screens, and keep table-row actions free of extra vertical margins.
- Managed live connections appear automatically in Remote folders with Open/Test and optional status text. Hide Edit/Remove and omit managed providers from the connection form; CLI/Launcher retain ownership of host paths and scopes.
- The Add connection dropdown floats outside the modal scroll container using shared viewport positioning, without shifting the form; close it on outside click, Escape, resize, and surrounding scroll.
- Add connection stays available with zero installed providers and opens the shared-style thumbnail dropdown. Missing plugins use Install shortcuts that open their actual Plugin Hub Index detail page by key, with a forced Index refresh if a cached entry is missing. Never install directly from Files: users review the plugin page and initiate installation there. Enabled installed plugins show their names without a prefix and open their connection form. Installed-but-disabled entries are disabled with an enablement hint, never offered for reinstallation. Determine installation from `plugins_list`, not enabled provider discovery. Keep plugin management outside this dropdown.
- The command toolbar includes the file-tree toggle and settings. Persist validated preferences in `fileBrowser.preferences`; header sorting and tree toggles remain temporary overrides.
- Remote paths use `/@connections/<provider>/<id>/...` (legacy `/@ssh` is accepted); list via the shared directory API and perform remote actions through `file_browser_connections`. Enabled community providers supply fields and supported permissions to one shared settings UI. Clear connection drafts on modal teardown. Reflect stored permissions in file actions and never route remote paths into local file mutations or Browser/Desktop previews. For SSH, require an explicit username and fingerprint trust and keep private keys/passwords out of responses.
- Icon view reuses list entries and their action/selection/navigation handlers, with token-based grid styling; hide size and modified date in icon view, retaining them in list view. Do not fork file behavior into a second renderer.
- Keep row action menus visible without disabling file-list scrolling; menus may float outside the scroll container but must still close on outside click, Escape, action click, and list scroll.
- The command toolbar remains in place as selection changes. Keep Home, Parent, Refresh, New folder, New file, Upload and selection actions accessible through the shared overflow control at narrow widths.
- Keep the file list readable in narrow canvas/modal containers by hiding the Modified date column before sacrificing the Name or Size columns.
- Use the shared `surface-workspace` palette and flat controls for both path and command rows.
- The list and icon views share type icons, accent-colored folders and ellipsized filenames. On compact panels retain the size column and a 44px checkbox target.
- Keep the list compact: 4px vertical header padding and 5px vertical item padding. The path-submit button is borderless and transparent, with subtle hover feedback.
- New file and New folder retain picker and provider permission guards. Save As and inline creation keep their pinned filename and confirmation controls.
- The list footer offers an inline name filter, Hidden checkbox and visible/total or selected count. Hide dotfiles initially. Filtering clears hidden selections before a bulk operation.
- Breadcrumbs (`preferences.pathBar = buttons`) and Text (`raw`) share one editable path input. Clicking empty breadcrumb space enters editing; the blank trailing slot remains a named keyboard-operable button with a visible focus outline and loading spinner, without a pencil icon. Enter submits the typed path, Escape cancels, and blur exits editing. Preserve caret position while typing and right-end visibility when unfocused.
- Autocomplete lists matching directories through the shared API; `/` must request filesystem root. Complete connection roots (`/@connections/<provider>/<id>` and legacy `/@ssh/<id>`) list their children with or without a trailing slash; namespaces and incomplete connection IDs do not trigger requests. Typing debounces requests; cancellation, new input, navigation, and teardown invalidate pending results. Tab accepts a suggestion and lists its children; Enter submits the typed value. Anchor the dropdown to its owning input so hidden hosts cannot show duplicates.
- Path input and breadcrumb observers belong to their mounted elements and disconnect on destruction. Breadcrumb overflow and toolbar menus are local Alpine state, independent across canvas/modal hosts. Keep whole ancestors accessible through the overflow menu and retain drag/drop on crumbs. Connection provider namespace segments are not browsable ancestors.
- Toolbar menus close on action, outside click, Escape, navigation, surrounding scroll, and resize. Dropdown scrolling itself must remain usable. Keep the loading indicator slot stable and preserve the current listing during fetches; loading rows must be inert to both keyboard and pointer interaction.
- Back/Forward move between history stacks only after successful navigation. Fresh successful navigation clears forward history; failed or same-folder navigation does not. Ignore stale directory responses after newer requests or teardown.
- `beginRename(file)` and `beginNewFolder()` edit names in the shared footer input. `openRenameModal(file, options)` and `openNewFolderModal()` open `rename-modal.html` for primary/external callers and use the inline footer in embedded views; callers need no presentation flags. Rename state captures its directory and duplicate-check entries without retargeting Files. Pending rename/create requests block cancellation until their result is applied. New folder temporarily replaces the Save As filename field and preserves its draft on return. The footer owns its responsive container so filename inputs use the full width on narrow hosts.
- New file configures the existing Files footer in place and creates an empty file through Editor, never overwriting existing names. Save As always opens its own standard modal without tabs and never replaces the retained Files listing or changes the workspace mode. Repeated Save As activates the existing dialog; pending saves and renames block dismissal. Surface docking preserves active Editor Open picker state.

- Single click selects. Ctrl/Command toggles and Shift selects a range in visible sort order. Double-click, double-tap or Enter opens. Arrow keys, Home/End, Space, select-all, F2, F5 and type-to-filter operate in the focused list. Save As retains its explicit save action.
- Copy to… and Move to… select a destination in the originating Files view. Save As retains its own view. Clipboard file transfers require the local record, matching plain text and opaque ID. Remote moves stay within one connection.
- Local removal moves entries into instance Trash on the same filesystem. Restore refuses collisions. Permanent deletion has an explicit confirmation. ZIP creation uses the configured archive limits. Properties summarizes the selection with common or mixed values. Local folder sizes are calculated on request. Octal permission edits apply to the selected files and folders only. Toolbar icon buttons use the shared title-based tooltip system.
- Preserve surface actions that route supported files to Browser, Desktop, or Editor.
- Drag a filename or selected row to move, hold Ctrl to copy, and drop onto folders, breadcrumbs, Parent or another Files pane. Drag blank space to select or sweep the checkbox column. Keep ordinary touch scrolling and cancel active gestures on Escape, blur, pointer cancellation and unmount. Local device drops preserve directory structure and empty folders. Remote capabilities stay provider-owned.
- File and folder entries in the shared tree must not have native or Bootstrap tooltips.
- Keep the tree filter's clear icon in the neutral text palette, matching other file controls.
- Folder names open folders through the host action, expanding them if needed; chevrons toggle branches without navigating. Indent branch status messages to the child-name column at each depth.
- Tree branches load through the existing authenticated file-list API on expansion; filtering covers loaded folders. Keep only the filter above the raw tree, without path, parent, or refresh controls. Show the root row and retain the hierarchy from the configured local starting folder (default `/a0`) or `/@connections` for remote paths, lazily expanding the current directory's ancestors within that root. Store `treeRoot` in `fileBrowser.preferences`, load it on store initialization for Editor-only sessions, and share it with Editor while retaining independent tree state. Path-bar navigation outside the configured root must not widen it. Preserve other loaded branches within the same root and share pending directory loads.
- Keep the tree on the right in canvas and modal modes; at narrow panel widths it overlays the content below the toolbar. Tree file clicks reuse picker selection or existing file-opening actions.
- Scroll the selected row into view after navigation, tree opening, or lazy insertion of that row. Wait for Alpine rendering, skip hidden hosts, and leave manual scrolling alone when unrelated branches expand.
- Scope unmount cleanup to the owning panel element; destroying an old host must not clean up the active modal.
- In list view, display a dash for folder sizes; only files show byte sizes. Do not recursively scan folders for list metadata.

## Work Guidance

- Share markup and store behavior between modal and canvas modes; branch only on explicit component `mode`.
- Keep modal footer relocation compatible with `data-modal-footer` while allowing canvas mode to render inline controls.
- Only standalone modal footers carry `data-modal-footer`; canvas and embedded footers stay inside their panels when the shared canvas shell detaches.

## Verification

- Smoke-test opening Files as a modal and from the right-canvas rail.
- Run `node --test tests/test_file_browser_views.mjs` for chat/view isolation, shared-mode toggling, captured callbacks, picker ownership, permissions and teardown. Run the existing targeted file-browser pytest suites for modal/canvas compatibility.
- Run `tests/test_file_tree.py` for lazy tree loading, path normalization, filtering, errors, and host cleanup.

## Child DOX Index

No child DOX files.

- All local/remote uploads use multipart `upload_work_dir_files`; no remote base64 lane. Shared helpers enforce transfer policy. Files archive controls expose independent expanded-size and entry-count budgets with no upper ceiling.
