# Pin to Top Plugin DOX

## Purpose

- Own built-in pinning for chats, scheduled tasks, and project folders in the sidebar.

## Ownership

- `plugin.yaml` owns the always-enabled plugin metadata.
- `helpers/pins.py` and `api/` own persistent pin state and authenticated toggle/read endpoints.
- `webui/pin-to-top-store.js` owns row ordering, divider callbacks, and the project pin interface used by Folder view.
- `extensions/webui/sidebar-row-actions-menu/` owns the dropdown action.
- `extensions/webui/initFw_end/pin-indicators.js` decorates existing chat, parallel-child, and task titles with passive Alpine-bound icons; indicator styling belongs to this plugin's menu extension.

## Local Contracts

- Pin state is separated into `chat`, `task`, and `project` groups and stored under the `plugin_pin_to_top` persistent KVP key; older state without `project` remains valid.
- Project keys are validated project directory names, with `""` reserved for the virtual **No project** folder. Adding a named project pin requires its project header to exist; removing a stale pin remains possible. Empty chat/task IDs and missing project IDs remain invalid.
- **No project** is pinned by default with timestamp `1.0`, ahead of dated project pins. Persist `no_project_pin_initialized` with pin changes so an explicit unpin survives reloads and changes to other pins; older pin state receives the default without losing existing pins.
- Folder view reads `pins.project`, calls `isProjectPinned(name)` / `toggleProjectPin(name)`, and can sort groups with `sortItems("project", items)` where each item has `id: name`.
- The plugin must register sidebar row-list callbacks; it must not patch chat/task stores or inject controls directly into rows.
- Pinned items sort before unpinned items, older pins remain first, and existing order is preserved within the unpinned group.
- The menu label and icon must reflect whether the active row is pinned.
- Keep pin markup, styling, and visibility inside this plugin. The idempotent startup decorator handles added rows in both list views; Alpine owns icon reactivity and cleanup when rows are removed. Do not add pin-specific hooks to the core sidebar or copy its row templates.
- Decorate only titles owned by the shared `chat-tree.html` and `task-row.html` components; community plugins may reuse sidebar styling classes with different data scopes.

## Work Guidance

- Keep the plugin always enabled and configuration-free.
- Keep runtime state under `usr/` through the shared persistent KVP helper.

## Verification

- Run `pytest plugins/_pin_to_top/tests tests/test_sidebar_row_actions.py`.
- Verify one reactive indicator per parent, worker, and task title after pin/unpin, folder collapse/remount, and flat/folder switching; core sidebar files must stay free of pin-specific code.

## Child DOX Index

No child DOX files.
