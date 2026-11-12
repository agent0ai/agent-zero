# Time Travel Plugin DOX

## Purpose

- Own Agent Zero workspace history, diff inspection, travel, snapshots, and revert for selectable Agent Zero workdir/project workspaces under `/a0/usr`.

## Ownership

- `helpers/time_travel.py` owns history storage, diff, travel, snapshot, preview, and revert mechanics.
- `helpers/locking.py` owns reentrant cross-process workspace locks; `helpers/retention.py` shares them for cleanup.
- `api/` owns selectable workspace list, history list, diff, preview, revert, snapshot, and travel endpoints.
- `webui/` owns the time-travel panel, workspace selector, store, main surface, and thumbnail.
- `plugin.yaml` and `extensions/` own metadata and hook contributions.

## Local Contracts

- Keep history operations scoped to Agent Zero-owned workdir/project workspaces.
- Display-path mapping must resolve real paths inside a dev checkout that itself lives under `/a0`, without doubling the base dir.
- Canonical workspace display paths are posix-normalized and workspace ids derive from that normalized string, so equivalent inputs keep stable ids.
- Nested dev checkouts switch once from physical to logical canonical paths, so their workspace ids change and older shadow repos stay on disk unreachable; production instances based at `/a0` keep their ids.
- Revert and travel operations must avoid unintended writes outside managed workspace paths.
- Git path arguments are literal. Capture exclusions also protect restore operations, including previously captured files and symlinked parent directories; conflicting restores fail before modifying files.
- Serialize complete history operations per workspace. Lock files live outside removable workspace histories; cleanup skips busy histories, symlinks and unknown directory names. Failed owner discovery must not classify live histories as orphaned.
- History listing never stages or scans workspace files. Pagination and file-name filtering use bounded Git batches; file statistics are batched per commit. Snapshots retain the index stat cache and remove deleted/excluded entries explicitly.
- Current-change inspection is an explicit `history_present` action. Its temporary repository borrows saved objects read-only and is removed afterward; `present: null` means unchecked, never clean. Git work runs outside API event loops, and UI responses remain scoped to the active workspace/request.
- Preserve enough metadata for clear preview and diff inspection before destructive actions.

## Work Guidance

- Coordinate API and UI changes so users can inspect effects before applying travel or revert operations.

## Verification

- Smoke-test workspace selection, snapshot, list, diff, preview, travel, and revert flows after changes.

## Child DOX Index

No child DOX files.
