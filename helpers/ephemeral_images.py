from __future__ import annotations

import base64
import threading
import time
import uuid
from dataclasses import dataclass


REF_PREFIX = "a0-ephemeral-image://"
DEFAULT_TTL_SECONDS = 15 * 60


@dataclass(frozen=True)
class EphemeralImage:
    ref: str
    context_id: str
    mime: str
    data: str
    name: str
    created_at: float
    expires_at: float

    @property
    def data_url(self) -> str:
        return f"data:{self.mime};base64,{self.data}"

    @property
    def display_name(self) -> str:
        return self.name or display_ref(self.ref)


_store: dict[str, EphemeralImage] = {}
_lock = threading.RLock()


def put_image_bytes(
    *,
    context_id: str,
    mime: str,
    payload: bytes,
    name: str = "",
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> str:
    data = base64.b64encode(bytes(payload or b"")).decode("ascii")
    return put_image(
        context_id=context_id,
        mime=mime,
        data=data,
        name=name,
        ttl_seconds=ttl_seconds,
    )


def put_image(
    *,
    context_id: str,
    mime: str,
    data: str,
    name: str = "",
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> str:
    compact_data = _compact_base64(data)
    if not compact_data:
        raise ValueError("ephemeral image data is empty")
    base64.b64decode(compact_data, validate=True)

    normalized_mime = _normalize_mime(mime)
    now = time.time()
    ref = f"{REF_PREFIX}{uuid.uuid4().hex}"
    image = EphemeralImage(
        ref=ref,
        context_id=str(context_id or "").strip(),
        mime=normalized_mime,
        data=compact_data,
        name=str(name or "").strip(),
        created_at=now,
        expires_at=now + max(1.0, float(ttl_seconds or DEFAULT_TTL_SECONDS)),
    )
    with _lock:
        _prune_expired_locked(now)
        _store[ref] = image
    return ref


def is_ref(value: object) -> bool:
    return str(value or "").strip().startswith(REF_PREFIX)


def display_ref(ref: str) -> str:
    value = str(ref or "").strip()
    if not is_ref(value):
        return value
    return f"{REF_PREFIX}<ephemeral>"


def get_image(ref: str, *, context_id: str = "") -> EphemeralImage | None:
    return _resolve_image(ref, context_id=context_id, consume=False)


def consume_image(ref: str, *, context_id: str = "") -> EphemeralImage | None:
    return _resolve_image(ref, context_id=context_id, consume=True)


def delete_image(ref: str) -> None:
    with _lock:
        _store.pop(str(ref or "").strip(), None)


def clear_context(context_id: str) -> None:
    normalized_context = str(context_id or "").strip()
    with _lock:
        for ref, image in list(_store.items()):
            if image.context_id == normalized_context:
                _store.pop(ref, None)


def _resolve_image(ref: str, *, context_id: str = "", consume: bool) -> EphemeralImage | None:
    value = str(ref or "").strip()
    if not is_ref(value):
        return None

    now = time.time()
    with _lock:
        _prune_expired_locked(now)
        image = _store.get(value)
        if image is None:
            return None
        requested_context = str(context_id or "").strip()
        if requested_context and image.context_id and image.context_id != requested_context:
            return None
        if consume:
            _store.pop(value, None)
        return image


def _compact_base64(data: str) -> str:
    return "".join(char for char in str(data or "") if not char.isspace())


def _normalize_mime(mime: str) -> str:
    value = str(mime or "").strip().lower()
    return value if value.startswith("image/") else "image/jpeg"


def _prune_expired_locked(now: float | None = None) -> None:
    current = time.time() if now is None else float(now)
    for ref, image in list(_store.items()):
        if image.expires_at <= current:
            _store.pop(ref, None)
