"""Tests for python/helpers/attachment_manager.py — AttachmentManager."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.attachment_manager import AttachmentManager


class TestAttachmentManagerAllowedExtensions:
    def test_image_extensions(self):
        am = AttachmentManager("/tmp")
        assert am.is_allowed_file("photo.jpg")
        assert am.is_allowed_file("photo.jpeg")
        assert am.is_allowed_file("photo.png")
        assert am.is_allowed_file("photo.bmp")

    def test_code_extensions(self):
        am = AttachmentManager("/tmp")
        assert am.is_allowed_file("script.py")
        assert am.is_allowed_file("app.js")
        assert am.is_allowed_file("run.sh")

    def test_document_extensions(self):
        am = AttachmentManager("/tmp")
        assert am.is_allowed_file("doc.md")
        assert am.is_allowed_file("doc.pdf")
        assert am.is_allowed_file("doc.txt")
        assert am.is_allowed_file("data.json")

    def test_rejects_unknown_extension(self):
        am = AttachmentManager("/tmp")
        assert am.is_allowed_file("file.xyz") is False


class TestGetFileType:
    def test_returns_image_for_jpg(self):
        am = AttachmentManager("/tmp")
        assert am.get_file_type("x.jpg") == "image"

    def test_returns_code_for_py(self):
        am = AttachmentManager("/tmp")
        assert am.get_file_type("x.py") == "code"

    def test_returns_unknown_for_unknown_ext(self):
        am = AttachmentManager("/tmp")
        assert am.get_file_type("x.xyz") == "unknown"


class TestGetFileExtension:
    def test_returns_lowercase_extension(self):
        assert AttachmentManager.get_file_extension("File.PNG") == "png"

    def test_returns_empty_for_no_extension(self):
        assert AttachmentManager.get_file_extension("noext") == ""

    def test_returns_last_extension(self):
        assert AttachmentManager.get_file_extension("file.tar.gz") == "gz"


class TestValidateMimeType:
    def test_accepts_image_mime(self):
        am = AttachmentManager("/tmp")
        f = MagicMock()
        f.content_type = "image/png"
        assert am.validate_mime_type(f) is True

    def test_accepts_text_mime(self):
        am = AttachmentManager("/tmp")
        f = MagicMock()
        f.content_type = "text/plain"
        assert am.validate_mime_type(f) is True

    def test_rejects_invalid_mime(self):
        am = AttachmentManager("/tmp")
        f = MagicMock()
        f.content_type = "invalid/type"
        assert am.validate_mime_type(f) is False

    def test_handles_missing_content_type(self):
        am = AttachmentManager("/tmp")
        f = MagicMock(spec=[])
        assert am.validate_mime_type(f) is False


class TestSaveFile:
    def test_save_file_returns_path_and_metadata(self, tmp_path):
        am = AttachmentManager(str(tmp_path))
        f = MagicMock()
        f.content_type = "image/png"
        f.save = MagicMock()
        with patch("python.helpers.attachment_manager.safe_filename", return_value="photo.png"):
            with patch.object(am, "generate_image_preview", return_value=None):
                path, meta = am.save_file(f, "photo.png")
        assert path is not None
        assert meta["filename"] == "photo.png"
        assert meta["type"] == "image"
        f.save.assert_called_once()

    def test_save_file_returns_none_on_invalid_filename(self, tmp_path):
        am = AttachmentManager(str(tmp_path))
        f = MagicMock()
        with patch("python.helpers.attachment_manager.safe_filename", return_value=None):
            with patch("python.helpers.attachment_manager.PrintStyle"):
                path, meta = am.save_file(f, "bad/name")
        assert path is None
        assert meta == {}


class TestGenerateImagePreview:
    def test_returns_base64_preview(self, tmp_path):
        from PIL import Image
        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(str(img_path))
        am = AttachmentManager(str(tmp_path))
        result = am.generate_image_preview(str(img_path))
        assert result is not None
        assert isinstance(result, str)
        import base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0
