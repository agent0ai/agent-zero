# attachment_manager.py DOX

## Purpose

- Own the `attachment_manager.py` helper module.
- This module tracks uploaded or generated attachments associated with chat contexts.
- Keep this file-level DOX profile synchronized with `attachment_manager.py` because this directory is intentionally flat.

## Ownership

- `attachment_manager.py` owns the runtime implementation.
- `attachment_manager.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `AttachmentManager` (no explicit base class)
  - `is_allowed_file(self, filename: str) -> bool`
  - `get_file_type(self, filename: str) -> str`
  - `get_file_extension(filename: str) -> str`
  - `validate_mime_type(self, file) -> bool`
  - `save_file(self, file: FileStorage, name: str) -> Tuple[str, Dict]`
  - `generate_image_preview(self, image_path: str, max_size: int=...) -> Optional[str]`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, settings/state persistence.
- Imported dependency areas include: `PIL`, `base64`, `helpers.print_style`, `helpers.security`, `io`, `os`, `typing`, `werkzeug.datastructures`.

## Key Concepts

- Important called helpers/classes observed in the source: `os.makedirs`, `self.get_file_extension`, `set.union`, `filename.rsplit.lower`, `safe_filename`, `os.path.join`, `self.get_file_type`, `file.save`, `ValueError`, `self.generate_image_preview`, `PrintStyle.error`, `img.thumbnail`, `io.BytesIO`, `img.save`, `base64.b64encode.decode`, `mime_type.split`, `img.convert`, `filename.rsplit`, `base64.b64encode`, `buffer.getvalue`.
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
