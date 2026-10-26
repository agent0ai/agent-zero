from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import chat_media, media_artifacts


@pytest.mark.parametrize("size", range(1, 13))
@pytest.mark.parametrize("whitespace", [False, True])
def test_decoded_size_limit_accepts_exact_boundary(size, whitespace):
    data = bytes(range(size))
    encoded = base64.b64encode(data).decode("ascii")
    if whitespace:
        encoded = (
            " \n"
            + "\r\n".join(encoded[i : i + 4] for i in range(0, len(encoded), 4))
            + "\t"
        )

    assert media_artifacts.estimated_base64_decoded_size(encoded) == size
    result = media_artifacts.decode_base64_payload(encoded, max_bytes=size)
    assert result.payload == data
    assert result.size == size


@pytest.mark.parametrize("size", range(1, 13))
def test_oversized_payload_is_rejected_before_decoding(monkeypatch, size):
    encoded = base64.b64encode(bytes(range(size))).decode("ascii")

    def unexpected_decode(*args, **kwargs):
        pytest.fail("Oversized input must be rejected before decoding")

    monkeypatch.setattr(media_artifacts.base64, "b64decode", unexpected_decode)
    with pytest.raises(media_artifacts.ArtifactTooLarge) as exc_info:
        media_artifacts.decode_base64_payload(encoded, max_bytes=size - 1)
    assert exc_info.value.limit == size - 1


@pytest.mark.parametrize(
    "encoded", ["=YQ=", "Y===", "====", "YQ==x", "YQ===", "YQ", "☃", "YWJj☃="]
)
def test_malformed_payload_remains_invalid(encoded):
    with pytest.raises(media_artifacts.InvalidBase64Data):
        media_artifacts.decode_base64_payload(encoded, max_bytes=64)


@pytest.mark.parametrize(
    "encoded", ["A" * 400, "=" * 400, "A" * 396 + "====", "☃" * 400]
)
def test_large_malformed_payload_is_rejected_before_decoding(monkeypatch, encoded):
    def unexpected_decode(*args, **kwargs):
        pytest.fail("Oversized input must be rejected before decoding")

    monkeypatch.setattr(media_artifacts.base64, "b64decode", unexpected_decode)
    with pytest.raises(media_artifacts.ArtifactTooLarge):
        media_artifacts.decode_base64_payload(encoded, max_bytes=4)


@pytest.mark.parametrize("size", [4, 5, 6])
def test_chat_image_save_accepts_exact_decoded_limit(monkeypatch, tmp_path, size):
    monkeypatch.setattr(chat_media, "artifact_dir", lambda *args, **kwargs: tmp_path)
    data = bytes(range(size))
    image = chat_media.save_image_base64(
        context_id="size-boundary",
        data=base64.b64encode(data).decode("ascii"),
        max_bytes=size,
    )
    assert image.size == size
    assert Path(image.path).read_bytes() == data


def test_post_decode_limit_still_checks_actual_payload(monkeypatch):
    monkeypatch.setattr(media_artifacts, "estimated_base64_decoded_size", lambda _: 1)
    with pytest.raises(media_artifacts.ArtifactTooLarge) as exc_info:
        media_artifacts.decode_base64_payload("YWJj", max_bytes=1)
    assert exc_info.value.size == 3
