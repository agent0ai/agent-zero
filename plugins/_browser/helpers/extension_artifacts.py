"""Consume verified screenshot output into Core-owned chat media, never a peer path."""

import io
import hashlib
import re
from typing import Any, Callable

from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding, BrowserBridgeArtifactReceiver, MAX_ARTIFACT_BYTES


class ExtensionArtifactError(ValueError):
    pass


class ExtensionScreenshotMaterializer:
    def __init__(self, *, receiver: BrowserBridgeArtifactReceiver, lease_for: Callable,
                 current: Callable[[ArtifactBinding], bool], save_image: Callable | None = None):
        self._receiver = receiver
        self._transport_profile = receiver.transport_profile
        self._lease_for = lease_for
        self._current = current
        self._save_image = save_image or _save_chat_image

    def __call__(self, binding, call, completion) -> dict[str, Any]:
        result = completion.result
        if (call.action != "screenshot" or call.target is None or not completion.ok or completion.receipts
                or len(completion.artifacts) != 1 or not isinstance(result, dict)
                or set(result) != {"lease_id", "browser_id", "tab_handle", "artifact_id"}):
            raise ExtensionArtifactError("INVALID_SCREENSHOT_RESULT")
        handle = call.target["tab_handle"]
        lease = self._lease_for(binding, handle)
        if (lease is None or result["lease_id"] != lease.lease_id
                or result["browser_id"] != handle or result["tab_handle"] != handle):
            raise ExtensionArtifactError("LEASE_CONFLICT")
        claimed = completion.artifacts[0]
        expected_mime = "image/jpeg" if call.args.get("format") == "jpeg" else "image/png"
        if (not isinstance(claimed, dict) or set(claimed) != {"artifact_id", "mime_type", "byte_count", "sha256", "purpose"}
                or claimed["artifact_id"] != result["artifact_id"] or claimed["purpose"] != "screenshot"
                or claimed["mime_type"] != expected_mime or type(claimed["byte_count"]) is not int
                or not 1 <= claimed["byte_count"] <= MAX_ARTIFACT_BYTES
                or not isinstance(claimed["sha256"], str) or re.fullmatch(r"sha256:[a-f0-9]{64}", claimed["sha256"]) is None):
            raise ExtensionArtifactError("INVALID_SCREENSHOT_DESCRIPTOR")
        artifact = ArtifactBinding(
            binding.principal, binding.connector_sid, binding.load_generation_id, binding.bridge_id,
            binding.context_id, binding.browser_session_id, binding.turn_id, binding.action_id, binding.op_id,
            claimed["artifact_id"], "output", "screenshot",
            transport_profile=self._transport_profile,
        )

        def consume(stream, descriptor):
            if descriptor.as_dict() != claimed:
                raise ExtensionArtifactError("ARTIFACT_INTEGRITY_MISMATCH")
            payload = stream.read(MAX_ARTIFACT_BYTES + 1)
            if len(payload) != descriptor.byte_count or "sha256:" + hashlib.sha256(payload).hexdigest() != descriptor.sha256:
                raise ExtensionArtifactError("ARTIFACT_INTEGRITY_MISMATCH")
            _validate_image(payload, expected_mime)
            # Decoding/verification cannot extend a turn or revive a lease.
            current_lease = self._lease_for(binding, handle)
            if (self._current(artifact) is not True or current_lease is None
                    or current_lease.lease_id != lease.lease_id or current_lease.origin != lease.origin):
                raise ExtensionArtifactError("SCOPE_DENIED")
            saved = self._save_image(context_id=binding.context_id, payload=payload, mime_type=expected_mime,
                                     category="screenshots", source="browser", preferred_name="browser-screenshot",
                                     max_bytes=MAX_ARTIFACT_BYTES)
            return {
                "browser_id": handle, "tab_handle": handle, "lease_id": lease.lease_id,
                "context_id": binding.context_id, "path": saved.path, "a0_path": saved.a0_path,
                "mime": expected_mime, "ephemeral": False, "chat_scoped": True,
                "vision_load": {"tool_name": "vision_load", "tool_args": {"paths": [saved.a0_path]}},
            }

        return self._receiver.consume(artifact, consume)


def _validate_image(payload: bytes, mime: str) -> None:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != ("JPEG" if mime == "image/jpeg" else "PNG") or image.width < 1 or image.height < 1 or image.width * image.height > 64_000_000:
                raise ValueError("invalid screenshot dimensions or format")
            image.verify()
    except Exception:
        raise ExtensionArtifactError("INVALID_SCREENSHOT_IMAGE") from None


def _save_chat_image(**kwargs):
    from helpers.chat_media import save_image_bytes

    return save_image_bytes(**kwargs)
