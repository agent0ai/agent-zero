"""Tests for python/helpers/vector_db.py — VectorDB, format_docs_plain, get_comparator."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document

from python.helpers.vector_db import (
    VectorDB,
    format_docs_plain,
    get_comparator,
)


@pytest.fixture
def mock_agent():
    return MagicMock()


class TestVectorDB:
    def test_init_sets_dataset_name(self, mock_agent):
        db = VectorDB(mock_agent, cache=True)
        assert db._dataset_name.startswith("docquery_")
        assert "docquery_" in db._dataset_name

    def test_get_all_docs_returns_empty_initially(self, mock_agent):
        db = VectorDB(mock_agent)
        assert db.get_all_docs() == {}

    @pytest.mark.asyncio
    async def test_search_by_metadata_with_comparator(self, mock_agent):
        db = VectorDB(mock_agent)
        db._docs["a"] = Document(page_content="x", metadata={"type": "code"})
        db._docs["b"] = Document(page_content="y", metadata={"type": "doc"})
        result = await db.search_by_metadata("type == 'code'", limit=0)
        assert len(result) == 1
        assert result[0].metadata["type"] == "code"

    @pytest.mark.asyncio
    async def test_search_by_metadata_respects_limit(self, mock_agent):
        db = VectorDB(mock_agent)
        for i in range(5):
            db._docs[f"d{i}"] = Document(page_content="x", metadata={"n": i})
        result = await db.search_by_metadata("True", limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_insert_documents_adds_to_docs(self, mock_agent):
        db = VectorDB(mock_agent)
        docs = [Document(page_content="hello", metadata={})]
        with patch("python.helpers.vector_db.configure_cognee"):
            with patch("python.helpers.vector_db._get_cognee") as m:
                cognee = MagicMock()
                cognee.add = AsyncMock()
                m.return_value = (cognee, MagicMock())
                ids = await db.insert_documents(docs)
        assert len(ids) == 1
        assert ids[0] in db._docs
        assert db._docs[ids[0]].page_content == "hello"

    @pytest.mark.asyncio
    async def test_delete_documents_by_ids(self, mock_agent):
        db = VectorDB(mock_agent)
        db._docs["id1"] = Document(page_content="a", metadata={})
        db._docs["id2"] = Document(page_content="b", metadata={})
        rem = await db.delete_documents_by_ids(["id1", "id3"])
        assert len(rem) == 1
        assert rem[0].page_content == "a"
        assert "id1" not in db._docs
        assert "id2" in db._docs


class TestFormatDocsPlain:
    def test_formats_doc_with_metadata(self):
        doc = Document(page_content="body", metadata={"title": "T", "author": "A"})
        result = format_docs_plain([doc])
        assert len(result) == 1
        assert "title: T" in result[0]
        assert "author: A" in result[0]
        assert "Content: body" in result[0]

    def test_empty_list_returns_empty(self):
        assert format_docs_plain([]) == []


class TestGetComparator:
    def test_comparator_true_condition(self):
        comp = get_comparator("x > 5")
        assert comp({"x": 10}) is True
        assert comp({"x": 3}) is False

    def test_comparator_string_condition(self):
        comp = get_comparator("kind == 'image'")
        assert comp({"kind": "image"}) is True
        assert comp({"kind": "text"}) is False

    def test_comparator_invalid_returns_false(self):
        comp = get_comparator("undefined_var == 1")
        assert comp({}) is False
