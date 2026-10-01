# Sync Components DOX

## Purpose

- Own WebUI state synchronization status UI and store.

## Ownership

- `sync-store.js` owns sync status state.
- `sync-status.html` owns sync indicator markup and the `sync-status-end`
  extension point for connection-related controls.

## Local Contracts

- Keep sync state compatible with WebSocket state-sync events.
- Apply `state_push` snapshots sequentially because WebSocket subscribers do not await async callbacks; later pushes must not race earlier full renders.
- Coalesce contiguous pending pushes for the same runtime, context, and log GUID before rendering. Keep the latest version of every distinct log record, preserve omitted collection deltas, and validate the entire sequence span; gaps and resets retain normal resynchronization behavior. Pass notifications in arrival order because grouped-toast replacement has read-status side effects.
- A queued state push that finishes after transport loss must not overwrite the
  `DISCONNECTED` mode or flush reconnect notifications.
- Avoid noisy user-facing alerts for transient sync state unless existing UX expects them.
- Keep the compact status cluster free of native title tooltips; interactive
  extensions must provide accessible names directly.

## Work Guidance

- Coordinate sync changes with WebSocket client and backend WebSocket extensions.

## Verification

- Smoke-test connection, reconnect, and state refresh indicators after changes.

## Child DOX Index

No child DOX files.
