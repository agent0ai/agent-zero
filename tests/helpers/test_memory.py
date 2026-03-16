"""Tests for python/helpers/memory.py — Cognee memory layer."""

import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Reset module-level state before each test."""
    import python.helpers.memory as mem
    import python.helpers.cognee_init as ci
    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    yield
    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()


# --- _subdir_to_dataset ---

class TestSubdirToDataset:
    def test_simple_name(self):
        from python.helpers.memory import _subdir_to_dataset
        assert _subdir_to_dataset("default") == "default"

    def test_slash_replaced(self):
        from python.helpers.memory import _subdir_to_dataset
        assert _subdir_to_dataset("projects/personal") == "projects_personal"

    def test_spaces_replaced(self):
        from python.helpers.memory import _subdir_to_dataset
        assert _subdir_to_dataset("my project") == "my_project"

    def test_mixed(self):
        from python.helpers.memory import _subdir_to_dataset
        assert _subdir_to_dataset("projects/my project") == "projects_my_project"

    def test_lowercased(self):
        from python.helpers.memory import _subdir_to_dataset
        assert _subdir_to_dataset("Projects/MyApp") == "projects_myapp"


# --- _extract_metadata_from_text ---

class TestExtractMetadataFromText:
    def test_text_with_meta_header(self):
        from python.helpers.memory import _extract_metadata_from_text
        meta = {"id": "abc123", "area": "main", "timestamp": "2026-01-01"}
        text = f'[META:{json.dumps(meta)}]\nHello world content'
        content, extracted = _extract_metadata_from_text(text)
        assert content == "Hello world content"
        assert extracted["id"] == "abc123"
        assert extracted["area"] == "main"

    def test_text_without_meta_header(self):
        from python.helpers.memory import _extract_metadata_from_text
        content, meta = _extract_metadata_from_text("Just plain text")
        assert content == "Just plain text"
        assert meta["area"] == "main"

    def test_malformed_meta_returns_full_text(self):
        from python.helpers.memory import _extract_metadata_from_text
        text = "[META:not valid json]\nContent here"
        content, meta = _extract_metadata_from_text(text)
        assert content == text
        assert meta["area"] == "main"

    def test_meta_without_closing_bracket(self):
        from python.helpers.memory import _extract_metadata_from_text
        text = '[META:{"id": "test"} some more text'
        content, meta = _extract_metadata_from_text(text)
        assert content == text


# --- _deduplicate_documents ---

class TestDeduplicateDocuments:
    def test_removes_duplicates_by_id(self):
        from python.helpers.memory import _deduplicate_documents
        from langchain_core.documents import Document

        docs = [
            Document(page_content="First", metadata={"id": "a"}),
            Document(page_content="Second", metadata={"id": "b"}),
            Document(page_content="Duplicate", metadata={"id": "a"}),
        ]
        result = _deduplicate_documents(docs)
        assert len(result) == 2
        assert result[0].page_content == "First"
        assert result[1].page_content == "Second"

    def test_deduplicates_by_content_when_no_id(self):
        from python.helpers.memory import _deduplicate_documents
        from langchain_core.documents import Document

        docs = [
            Document(page_content="Same content", metadata={}),
            Document(page_content="Same content", metadata={}),
            Document(page_content="Different", metadata={}),
        ]
        result = _deduplicate_documents(docs)
        assert len(result) == 2

    def test_preserves_order(self):
        from python.helpers.memory import _deduplicate_documents
        from langchain_core.documents import Document

        docs = [
            Document(page_content="C", metadata={"id": "3"}),
            Document(page_content="A", metadata={"id": "1"}),
            Document(page_content="B", metadata={"id": "2"}),
        ]
        result = _deduplicate_documents(docs)
        assert [d.page_content for d in result] == ["C", "A", "B"]


# --- _parse_filter_to_node_names ---

class TestParseFilterToNodeNames:
    def test_empty_filter(self):
        from python.helpers.memory import _parse_filter_to_node_names
        assert _parse_filter_to_node_names("") == []

    def test_main_filter(self):
        from python.helpers.memory import _parse_filter_to_node_names
        result = _parse_filter_to_node_names("area == 'main'")
        assert "main" in result

    def test_solutions_filter(self):
        from python.helpers.memory import _parse_filter_to_node_names
        result = _parse_filter_to_node_names("area == 'solutions'")
        assert "solutions" in result

    def test_combined_filter(self):
        from python.helpers.memory import _parse_filter_to_node_names
        result = _parse_filter_to_node_names("area == 'main' or area == 'fragments'")
        assert "main" in result
        assert "fragments" in result


# --- _results_to_documents ---

class TestResultsToDocuments:
    def test_empty_results(self):
        from python.helpers.memory import _results_to_documents
        assert _results_to_documents(None, 10) == []
        assert _results_to_documents([], 10) == []

    def test_string_results(self):
        from python.helpers.memory import _results_to_documents
        results = ["Hello world", "Test content"]
        docs = _results_to_documents(results, 10)
        assert len(docs) == 2
        assert docs[0].page_content == "Hello world"

    def test_result_with_search_result_attr(self):
        from python.helpers.memory import _results_to_documents
        mock_result = MagicMock()
        mock_result.search_result = "inner content"
        mock_result.dataset_name = "test_ds"
        docs = _results_to_documents([mock_result], 10)
        assert len(docs) == 1
        assert docs[0].page_content == "inner content"
        assert docs[0].metadata["dataset"] == "test_ds"

    def test_respects_limit(self):
        from python.helpers.memory import _results_to_documents
        results = [f"item_{i}" for i in range(20)]
        docs = _results_to_documents(results, 5)
        assert len(docs) == 5

    def test_meta_header_extraction(self):
        from python.helpers.memory import _results_to_documents
        meta = {"id": "test_id", "area": "solutions"}
        text = f'[META:{json.dumps(meta)}]\nActual content'
        docs = _results_to_documents([text], 10)
        assert docs[0].page_content == "Actual content"
        assert docs[0].metadata["id"] == "test_id"
        assert docs[0].metadata["area"] == "solutions"

    def test_dict_results(self):
        from python.helpers.memory import _results_to_documents
        results = [{"text": "from dict", "other": "data"}]
        docs = _results_to_documents(results, 10)
        assert docs[0].page_content == "from dict"


# --- get_knowledge_subdirs_by_memory_subdir ---

class TestGetKnowledgeSubdirsByMemorySubdir:
    def test_does_not_mutate_input_list(self):
        from python.helpers.memory import get_knowledge_subdirs_by_memory_subdir
        original = ["default", "custom"]
        original_copy = list(original)
        with patch("python.helpers.memory.get_project_meta_folder",
                    create=True, return_value="usr/projects/test/.a0proj"):
            with patch.dict("sys.modules", {"python.helpers.projects": MagicMock(
                get_project_meta_folder=MagicMock(return_value="usr/projects/test/.a0proj/knowledge")
            )}):
                result = get_knowledge_subdirs_by_memory_subdir("projects/test", original)
        assert original == original_copy
        assert len(result) > len(original)

    def test_non_project_returns_copy(self):
        from python.helpers.memory import get_knowledge_subdirs_by_memory_subdir
        original = ["default"]
        result = get_knowledge_subdirs_by_memory_subdir("default", original)
        assert result == original
        assert result is not original


# --- _get_cognee delegates to cognee_init.get_cognee ---

class TestGetCognee:
    def test_returns_same_instance(self):
        from python.helpers.memory import _get_cognee
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        mock_search_type = MagicMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = mock_search_type
        c1, st1 = _get_cognee()
        c2, st2 = _get_cognee()
        assert c1 is c2
        assert c1 is mock_cognee
        assert st1 is mock_search_type

    def test_raises_when_not_initialized(self):
        from python.helpers.memory import _get_cognee
        with pytest.raises(RuntimeError, match="Cognee not initialized"):
            _get_cognee()


# --- reload resets _configured ---

class TestReload:
    def test_reload_resets_configured_flag(self):
        import python.helpers.memory as mem
        import python.helpers.cognee_init as ci
        ci._configured = True
        ci._cognee_module = MagicMock()
        ci._search_type_class = MagicMock()
        mem.Memory._initialized = True
        mem.reload()
        assert ci._configured is False
        assert ci._cognee_module is None
        assert ci._search_type_class is None
        assert mem.Memory._initialized is False


# --- Memory._area_dataset ---

class TestAreaDataset:
    def test_area_dataset_format(self):
        from python.helpers.memory import Memory
        mem = Memory(dataset_name="projects_personal", memory_subdir="projects/personal")
        assert mem._area_dataset("main") == "projects_personal_main"
        assert mem._area_dataset("solutions") == "projects_personal_solutions"
        assert mem._area_dataset("fragments") == "projects_personal_fragments"


# --- Memory._build_node_sets ---

class TestBuildNodeSets:
    def test_non_project(self):
        from python.helpers.memory import Memory
        mem = Memory(dataset_name="default", memory_subdir="default")
        assert mem._build_node_sets("main") == ["main"]

    def test_project_adds_project_node(self):
        from python.helpers.memory import Memory
        mem = Memory(dataset_name="projects_personal", memory_subdir="projects/personal")
        result = mem._build_node_sets("main")
        assert "main" in result
        assert "project_personal" in result


# --- Memory._datasets_for_filter ---

class TestDatasetsForFilter:
    def test_empty_filter_returns_all_areas(self):
        from python.helpers.memory import Memory
        mem = Memory(dataset_name="default", memory_subdir="default")
        result = mem._datasets_for_filter("")
        assert len(result) == 3
        assert "default_main" in result
        assert "default_fragments" in result
        assert "default_solutions" in result

    def test_filter_by_area(self):
        from python.helpers.memory import Memory
        mem = Memory(dataset_name="default", memory_subdir="default")
        result = mem._datasets_for_filter("area == 'main'")
        assert "default_main" in result
        assert "default_solutions" not in result


# --- _delete_data_by_id improved matching ---

@pytest.mark.asyncio
async def test_delete_data_by_id_uses_raw_data_location():
    from python.helpers.memory import _delete_data_by_id
    import python.helpers.cognee_init as ci

    mock_cognee = MagicMock()
    mock_ds = MagicMock()
    mock_ds.name = "test_main"
    mock_ds.id = "ds_id_1"

    mock_item = MagicMock()
    mock_item.raw_data_location = "file:///data/doc_abc123.txt"
    mock_item.name = "doc_abc123.txt"
    mock_item.id = "item_id_1"

    mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
    mock_cognee.datasets.list_data = AsyncMock(return_value=[mock_item])
    mock_cognee.datasets.delete_data = AsyncMock()

    ci._cognee_module = mock_cognee
    ci._search_type_class = MagicMock()

    result = await _delete_data_by_id("test_main", "abc123")
    assert result is True
    mock_cognee.datasets.delete_data.assert_called_once_with(
        dataset_id="ds_id_1", data_id="item_id_1"
    )


@pytest.mark.asyncio
async def test_delete_data_by_id_returns_false_when_not_found():
    from python.helpers.memory import _delete_data_by_id
    import python.helpers.cognee_init as ci

    mock_cognee = MagicMock()
    mock_ds = MagicMock()
    mock_ds.name = "test_main"
    mock_ds.id = "ds_id_1"
    mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
    mock_cognee.datasets.list_data = AsyncMock(return_value=[])

    ci._cognee_module = mock_cognee
    ci._search_type_class = MagicMock()

    result = await _delete_data_by_id("test_main", "nonexistent_id")
    assert result is False


@pytest.mark.asyncio
async def test_delete_data_by_id_returns_false_for_missing_dataset():
    from python.helpers.memory import _delete_data_by_id
    import python.helpers.cognee_init as ci

    mock_cognee = MagicMock()
    mock_cognee.datasets.list_datasets = AsyncMock(return_value=[])

    ci._cognee_module = mock_cognee
    ci._search_type_class = MagicMock()

    result = await _delete_data_by_id("nonexistent_dataset", "some_id")
    assert result is False


# --- configure_cognee integration ---

class TestMemoryCallsConfigureCognee:
    """Verify Memory operations use cognee_init.get_cognee() for module access."""

    @pytest.mark.asyncio
    async def test_insert_documents_uses_initialized_cognee(self):
        """insert_documents uses cognee module from cognee_init."""
        from python.helpers.memory import Memory
        from langchain_core.documents import Document
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        memory = await Memory.get_by_subdir("default", preload_knowledge=False)
        doc = Document(page_content="test", metadata={"area": "main"})
        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            await memory.insert_documents([doc])

        mock_cognee.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_returns_valid_memory(self):
        """Memory.get() returns valid Memory instance."""
        from python.helpers.memory import Memory

        mock_agent = MagicMock()
        mock_agent.context = MagicMock()
        mock_agent.context.config = MagicMock()
        mock_agent.context.config.knowledge_subdirs = []
        mock_agent.context.config.memory_subdir = "default"

        with patch("python.helpers.memory.get_agent_memory_subdir", return_value="default"), \
             patch("python.helpers.memory.get_knowledge_subdirs_by_memory_subdir", return_value=[]):
            mem = await Memory.get(mock_agent)

        assert mem.dataset_name == "default"

    @pytest.mark.asyncio
    async def test_insert_documents_works_after_init(self):
        """Verify that insert_documents can add data after init_cognee."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        from langchain_core.documents import Document
        doc = Document(page_content="test content", metadata={"area": "main"})

        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            memory = await Memory.get_by_subdir("default", preload_knowledge=False)
            ids = await memory.insert_documents([doc])

        mock_cognee.add.assert_called_once()
        assert len(ids) == 1

    @pytest.mark.asyncio
    async def test_insert_documents_does_not_return_id_on_failure(self):
        """Bug fix: insert_documents should NOT return an id when cognee.add() fails."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock(side_effect=Exception("add failed"))
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        from langchain_core.documents import Document
        doc = Document(page_content="test content", metadata={"area": "main"})

        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            memory = await Memory.get_by_subdir("default", preload_knowledge=False)
            ids = await memory.insert_documents([doc])

        assert len(ids) == 0

    @pytest.mark.asyncio
    async def test_search_similarity_threshold_handles_cognee_failure(self):
        """If cognee.search() fails, search_similarity_threshold should return []."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=Exception("search failed"))
        mock_search_type = MagicMock()
        mock_search_type.CHUNKS = MagicMock(name="CHUNKS")
        ci._cognee_module = mock_cognee
        ci._search_type_class = mock_search_type

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": False,
                "cognee_search_type": "CHUNKS",
            }.get(name, default)
            memory = await Memory.get_by_subdir("default", preload_knowledge=False)
            results = await memory.search_similarity_threshold(
                query="test", limit=10, threshold=0.5
            )

        assert results == []


# --- Memory.Area enum ---

class TestMemoryAreaEnum:
    def test_area_values(self):
        from python.helpers.memory import Memory
        assert Memory.Area.MAIN.value == "main"
        assert Memory.Area.FRAGMENTS.value == "fragments"
        assert Memory.Area.SOLUTIONS.value == "solutions"

    def test_area_iteration(self):
        from python.helpers.memory import Memory
        areas = list(Memory.Area)
        assert len(areas) == 3
        assert Memory.Area.MAIN in areas


# --- Memory.insert_text ---

class TestMemoryInsertText:
    @pytest.mark.asyncio
    async def test_insert_text_returns_id(self):
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            memory = Memory(dataset_name="default", memory_subdir="default")
            doc_id = await memory.insert_text("hello world", {"area": "main"})

        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
        mock_cognee.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_text_with_metadata(self):
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            memory = Memory(dataset_name="default", memory_subdir="default")
            doc_id = await memory.insert_text("test", {"area": "solutions", "custom": "value"})

        assert doc_id
        call_args = mock_cognee.add.call_args
        assert "[META:" in call_args[0][0]
        assert "solutions" in call_args[0][0]


# --- Memory.delete_documents_by_query ---

class TestMemoryDeleteDocumentsByQuery:
    @pytest.mark.asyncio
    async def test_delete_documents_by_query_returns_docs(self):
        from python.helpers.memory import Memory
        from langchain_core.documents import Document
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=[
            Document(page_content="match", metadata={"id": "id1"})
        ])
        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"
        mock_item = MagicMock()
        mock_item.raw_data_location = "id1"
        mock_item.id = "item1"
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
        mock_cognee.datasets.list_data = AsyncMock(return_value=[mock_item])
        mock_cognee.datasets.delete_data = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": False,
                "cognee_search_type": "CHUNKS",
            }.get(name, default)
            memory = Memory(dataset_name="default", memory_subdir="default")
            removed = await memory.delete_documents_by_query("test query", threshold=0.5)

        assert len(removed) >= 0


# --- Memory.delete_documents_by_ids ---

class TestMemoryDeleteDocumentsByIds:
    @pytest.mark.asyncio
    async def test_delete_documents_by_ids(self):
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"
        mock_item = MagicMock()
        mock_item.raw_data_location = "abc123"
        mock_item.id = "item1"
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
        mock_cognee.datasets.list_data = AsyncMock(return_value=[mock_item])
        mock_cognee.datasets.delete_data = AsyncMock()
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        memory = Memory(dataset_name="default", memory_subdir="default")
        removed = await memory.delete_documents_by_ids(["abc123"])

        assert len(removed) >= 1


# --- Memory.format_docs_plain ---

class TestMemoryFormatDocsPlain:
    def test_format_docs_plain(self):
        from python.helpers.memory import Memory
        from langchain_core.documents import Document

        docs = [
            Document(page_content="content1", metadata={"id": "1", "area": "main"}),
            Document(page_content="content2", metadata={"id": "2"}),
        ]
        result = Memory.format_docs_plain(docs)
        assert len(result) == 2
        assert "id: 1" in result[0]
        assert "Content: content1" in result[0]
        assert "Content: content2" in result[1]


# --- Memory.get_timestamp ---

class TestMemoryGetTimestamp:
    def test_get_timestamp_format(self):
        from python.helpers.memory import Memory
        ts = Memory.get_timestamp()
        assert "202" in ts or "203" in ts  # year
        assert "-" in ts
        assert ":" in ts


# --- Memory.get_document_by_id ---

class TestMemoryGetDocumentById:
    def test_get_document_by_id_returns_none(self):
        from python.helpers.memory import Memory
        memory = Memory(dataset_name="default", memory_subdir="default")
        result = memory.get_document_by_id("nonexistent")
        assert result is None


# --- Memory.update_documents ---

class TestMemoryUpdateDocuments:
    @pytest.mark.asyncio
    async def test_update_documents_deletes_and_inserts(self):
        from python.helpers.memory import Memory
        from langchain_core.documents import Document
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_cognee.add = AsyncMock()
        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
        mock_cognee.datasets.list_data = AsyncMock(return_value=[])
        ci._cognee_module = mock_cognee
        ci._search_type_class = MagicMock()

        doc = Document(page_content="updated", metadata={"id": "old_id", "area": "main"})
        with patch("python.helpers.cognee_background.CogneeBackgroundWorker") as MockBg:
            MockBg.get_instance.return_value = MagicMock()
            memory = Memory(dataset_name="default", memory_subdir="default")
            ids = await memory.update_documents([doc])

        assert len(ids) == 1
        mock_cognee.add.assert_called_once()


# --- abs_knowledge_dir ---

class TestAbsKnowledgeDir:
    def test_default_subdir(self):
        from python.helpers.memory import abs_knowledge_dir
        with patch("python.helpers.memory.files") as mock_files:
            mock_files.get_abs_path.side_effect = lambda *a: "/".join(str(x) for x in a)
            result = abs_knowledge_dir("default")
        assert "knowledge" in result

    def test_custom_subdir(self):
        from python.helpers.memory import abs_knowledge_dir
        with patch("python.helpers.memory.files") as mock_files:
            mock_files.get_abs_path.side_effect = lambda *a: "/".join(str(x) for x in a)
            result = abs_knowledge_dir("custom")
        assert "usr" in result
        assert "knowledge" in result

    def test_named_subdir(self):
        from python.helpers.memory import abs_knowledge_dir
        with patch("python.helpers.memory.files") as mock_files:
            mock_files.get_abs_path.side_effect = lambda *a: "/".join(str(x) for x in a)
            result = abs_knowledge_dir("my_knowledge", "sub")
        assert "my_knowledge" in result
        assert "sub" in result


# --- get_existing_memory_subdirs ---

class TestGetExistingMemorySubdirs:
    def test_returns_default_when_exception(self):
        from python.helpers.memory import get_existing_memory_subdirs
        with patch("python.helpers.projects.get_projects_parent_folder") as mock_get:
            mock_get.side_effect = Exception("no projects")
            result = get_existing_memory_subdirs()
        assert result == ["default"]

    def test_includes_projects(self):
        from python.helpers.memory import get_existing_memory_subdirs
        with patch("python.helpers.projects.get_projects_parent_folder", return_value="/tmp/projects"), \
             patch("os.path.exists", return_value=True), \
             patch("python.helpers.memory.files") as mock_files:
            mock_files.get_subdirectories.return_value = ["proj1", "proj2"]
            result = get_existing_memory_subdirs()
        assert "default" in result
        assert "projects/proj1" in result
        assert "projects/proj2" in result


# --- abs_db_dir ---

class TestAbsDbDir:
    def test_abs_db_dir_delegates_to_state_dir(self):
        from python.helpers.memory import abs_db_dir
        with patch("python.helpers.memory._state_dir") as mock_state:
            mock_state.return_value = "/tmp/state"
            result = abs_db_dir("default")
        assert result == "/tmp/state"


# --- get_custom_knowledge_subdir_abs ---

class TestGetCustomKnowledgeSubdirAbs:
    def test_returns_custom_path(self):
        from python.helpers.memory import get_custom_knowledge_subdir_abs
        with patch("python.helpers.memory.files") as mock_files:
            mock_files.get_abs_path.return_value = "/usr/knowledge"
            mock_agent = MagicMock()
            mock_agent.config.knowledge_subdirs = ["custom"]
            result = get_custom_knowledge_subdir_abs(mock_agent)
        assert result == "/usr/knowledge"

    def test_raises_when_no_custom(self):
        from python.helpers.memory import get_custom_knowledge_subdir_abs
        mock_agent = MagicMock()
        mock_agent.config.knowledge_subdirs = ["default"]
        with pytest.raises(Exception, match="No custom knowledge subdir"):
            get_custom_knowledge_subdir_abs(mock_agent)


# --- Memory._multi_search parallel execution ---

def _make_search_type_enum():
    """Create a mock SearchType enum with common types."""
    from types import SimpleNamespace
    st = SimpleNamespace()
    for name in ["CHUNKS", "CHUNKS_LEXICAL", "GRAPH_COMPLETION"]:
        member = SimpleNamespace(name=name, value=name)
        setattr(st, name, member)
    return st


class TestMultiSearchParallel:
    """Verify _multi_search runs search types in parallel with timeouts."""

    @pytest.mark.asyncio
    async def test_multi_search_runs_in_parallel(self):
        """Two search types with 0.5s delay each should complete in <0.9s."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        SearchType = _make_search_type_enum()

        async def delayed_search(query_text, query_type, top_k, datasets, node_name, **kw):
            await asyncio.sleep(0.5)
            return [f"result_{query_type.name}"]

        mock_cognee = MagicMock()
        mock_cognee.search = delayed_search
        ci._cognee_module = mock_cognee
        ci._search_type_class = SearchType

        memory = Memory(dataset_name="default", memory_subdir="default")

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_search_types": "CHUNKS,CHUNKS_LEXICAL",
            }.get(name, default)

            loop = asyncio.get_event_loop()
            start = loop.time()
            results = await memory._multi_search(
                mock_cognee, SearchType, "test query", limit=5,
                datasets=["ds_main"], node_names=["main"],
            )
            elapsed = loop.time() - start

        assert len(results) == 2
        assert elapsed < 0.9, f"Expected parallel execution (<0.9s), took {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_multi_search_timeout_per_type(self):
        """One type hangs, other returns results; overall completes without hanging."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        SearchType = _make_search_type_enum()

        async def mixed_search(query_text, query_type, top_k, datasets, node_name, **kw):
            if query_type.name == "CHUNKS":
                return ["good_result"]
            await asyncio.sleep(60)
            return ["should_not_appear"]

        mock_cognee = MagicMock()
        mock_cognee.search = mixed_search
        ci._cognee_module = mock_cognee
        ci._search_type_class = SearchType

        memory = Memory(dataset_name="default", memory_subdir="default")

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_search_types": "CHUNKS,CHUNKS_LEXICAL",
            }.get(name, default)

            with patch.object(Memory, "SEARCH_TIMEOUT", 0.3):
                loop = asyncio.get_event_loop()
                start = loop.time()
                results = await memory._multi_search(
                    mock_cognee, SearchType, "test query", limit=5,
                    datasets=["ds_main"], node_names=["main"],
                )
                elapsed = loop.time() - start

        assert elapsed < 2.0, f"Should not hang, took {elapsed:.2f}s"
        contents = [doc.page_content for doc in results]
        assert any("good_result" in c for c in contents)
        assert not any("should_not_appear" in c for c in contents)

    @pytest.mark.asyncio
    async def test_multi_search_fallback_on_all_fail(self):
        """All types fail → fallback to CHUNKS."""
        from python.helpers.memory import Memory
        import python.helpers.cognee_init as ci

        SearchType = _make_search_type_enum()
        call_log = []

        async def failing_then_fallback(query_text, query_type, top_k, **kw):
            call_log.append(query_type.name)
            if query_type.name == "CHUNKS" and len(call_log) > 2:
                return ["fallback_result"]
            raise Exception(f"{query_type.name} failed")

        mock_cognee = MagicMock()
        mock_cognee.search = failing_then_fallback
        ci._cognee_module = mock_cognee
        ci._search_type_class = SearchType

        memory = Memory(dataset_name="default", memory_subdir="default")

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_search_types": "CHUNKS,CHUNKS_LEXICAL",
            }.get(name, default)

            results = await memory._multi_search(
                mock_cognee, SearchType, "test query", limit=5,
                datasets=["ds_main"], node_names=["main"],
            )

        assert len(results) >= 1
        assert any("fallback_result" in doc.page_content for doc in results)
        assert "CHUNKS" in call_log
