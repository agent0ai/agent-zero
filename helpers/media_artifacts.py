from __future__ import annotations

import base64
import binascii
import mimetypes
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from helpers import files


DEFAULT_MAX_ARTIFACT_SIZE_BYTES = 25 * 1024 * 1024


class MediaArtifactError(ValueError):
    pass


class EmptyBase64Data(MediaArtifactError):
    pass


class InvalidBase64Data(MediaArtifactError):
    pass


class ArtifactTooLarge(MediaArtifactError):
    def __init__(self, size: int, limit: int):
        super().__init__(f"artifact is too large ({size} bytes, limit {limit} bytes)")
        self.size = size
        self.limit = limit


@dataclass(frozen=True)
class Base64Payload:
    data: str
    payload: bytes
    size: int


@dataclass(frozen=True)
class ImageDataUrl:
    url: str
    mime: str
    size: int


@dataclass(frozen=True)
class SavedArtifact:
    path: str
    mime: str
    size: int


def compact_base64(data: str) -> str:
    return "".join(char for char in str(data or "") if not char.isspace())


def estimated_base64_decoded_size(data: str) -> int:
    compact_length = len(compact_base64(data))
    return (compact_length * 3) // 4


def decode_base64_payload(
    data: str,
    *,
    max_bytes: int | None = None,
) -> Base64Payload:
    compact = compact_base64(data)
    if not compact:
        raise EmptyBase64Data("base64 data is empty")

    if max_bytes is not None:
        estimated_size = estimated_base64_decoded_size(compact)
        if estimated_size > max_bytes:
            raise ArtifactTooLarge(estimated_size, max_bytes)

    try:
        payload = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InvalidBase64Data("base64 data could not be decoded") from exc

    if max_bytes is not None and len(payload) > max_bytes:
        raise ArtifactTooLarge(len(payload), max_bytes)

    return Base64Payload(data=compact, payload=payload, size=len(payload))


def normalize_mime(
    mime_type: str,
    *,
    default: str = "application/octet-stream",
    required_prefix: str = "",
) -> str:
    value = str(mime_type or "").strip().lower()
    if not value:
        return default
    if required_prefix and not value.startswith(required_prefix):
        return default
    return value


def guess_extension(mime_type: str, fallback: str = ".bin") -> str:
    ext = mimetypes.guess_extension(str(mime_type or "").strip().lower()) or fallback
    return ".jpg" if ext == ".jpe" else ext


def filename_from_uri(uri: str) -> str:
    value = str(uri or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    return Path(parsed.path or value).name


def safe_filename(
    value: str,
    *,
    default: str = "artifact.bin",
    default_extension: str = ".bin",
) -> str:
    source = str(value or "").strip() or default
    cleaned = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "_"
        for char in source
    )
    cleaned = cleaned.strip("._") or default
    if "." not in cleaned:
        ext = default_extension if default_extension.startswith(".") else f".{default_extension}"
        cleaned += ext
    return cleaned


def image_data_url_from_base64(
    data: str,
    *,
    mime_type: str = "image/png",
    max_bytes: int | None = None,
) -> ImageDataUrl:
    payload = decode_base64_payload(data, max_bytes=max_bytes)
    safe_mime = normalize_mime(
        mime_type,
        default="image/png",
        required_prefix="image/",
    )
    return ImageDataUrl(
        url=f"data:{safe_mime};base64,{payload.data}",
        mime=safe_mime,
        size=payload.size,
    )


def save_base64_artifact(
    data: str,
    *,
    mime_type: str = "application/octet-stream",
    directory_parts: tuple[str, ...],
    preferred_name: str = "",
    default_filename: str = "artifact.bin",
    max_bytes: int | None = None,
) -> SavedArtifact:
    payload = decode_base64_payload(data, max_bytes=max_bytes)
    safe_mime = normalize_mime(mime_type)
    preferred_filename = filename_from_uri(preferred_name) or default_filename
    default_extension = guess_extension(safe_mime, Path(default_filename).suffix or ".bin")
    filename = safe_filename(
        preferred_filename,
        default=default_filename,
        default_extension=default_extension,
    )
    filename_path = Path(filename)
    stem = filename_path.stem or Path(default_filename).stem or "artifact"
    suffix = filename_path.suffix or default_extension

    artifact_dir = Path(files.get_abs_path(*directory_parts))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
    path.write_bytes(payload.payload)

    return SavedArtifact(
        path=files.normalize_a0_path(str(path)),
        mime=safe_mime,
        size=payload.size,
    )
