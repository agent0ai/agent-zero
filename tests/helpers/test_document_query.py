"""Tests for python/helpers/document_query.py."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def mock_vector_db():
    """Mock VectorDB with async methods."""
    db = MagicMock()
    db.insert_documents = AsyncMock(return_value=["id1", "id2"])
    db.search_by_metadata = AsyncMock(return_value=[])
    db.search_by_similarity_threshold = AsyncMock(return_value=[])
    db.delete_documents_by_ids = AsyncMock(return_value=[])
    db.db = MagicMock()
    db.db.get_all_docs = MagicMock(return_value={})
    return db


@pytest.fixture
def mock_agent_with_config(mock_agent):
    """Ensure mock_agent has config."""
    mock_agent.config = MagicMock()
    mock_agent.config.chat_model = "openrouter/test-model"
    mock_agent.config.embeddings_model = "openai/text-embedding-3-small"
    return mock_agent


# --- DocumentQueryStore ---


class TestDocumentQueryStoreGet:
    def test_get_raises_when_agent_none(self):
        from python.helpers.document_query import DocumentQueryStore

        with pytest.raises(ValueError, match="Agent and agent config must be provided"):
            DocumentQueryStore.get(None)

    def test_get_raises_when_agent_config_none(self):
        from python.helpers.document_query import DocumentQueryStore

        agent = MagicMock()
        agent.config = None
        with pytest.raises(ValueError, match="Agent and agent config must be provided"):
            DocumentQueryStore.get(agent)

    def test_get_returns_store_instance(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        assert store is not None
        assert store.agent == mock_agent_with_config
        assert store.vector_db is None


class TestDocumentQueryStoreNormalizeUri:
    def test_normalize_file_uri_strips_and_prefixes(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        with patch("python.helpers.document_query.files.fix_dev_path", side_effect=lambda x: x):
            result = store.normalize_uri("file:///path/to/doc.pdf")
            assert result.startswith("file://")
            assert "path" in result or "doc" in result

    def test_normalize_http_to_https(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        result = store.normalize_uri("http://example.com/doc.html")
        assert result == "https://example.com/doc.html"

    def test_normalize_https_unchanged(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        result = store.normalize_uri("https://example.com/doc.html")
        assert result == "https://example.com/doc.html"

    def test_normalize_strips_whitespace(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        with patch("python.helpers.document_query.files.fix_dev_path", side_effect=lambda x: x.strip()):
            result = store.normalize_uri("  file:///x  ")
            assert result == store.normalize_uri("file:///x")


class TestDocumentQueryStoreAddDocument:
    @pytest.mark.asyncio
    async def test_add_document_success(self, mock_agent_with_config, mock_vector_db):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        mock_vector_db.insert_documents.return_value = ["chunk1", "chunk2"]

        with patch.object(store, "delete_document", new_callable=AsyncMock, return_value=True):
            success, ids = await store.add_document("Some text content here.", "file:///doc.txt")
        assert success is True
        assert ids == ["chunk1", "chunk2"]
        mock_vector_db.insert_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_document_empty_text_returns_false(self, mock_agent_with_config, mock_vector_db):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db

        with patch.object(store, "delete_document", new_callable=AsyncMock):
            success, ids = await store.add_document("", "file:///doc.txt")
        assert success is False
        assert ids == []
        mock_vector_db.insert_documents.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_document_exception_returns_false(self, mock_agent_with_config, mock_vector_db):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        mock_vector_db.insert_documents.side_effect = Exception("DB error")

        with patch.object(store, "delete_document", new_callable=AsyncMock):
            success, ids = await store.add_document("Content here", "file:///doc.txt")
        assert success is False
        assert ids == []


class TestDocumentQueryStoreGetDocument:
    @pytest.mark.asyncio
    async def test_get_document_none_when_no_vector_db(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = None
        result = await store.get_document("file:///doc.txt")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_combines_chunks(self, mock_agent_with_config, mock_vector_db):
        from langchain_core.documents import Document
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        chunks = [
            Document(page_content="Part1", metadata={"chunk_index": 0, "total_chunks": 2, "document_uri": "file:///doc"}),
            Document(page_content="Part2", metadata={"chunk_index": 1, "total_chunks": 2, "document_uri": "file:///doc"}),
        ]
        mock_vector_db.search_by_metadata = AsyncMock(return_value=chunks)

        result = await store.get_document("file:///doc")
        assert result is not None
        assert result.page_content == "Part1\nPart2"


class TestDocumentQueryStoreDocumentExists:
    @pytest.mark.asyncio
    async def test_document_exists_false_when_no_vector_db(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = None
        assert await store.document_exists("file:///doc.txt") is False

    @pytest.mark.asyncio
    async def test_document_exists_true_when_chunks_found(self, mock_agent_with_config, mock_vector_db):
        from langchain_core.documents import Document
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        mock_vector_db.search_by_metadata = AsyncMock(
            return_value=[Document(page_content="x", metadata={"document_uri": "file:///doc"})]
        )
        assert await store.document_exists("file:///doc") is True


class TestDocumentQueryStoreDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_document_false_when_no_vector_db(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = None
        assert await store.delete_document("file:///doc.txt") is False

    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_agent_with_config, mock_vector_db):
        from langchain_core.documents import Document
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        chunks = [Document(page_content="x", metadata={"id": "id1", "document_uri": "file:///doc"})]
        mock_vector_db.search_by_metadata = AsyncMock(return_value=chunks)
        mock_vector_db.delete_documents_by_ids = AsyncMock(return_value=chunks)

        result = await store.delete_document("file:///doc")
        assert result is True


class TestDocumentQueryStoreSearchDocuments:
    @pytest.mark.asyncio
    async def test_search_documents_empty_when_no_vector_db(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = None
        result = await store.search_documents("query")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_documents_empty_query_returns_empty(self, mock_agent_with_config, mock_vector_db):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        result = await store.search_documents("")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_documents_returns_results(self, mock_agent_with_config, mock_vector_db):
        from langchain_core.documents import Document
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        docs = [Document(page_content="match", metadata={})]
        mock_vector_db.search_by_similarity_threshold = AsyncMock(return_value=docs)

        result = await store.search_documents("query", limit=5)
        assert result == docs


class TestDocumentQueryStoreListDocuments:
    @pytest.mark.asyncio
    async def test_list_documents_empty_when_no_vector_db(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = None
        result = await store.list_documents()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_documents_returns_sorted_uris(self, mock_agent_with_config, mock_vector_db):
        from python.helpers.document_query import DocumentQueryStore

        store = DocumentQueryStore.get(mock_agent_with_config)
        store.vector_db = mock_vector_db
        mock_doc = MagicMock()
        mock_doc.metadata = {"document_uri": "file:///b"}
        mock_doc2 = MagicMock()
        mock_doc2.metadata = {"document_uri": "file:///a"}
        mock_vector_db.db.get_all_docs.return_value = {"1": mock_doc, "2": mock_doc2}

        result = await store.list_documents()
        assert result == ["file:///a", "file:///b"]


# --- DocumentQueryHelper ---


class TestDocumentQueryHelper:
    def test_initialization(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        helper = DocumentQueryHelper(mock_agent_with_config)
        assert helper.agent == mock_agent_with_config
        assert helper.store is not None
        assert helper.progress_callback is not None

    @pytest.mark.asyncio
    async def test_document_qa_no_chunks_returns_false(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        mock_agent_with_config.handle_intervention = AsyncMock()
        mock_agent_with_config.parse_prompt = MagicMock(return_value="system prompt")
        mock_agent_with_config.call_utility_model = AsyncMock(return_value="optimized query")
        mock_agent_with_config.call_chat_model = AsyncMock(return_value=("reply", None))

        helper = DocumentQueryHelper(mock_agent_with_config)
        helper.store = MagicMock()
        helper.store.normalize_uri = lambda x: x
        helper.store.search_documents = AsyncMock(return_value=[])
        helper.document_get_content = AsyncMock(return_value="content")

        success, content = await helper.document_qa(["file:///doc"], ["question?"])
        assert success is False
        assert "No content found" in content or "!!! No content" in content

    @pytest.mark.asyncio
    async def test_document_get_content_raises_for_compressed_encoding(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        mock_agent_with_config.handle_intervention = AsyncMock()
        helper = DocumentQueryHelper(mock_agent_with_config)
        helper.store = MagicMock()
        helper.store.normalize_uri = lambda x: x
        helper.store.document_exists = AsyncMock(return_value=False)

        with patch("python.helpers.document_query.mimetypes.guess_type", return_value=("text/plain", "gzip")):
            with pytest.raises(ValueError, match="Compressed"):
                await helper.document_get_content("file:///doc.txt", add_to_db=False)

    @pytest.mark.asyncio
    async def test_document_get_content_raises_for_octet_stream(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        mock_agent_with_config.handle_intervention = AsyncMock()
        helper = DocumentQueryHelper(mock_agent_with_config)
        helper.store = MagicMock()
        helper.store.normalize_uri = lambda x: x
        helper.store.document_exists = AsyncMock(return_value=False)

        with patch("python.helpers.document_query.mimetypes.guess_type", return_value=("application/octet-stream", None)):
            with patch("python.helpers.document_query.urlparse") as mock_parse:
                mock_parse.return_value.scheme = "file"
                mock_parse.return_value.path = "/path"
                with patch("python.helpers.document_query.files.fix_dev_path", return_value="/path"):
                    with pytest.raises(ValueError, match="Unsupported document mimetype"):
                        await helper.document_get_content("file:///path/unknown", add_to_db=False)

    @pytest.mark.asyncio
    async def test_handle_text_document_file_scheme(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        helper = DocumentQueryHelper(mock_agent_with_config)
        with patch("python.helpers.document_query.files.read_file_bin", return_value=b"file content"):
            result = helper.handle_text_document("/path/to/file.txt", "file")
        assert result == "file content"

    def test_handle_text_document_unsupported_scheme_raises(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        helper = DocumentQueryHelper(mock_agent_with_config)
        with pytest.raises(ValueError, match="Unsupported scheme"):
            helper.handle_text_document("/path", "ftp")

    @pytest.mark.asyncio
    async def test_handle_html_document_file_scheme(self, mock_agent_with_config):
        from python.helpers.document_query import DocumentQueryHelper

        helper = DocumentQueryHelper(mock_agent_with_config)
        with patch("python.helpers.document_query.files.read_file_bin", return_value=b"<html>body</html>"):
            result = helper.handle_html_document("/path/to/file.html", "file")
        assert "body" in result or "html" in result.lower()
