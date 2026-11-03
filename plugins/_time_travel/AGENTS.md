# Time Travel Plugin DOX

## Purpose

- Own Agent Zero workspace history, diff inspection, travel, snapshots, and revert for selectable Agent Zero workdir/project workspaces under `/a0/usr`.

## Ownership

- `helpers/time_travel.py` owns history storage, diff, travel, snapshot, preview, and revert mechanics.
- `api/` owns selectable workspace list, history list, diff, preview, revert, snapshot, and travel endpoints.
- `webui/` owns the time-travel panel, workspace selector, store, main surface, and thumbnail.
- `plugin.yaml` and `extensions/` own metadata and hook contributions.

## Local Contracts

- Keep history operations scoped to Agent Zero-owned workdir/project workspaces.
- Display-path mapping must resolve real paths inside a dev checkout that itself lives under `/a0`, without doubling the base dir.
- Canonical workspace display paths are posix-normalized and workspace ids derive from that normalized string, so equivalent inputs keep stable ids.
- Nested dev checkouts switch once from physical to logical canonical paths, so their workspace ids change and older shadow repos stay on disk unreachable; production instances based at `/a0` keep their ids.
- Revert and travel operations must avoid unintended writes outside managed workspace paths.
- Preserve enough metadata for clear preview and diff inspection before destructive actions.

## Work Guidance

- Coordinate API and UI changes so users can inspect effects before applying travel or revert operations.

## Verification

- Smoke-test workspace selection, snapshot, list, diff, preview, travel, and revert flows after changes.

## Child DOX Index

No child DOX files.
