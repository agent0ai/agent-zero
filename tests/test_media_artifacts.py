from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import media_artifacts


def test_image_data_url_from_base64_compacts_and_normalizes_mime():
    encoded = " \n" + base64.b64encode(b"image-bytes").decode("ascii") + "\n"

    image = media_artifacts.image_data_url_from_base64(
        encoded,
        mime_type="IMAGE/WEBP",
    )

    assert image.mime == "image/webp"
    assert image.size == 11
    assert image.url == "data:image/webp;base64,aW1hZ2UtYnl0ZXM="


def test_decode_base64_payload_rejects_empty_invalid_and_oversized_data():
    with pytest.raises(media_artifacts.EmptyBase64Data):
        media_artifacts.decode_base64_payload(" \n ")

    with pytest.raises(media_artifacts.InvalidBase64Data):
        media_artifacts.decode_base64_payload("not base64")

    with pytest.raises(media_artifacts.ArtifactTooLarge) as exc_info:
        media_artifacts.decode_base64_payload("ZmFrZQ==", max_bytes=2)

    assert exc_info.value.size == media_artifacts.estimated_base64_decoded_size("ZmFrZQ==")
    assert exc_info.value.limit == 2


def test_save_base64_artifact_uses_uri_filename_and_normalized_a0_path(monkeypatch, tmp_path):
    def fake_get_abs_path(*parts):
        return str(tmp_path.joinpath(*parts))

    def fake_normalize_a0_path(path: str):
        return "/a0/" + str(Path(path).relative_to(tmp_path)).replace("\\", "/")

    monkeypatch.setattr(media_artifacts.files, "get_abs_path", fake_get_abs_path)
    monkeypatch.setattr(media_artifacts.files, "normalize_a0_path", fake_normalize_a0_path)

    artifact = media_artifacts.save_base64_artifact(
        base64.b64encode(b"audio-bytes").decode("ascii"),
        mime_type="audio/mpeg",
        directory_parts=("tmp", "media-test"),
        preferred_name="memory://venice/generated track.mp3",
        default_filename="fallback.bin",
    )

    assert artifact.mime == "audio/mpeg"
    assert artifact.size == 11
    assert artifact.path.startswith("/a0/tmp/media-test/generated_track_")
    assert artifact.path.endswith(".mp3")
    assert (tmp_path / artifact.path.removeprefix("/a0/")).read_bytes() == b"audio-bytes"
