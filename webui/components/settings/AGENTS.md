# Settings Components DOX

## Purpose

- Own WebUI settings shell and built-in settings subsections.

## Ownership

- `settings.html` and `settings-store.js` own the settings shell and state.
- Subdirectories own settings areas such as agent, external, developer, MCP, backup, plugins, secrets, skills, tunnel, and A2A.
- `mcp/client/` owns the global/project MCP server manager, server search, raw JSON editor surface, examples modal, server tool detail modal, MCP scanner modal, scan checks, and scan prompt assets.
- `skills/` owns skill listing, importing, standalone skill scanning, uploaded archive scan preparation UI, scanner modal, scan checks, and scan prompt assets.

## Local Contracts

- `file-browser/` owns the Files settings page, with appearance, remote folders/plugin controls, file limits and archives in that order. Use standard stacked Settings field rows rather than a bespoke two-column grid. The Files gear and provider plugin shortcuts open this category. Appearance includes the browser-local tree starting folder shared by Files and Editor, defaulting to `/a0`. Remember-location is a normal Settings draft; existing immediate Files limit writes also update the open Settings draft to avoid stale overwrite.
- Keep settings payloads synchronized with backend APIs and plugin settings contracts.
- Settings tabs that expose plugin `settings_sections` must mount `settings/plugins/plugins-subsection.html` with matching `data-tab` and sidebar/nav section IDs.
- Do not store secrets in localStorage, URLs, or console output.
- Preserve Store Gating and modal footer conventions in settings components.
- Interface control visibility is edited as a Save/Cancel draft, persisted with instance settings, and applied through the shared frontend preference store after Settings saves successfully.
- Bundled controls contributed by plugins add their Interface row through
  `interface-controls-end` and register visibility defaults with the shared
  preference store.
- MCP manager tool toggles write `disabled_tools` into the draft JSON and require Apply before changing the running MCP tool set.
- Confirmed MCP server removals apply immediately and refresh server status; other MCP manager draft edits still require Apply.
- MCP manager local command forms accept shell-style command and argument lines; quote argument values that intentionally contain spaces.

- Interface nests registered canvas surfaces under the right canvas rail control, using their plain titles, with independent mobile/desktop visibility in the same Save/Cancel draft. `open(tab, section)` supports direct section entry; initial scrolling waits for component markup and uses instant positioning so scroll anchoring follows later content growth.

## Work Guidance

- Prefer subsection-local stores for complex settings areas.
- Coordinate plugin settings UI changes with `webui/components/plugins/` and `plugins/AGENTS.md`.
- Keep MCP scanner checks and prompt assets close to the MCP client modal so scanner behavior remains reviewable with the UI that invokes it.
- Keep Skills scanner checks and prompt assets close to the Skills settings section so scanner behavior remains reviewable with import and standalone scan entry points.
- Keep MCP manager search and toggle affordances consistent between global and project scope because both are rendered by the same client modal.

## Verification

- Smoke-test changed settings tabs, Interface mobile/desktop selectors, and save/reload behavior after visible or API changes.

## Child DOX Index

No child DOX files.
