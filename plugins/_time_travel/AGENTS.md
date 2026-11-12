# Time Travel Plugin DOX

## Purpose

- Own Agent Zero workspace history, diff inspection, travel, snapshots, and revert for selectable Agent Zero workdir/project workspaces under `/a0/usr`.

## Ownership

- `helpers/time_travel.py` owns history storage, diff, travel, snapshot, preview, and revert mechanics.
- `helpers/locking.py` owns reentrant cross-process workspace locks; `helpers/retention.py` shares them for cleanup.
- `helpers/compaction.py` owns opt-in ancestry expiry, checkpoint creation, atomic ref updates and Git object reclamation.
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
- `capture_exclude_patterns` uses workspace-relative Git-style patterns in addition to immutable built-in exclusions; `capture_max_file_mb` defaults to 0 (unlimited). Oversized files are reported by capture/current inspection. Capture must fail on unreadable directories rather than commit an incomplete tree. Automatic captures recheck plugin enablement before scheduling and execution.
- Snapshot expiry is opt-in (`history_retention_enabled: false`). Its suggested limits are 500 recent snapshots and 30 days; either limit can be disabled with 0. The current state and full-tree checkpoint boundaries survive, and retained commit messages, metadata, timestamps and file trees remain intact. Current state/checkpoints can exceed the recent-snapshot count; this is not a byte quota.
- Compaction expires preserved tips outside the retained window and rewrites retained ancestry in one compare-and-swap ref transaction, then resets the shadow index, expires reflogs and runs non-aggressive GC under the workspace lock. It never edits workspace files. `compaction.pending` survives failure and requests a GC retry; unchanged histories do not trigger repeated GC. Unsupported refs/merges/headers or symlinked storage fail closed.
- Compaction runs in the POSIX framework runtime. Timed-out Git maintenance kills its whole process group before releasing the workspace lock, including pack/repack children.
- Checkpoints can be traveled to but cannot be reverted against an empty tree. Enabling expiry can change retained commit ids; users must refresh stale selections. Storage UI reports Git object bytes, not a promised disk ceiling.
- Snapshot/travel activity is recorded separately from Git maintenance, so compaction does not restart the inactive-workspace expiry clock; older histories inherit their last filesystem activity on first maintenance.
- Binary previews return file statistics without generating an unused binary patch; revert still uses Git's binary patch support.
- Preserve enough metadata for clear preview and diff inspection before destructive actions.

## Work Guidance

- Coordinate API and UI changes so users can inspect effects before applying travel or revert operations.

## Verification

- Smoke-test workspace selection, snapshot, list, diff, preview, travel, and revert flows after changes.

## Child DOX Index

No child DOX files.
