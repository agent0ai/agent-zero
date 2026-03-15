"""Tests for python/api/image_get.py — ImageGet API handler."""

import io
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.image_get import ImageGet, _send_file_type_icon, _send_fallback_icon


def _make_handler(app=None, lock=None):
    return ImageGet(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestImageGet:
    def test_get_methods_returns_get(self):
        assert ImageGet.get_methods() == ["GET"]

    @pytest.mark.asyncio
    async def test_process_raises_when_no_path(self):
        handler = _make_handler()
        request = MagicMock()
        request.args = {}
        with pytest.raises(ValueError, match="No path provided"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_uses_path_from_input(self):
        handler = _make_handler()
        request = MagicMock()
        request.args = {}
        mock_response = MagicMock()
        mock_response.headers = {}
        with patch("python.api.image_get.runtime.is_development", return_value=False), \
             patch("python.api.image_get.files.exists", return_value=True), \
             patch("python.api.image_get.send_file", return_value=mock_response):
            result = await handler.process({"path": "/some/image.png"}, request)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_process_uses_path_from_request_args(self):
        handler = _make_handler()
        request = MagicMock()
        request.args = {"path": "/img.jpg"}
        mock_response = MagicMock()
        mock_response.headers = {}
        with patch("python.api.image_get.runtime.is_development", return_value=False), \
             patch("python.api.image_get.files.exists", return_value=True), \
             patch("python.api.image_get.send_file", return_value=mock_response):
            result = await handler.process({}, request)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_process_adds_cache_headers_for_image(self):
        handler = _make_handler()
        request = MagicMock()
        request.args = {}
        mock_response = MagicMock()
        mock_response.headers = {}
        with patch("python.api.image_get.runtime.is_development", return_value=False), \
             patch("python.api.image_get.files.exists", return_value=True), \
             patch("python.api.image_get.send_file", return_value=mock_response):
            await handler.process({"path": "/img.png"}, request)
        assert mock_response.headers.get("Cache-Control") == "public, max-age=3600"
        assert mock_response.headers.get("X-File-Type") == "image"

    @pytest.mark.asyncio
    async def test_process_returns_icon_for_non_image_extension(self):
        handler = _make_handler()
        request = MagicMock()
        request.args = {}
        mock_response = MagicMock()
        mock_response.headers = {}
        with patch("python.api.image_get._send_file_type_icon", return_value=mock_response):
            result = await handler.process({"path": "/doc.pdf"}, request)
        assert result == mock_response


class TestSendFileTypeIcon:
    def test_returns_archive_icon_for_zip(self):
        mock_resp = MagicMock()
        mock_resp.headers = {}
        with patch("python.api.image_get._send_fallback_icon", return_value=mock_resp):
            result = _send_file_type_icon(".zip", "file.zip")
        assert result == mock_resp

    def test_returns_document_icon_for_pdf(self):
        mock_resp = MagicMock()
        mock_resp.headers = {}
        with patch("python.api.image_get._send_fallback_icon", return_value=mock_resp):
            result = _send_file_type_icon(".pdf", "doc.pdf")
        assert result == mock_resp

    def test_returns_code_icon_for_py(self):
        mock_resp = MagicMock()
        mock_resp.headers = {}
        with patch("python.api.image_get._send_fallback_icon", return_value=mock_resp):
            result = _send_file_type_icon(".py", "script.py")
        assert result == mock_resp


class TestSendFallbackIcon:
    def test_returns_send_file_response(self, tmp_path):
        icon_path = tmp_path / "file.svg"
        icon_path.write_text("<svg/>")
        with patch("python.api.image_get.files.get_abs_path", return_value=str(icon_path)), \
             patch("python.api.image_get.send_file") as mock_send:
            mock_send.return_value = MagicMock()
            result = _send_fallback_icon("file")
        mock_send.assert_called_once()
        assert "file.svg" in str(mock_send.call_args[0][0])
