"""Tests for python/helpers/images.py — compress_image."""

import sys
from pathlib import Path
from unittest.mock import patch
import io

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

from python.helpers.images import compress_image


class TestCompressImage:
    def test_compress_reduces_size_for_large_image(self):
        img = Image.new("RGB", (800, 600), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()
        compressed = compress_image(raw, max_pixels=256_000, quality=50)
        assert len(compressed) < len(raw)
        assert isinstance(compressed, bytes)

    def test_compress_output_is_jpeg(self):
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()
        compressed = compress_image(raw, max_pixels=256_000, quality=50)
        assert compressed[:2] == b"\xff\xd8"

    def test_compress_small_image_still_works(self):
        img = Image.new("RGB", (50, 50), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()
        compressed = compress_image(raw, max_pixels=256_000, quality=50)
        assert len(compressed) > 0

    def test_compress_handles_rgba(self):
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()
        compressed = compress_image(raw, max_pixels=256_000, quality=50)
        assert len(compressed) > 0

    def test_compress_respects_max_pixels(self):
        img = Image.new("RGB", (1000, 1000), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()
        compressed = compress_image(raw, max_pixels=10_000, quality=80)
        out_img = Image.open(io.BytesIO(compressed))
        assert out_img.width * out_img.height <= 10_000 + 1000
