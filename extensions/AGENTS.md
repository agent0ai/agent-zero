# Extensions DOX

## Purpose

- Own core lifecycle extension implementations for backend and WebUI extension points.
- Keep built-in hook behavior ordered, discoverable, and compatible with plugin extension discovery.

## Ownership

- `python/` contains backend lifecycle hooks executed through `helpers.extension`.
- `webui/` contains frontend extension contributions loaded through `webui/js/extensions.js`.
- Plugin-specific extensions belong inside each plugin's `extensions/` directory.

## Local Contracts

- Extension directory names are runtime extension point names.
- File ordering matters when names include numeric prefixes.
- Extensions must be safe to run repeatedly when the lifecycle point can fire multiple times.
- Secret masking, auth, security, and persistence extensions must not be bypassed by convenience changes.

## Work Guidance

- Keep extension code small and focused on its hook point.
- Move shared logic into `helpers/` when it is reused outside one extension.
- Coordinate changes with plugin extension docs and tests when extension point semantics change.

## Verification

- Run targeted lifecycle, prompt, stream, WebSocket, or WebUI extension tests for changed hook points.
- Smoke-test startup when changing initialization, migration, or system-prompt extensions.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [python/AGENTS.md](python/AGENTS.md) | Backend lifecycle extension hook files. |
| [webui/AGENTS.md](webui/AGENTS.md) | Frontend extension contributions. |
