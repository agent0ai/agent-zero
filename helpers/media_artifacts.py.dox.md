# media_artifacts.py DOX

## Purpose

- Own the `media_artifacts.py` helper module.
- This module validates, decodes, names, and normalizes media artifact payloads.
- Keep this file-level DOX profile synchronized with `media_artifacts.py` because this directory is intentionally flat.

## Ownership

- `media_artifacts.py` owns the runtime implementation.
- `media_artifacts.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `MediaArtifactError` (`ValueError`)
- `EmptyBase64Data` (`MediaArtifactError`)
- `InvalidBase64Data` (`MediaArtifactError`)
- `ArtifactTooLarge` (`MediaArtifactError`)
- `Base64Payload` (no explicit base class)
- `ImageDataUrl` (no explicit base class)
- `SavedArtifact` (no explicit base class)
- Top-level functions:
- `compact_base64(data: str) -> str`
- `estimated_base64_decoded_size(data: str) -> int`
- `decode_base64_payload(data: str, max_bytes: int | None=...) -> Base64Payload`
- `normalize_mime(mime_type: str, default: str=..., required_prefix: str=...) -> str`
- `guess_extension(mime_type: str, fallback: str=...) -> str`
- `filename_from_uri(uri: str) -> str`
- `safe_filename(value: str, default: str=..., default_extension: str=...) -> str`
- `image_data_url_from_base64(data: str, mime_type: str=..., max_bytes: int | None=...) -> ImageDataUrl`
- `save_base64_artifact(data: str, mime_type: str=..., directory_parts: tuple[str, ...], preferred_name: str=..., default_filename: str=..., max_bytes: int | None=...) -> SavedArtifact`
- Notable constants/configuration names: `DEFAULT_MAX_ARTIFACT_SIZE_BYTES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, network calls.
- Imported dependency areas include: `__future__`, `base64`, `binascii`, `dataclasses`, `helpers`, `mimetypes`, `pathlib`, `urllib.parse`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `dataclass`, `join`, `compact_base64`, `Base64Payload`, `str.strip.lower`, `str.strip`, `urlparse`, `decode_base64_payload`, `normalize_mime`, `ImageDataUrl`, `guess_extension`, `safe_filename`, `Path`, `artifact_dir.mkdir`, `path.write_bytes`, `SavedArtifact`, `super.__init__`, `EmptyBase64Data`, `estimated_base64_decoded_size`, `base64.b64decode`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_mcp_handler_multimodal.py`
  - `tests/test_media_artifacts.py`

## Child DOX Index

No child DOX files.
