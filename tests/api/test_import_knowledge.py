"""Tests for python/api/import_knowledge.py — ImportKnowledge API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.import_knowledge import ImportKnowledge


def _make_handler(app=None, lock=None):
    return ImportKnowledge(app=app or MagicMock(), thread_lock=lock or threading.Lock())


def _make_file_storage(filename="doc.txt"):
    storage = MagicMock()
    storage.filename = filename
    storage.save = MagicMock()
    return storage


class TestImportKnowledge:
    @pytest.mark.asyncio
    async def test_process_raises_when_no_files(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.files = {}
        request.form = {"ctxid": "ctx-1"}

        with pytest.raises(Exception, match="No files part"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_raises_when_no_ctxid(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage()
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"ctxid": ""}

        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_returns_filenames_on_success(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()
        mock_ctx.log = MagicMock()
        storage = _make_file_storage("knowledge.pdf")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"ctxid": "ctx-1"}

        knowledge_dir = tmp_path / "knowledge" / "main"
        knowledge_dir.mkdir(parents=True)

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.import_knowledge.files.get_abs_path",
                 return_value=str(knowledge_dir),
             ), \
             patch(
                 "python.api.import_knowledge.memory.get_custom_knowledge_subdir_abs",
                 return_value=str(tmp_path / "knowledge"),
             ), \
             patch(
                 "python.api.import_knowledge.memory.Memory.reload",
                 new_callable=AsyncMock,
             ):
            result = await handler.process({}, request)

        assert result["message"] == "Knowledge Imported"
        assert "filenames" in result
        assert "knowledge.pdf" in result["filenames"]

    @pytest.mark.asyncio
    async def test_process_raises_when_folder_not_writable(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()
        storage = _make_file_storage("x.txt")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"ctxid": "ctx-1"}

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.import_knowledge.memory.get_custom_knowledge_subdir_abs",
                 return_value=str(tmp_path / "knowledge"),
             ), \
             patch(
                 "python.api.import_knowledge.os.makedirs",
             ), \
             patch(
                 "python.api.import_knowledge.os.access",
                 return_value=False,
             ):
            with pytest.raises(Exception, match="not writable"):
                await handler.process({}, request)
