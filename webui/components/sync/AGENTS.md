# Sync Components DOX

## Purpose

- Own WebUI state synchronization status UI and store.

## Ownership

- `sync-store.js` owns sync status state.
- `sync-status.html` owns sync indicator markup and the `sync-status-end`
  extension point for connection-related controls.

## Local Contracts

- Keep sync state compatible with WebSocket state-sync events.
- Avoid noisy user-facing alerts for transient sync state unless existing UX expects them.
- Keep the compact status cluster free of native title tooltips; interactive
  extensions must provide accessible names directly.

## Work Guidance

- Coordinate sync changes with WebSocket client and backend WebSocket extensions.

## Verification

- Smoke-test connection, reconnect, and state refresh indicators after changes.

## Child DOX Index

No child DOX files.
