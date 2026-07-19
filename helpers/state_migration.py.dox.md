# state_migration.py DOX

## Purpose

- Own the `state_migration.py` helper module.
- This module moves retired state tree paths to current runtime locations.
- Keep this file-level DOX profile synchronized with `state_migration.py` because this directory is intentionally flat.

## Ownership

- `state_migration.py` owns the runtime implementation.
- `state_migration.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `migrate_retired_state_tree(source: Path, destination: Path, owner: str, migrated: list[str], warnings: list[str], errors: list[str]) -> None`: Move retired plugin state into its plugin-owned state directory.
- `_move_path(source: Path, target: Path, migrated: list[str]) -> None`
- `_next_conflict_path(path: Path) -> Path`
- `_remove_empty_dir(path: Path, owner: str, warnings: list[str]) -> None`
- `_same_path(left: Path, right: Path) -> bool`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, plugin state, settings/state persistence.
- Imported dependency areas include: `__future__`, `pathlib`, `shutil`.

## Key Concepts

- Important called helpers/classes observed in the source: `_same_path`, `final_target.parent.mkdir`, `shutil.move`, `path.with_name`, `_move_path`, `source.is_dir`, `target.is_dir`, `source.rmdir`, `target.exists`, `target.is_symlink`, `_next_conflict_path`, `candidate.exists`, `candidate.is_symlink`, `path.rmdir`, `source.exists`, `source.is_symlink`, `destination.mkdir`, `_remove_empty_dir`, `source.iterdir`, `left.resolve`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
