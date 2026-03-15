"""Tests for python/helpers/memory.py — Cognee memory layer."""

import sys
import json
import asyncio
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Reset module-level state before each test."""
    import python.helpers.memory as mem
    import python.helpers.cognee_init as ci
    mem._cognee = None
    mem._SearchType = None
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False
    yield
    mem._cognee = None
    mem._SearchType = None
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False


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


# --- _get_cognee thread safety ---

class TestGetCogneeThreadSafety:
    def test_returns_same_instance(self):
        from python.helpers.memory import _get_cognee
        mock_cognee = MagicMock()
        mock_search_type = MagicMock()
        with patch("python.helpers.memory.configure_cognee"), \
             patch.dict("sys.modules", {
                 "cognee": mock_cognee,
             }):
            mock_cognee.SearchType = mock_search_type
            c1, st1 = _get_cognee()
            c2, st2 = _get_cognee()
        assert c1 is c2

    def test_concurrent_calls_safe(self):
        from python.helpers.memory import _get_cognee
        import python.helpers.memory as mem

        call_count = 0

        def mock_configure():
            nonlocal call_count
            call_count += 1

        mock_cognee_mod = MagicMock()
        mock_cognee_mod.SearchType = MagicMock()

        errors = []

        def worker():
            try:
                with patch("python.helpers.memory.configure_cognee", side_effect=mock_configure), \
                     patch.dict("sys.modules", {"cognee": mock_cognee_mod}):
                    _get_cognee()
            except Exception as e:
                errors.append(e)

        mem._cognee = None
        mem._SearchType = None

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


# --- reload resets _configured ---

class TestReload:
    def test_reload_resets_configured_flag(self):
        import python.helpers.memory as mem
        import python.helpers.cognee_init as ci
        ci._configured = True
        mem.Memory._initialized = True
        mem.reload()
        assert ci._configured is False
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
    import python.helpers.memory as mem

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

    mem._cognee = mock_cognee
    mem._SearchType = MagicMock()

    result = await _delete_data_by_id("test_main", "abc123")
    assert result is True
    mock_cognee.datasets.delete_data.assert_called_once_with(
        dataset_id="ds_id_1", data_id="item_id_1"
    )


@pytest.mark.asyncio
async def test_delete_data_by_id_returns_false_when_not_found():
    from python.helpers.memory import _delete_data_by_id
    import python.helpers.memory as mem

    mock_cognee = MagicMock()
    mock_ds = MagicMock()
    mock_ds.name = "test_main"
    mock_ds.id = "ds_id_1"
    mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
    mock_cognee.datasets.list_data = AsyncMock(return_value=[])

    mem._cognee = mock_cognee
    mem._SearchType = MagicMock()

    result = await _delete_data_by_id("test_main", "nonexistent_id")
    assert result is False


@pytest.mark.asyncio
async def test_delete_data_by_id_returns_false_for_missing_dataset():
    from python.helpers.memory import _delete_data_by_id
    import python.helpers.memory as mem

    mock_cognee = MagicMock()
    mock_cognee.datasets.list_datasets = AsyncMock(return_value=[])

    mem._cognee = mock_cognee
    mem._SearchType = MagicMock()

    result = await _delete_data_by_id("nonexistent_dataset", "some_id")
    assert result is False
