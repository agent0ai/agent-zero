"""Tests for _50_recall_memories.py — Two-phase search, timeouts, system_prompt."""

import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.extensions.message_loop_prompts_after._50_recall_memories import (
    _resolve_search_types,
    _extract_texts,
    _multi_cognee_search,
    _write_extras,
    PER_SEARCH_TIMEOUT,
)


def _make_search_type_enum():
    """Create a mock SearchType enum with common types."""
    st = SimpleNamespace()
    for name in [
        "CHUNKS", "CHUNKS_LEXICAL", "GRAPH_COMPLETION", "RAG_COMPLETION",
        "TRIPLET_COMPLETION", "GRAPH_SUMMARY_COMPLETION", "TEMPORAL",
        "FEELING_LUCKY", "NATURAL_LANGUAGE",
        "GRAPH_COMPLETION_COT", "GRAPH_COMPLETION_CONTEXT_EXTENSION",
    ]:
        member = SimpleNamespace(name=name, value=name)
        setattr(st, name, member)
    return st


# --- _resolve_search_types ---

class TestResolveSearchTypes:
    def test_default_multi_search_splits_fast_slow(self):
        SearchType = _make_search_type_enum()
        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.get_cognee_setting"
        ) as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": True,
                "cognee_search_types": "GRAPH_COMPLETION,CHUNKS_LEXICAL",
            }.get(name, default)
            fast, slow = _resolve_search_types(SearchType)

        fast_names = {t.name for t in fast}
        slow_names = {t.name for t in slow}
        assert "CHUNKS_LEXICAL" in fast_names
        assert "GRAPH_COMPLETION" in slow_names
        assert "CHUNKS_LEXICAL" not in slow_names

    def test_all_slow_types_get_chunks_as_fast_fallback(self):
        SearchType = _make_search_type_enum()
        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.get_cognee_setting"
        ) as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": True,
                "cognee_search_types": "GRAPH_COMPLETION,RAG_COMPLETION",
            }.get(name, default)
            fast, slow = _resolve_search_types(SearchType)

        assert len(fast) == 1
        assert fast[0].name == "CHUNKS"
        assert len(slow) == 2

    def test_single_search_mode(self):
        SearchType = _make_search_type_enum()
        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.get_cognee_setting"
        ) as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": False,
                "cognee_search_type": "CHUNKS",
            }.get(name, default)
            fast, slow = _resolve_search_types(SearchType)

        assert len(fast) == 1
        assert fast[0].name == "CHUNKS"
        assert len(slow) == 0

    def test_invalid_type_falls_back_to_chunks(self):
        SearchType = _make_search_type_enum()
        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.get_cognee_setting"
        ) as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": False,
                "cognee_search_type": "NONEXISTENT_TYPE",
            }.get(name, default)
            fast, slow = _resolve_search_types(SearchType)

        assert len(fast) == 1
        assert fast[0].name == "CHUNKS"

    def test_temporal_is_slow(self):
        SearchType = _make_search_type_enum()
        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.get_cognee_setting"
        ) as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": True,
                "cognee_search_types": "CHUNKS,TEMPORAL",
            }.get(name, default)
            fast, slow = _resolve_search_types(SearchType)

        assert any(t.name == "CHUNKS" for t in fast)
        assert any(t.name == "TEMPORAL" for t in slow)


# --- _extract_texts ---

class TestExtractTexts:
    def test_empty_results(self):
        assert _extract_texts(None, 10) == []
        assert _extract_texts([], 10) == []

    def test_string_results(self):
        results = ["Hello", "World"]
        texts = _extract_texts(results, 10)
        assert texts == ["Hello", "World"]

    def test_strips_meta_header(self):
        meta_text = '[META:{"id": "abc"}]\nActual content'
        texts = _extract_texts([meta_text], 10)
        assert texts == ["Actual content"]

    def test_search_result_attribute(self):
        mock_r = MagicMock()
        mock_r.search_result = "inner text"
        del mock_r.page_content
        texts = _extract_texts([mock_r], 10)
        assert texts == ["inner text"]

    def test_page_content_attribute(self):
        mock_r = MagicMock(spec=[])
        mock_r.search_result = MagicMock(spec=[])
        mock_r.search_result.page_content = "from page_content"
        texts = _extract_texts([mock_r], 10)
        assert "from page_content" in texts[0]

    def test_dict_result(self):
        results = [{"text": "from_dict", "extra": "data"}]
        texts = _extract_texts(results, 10)
        assert texts == ["from_dict"]

    def test_respects_limit(self):
        results = [f"item_{i}" for i in range(20)]
        texts = _extract_texts(results, 5)
        assert len(texts) == 5


# --- _multi_cognee_search ---

class TestMultiCogneeSearch:
    @pytest.mark.asyncio
    async def test_returns_results(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=["result1", "result2"])
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test query",
            top_k=10,
            datasets=["ds_main"],
            node_name=["main"],
            session_id="test_session",
        )
        assert results is not None
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_all_fail(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=Exception("search failed"))
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test",
            top_k=10,
            datasets=["ds_main"],
            node_name=["main"],
            session_id="test_session",
        )
        assert results is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        async def slow_search(**kwargs):
            await asyncio.sleep(PER_SEARCH_TIMEOUT + 5)
            return ["should_not_return"]

        mock_cognee = MagicMock()
        mock_cognee.search = slow_search
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test",
            top_k=10,
            datasets=["ds_main"],
            node_name=["main"],
            session_id="test_session",
        )
        assert results is None

    @pytest.mark.asyncio
    async def test_deduplicates_results(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=["same_text", "same_text", "different"])
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test",
            top_k=10,
            datasets=["ds_main"],
            node_name=["main"],
            session_id="test_session",
        )
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_passes_system_prompt(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=["result"])
        SearchType = _make_search_type_enum()

        await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
            system_prompt="Be helpful",
        )
        call_kwargs = mock_cognee.search.call_args[1]
        assert call_kwargs["system_prompt"] == "Be helpful"

    @pytest.mark.asyncio
    async def test_omits_system_prompt_when_empty(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(return_value=["result"])
        SearchType = _make_search_type_enum()

        await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
            system_prompt="",
        )
        call_kwargs = mock_cognee.search.call_args[1]
        assert "system_prompt" not in call_kwargs

    @pytest.mark.asyncio
    async def test_multiple_types_aggregated(self):
        call_types = []

        async def mock_search(query_type, **kwargs):
            call_types.append(query_type.name)
            return [f"result_{query_type.name}"]

        mock_cognee = MagicMock()
        mock_cognee.search = mock_search
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
        )
        assert len(results) == 2
        assert set(call_types) == {"CHUNKS", "CHUNKS_LEXICAL"}

    @pytest.mark.asyncio
    async def test_partial_failure_returns_successful_results(self):
        call_count = 0

        async def mock_search(query_type, **kwargs):
            nonlocal call_count
            call_count += 1
            if query_type.name == "CHUNKS":
                return ["good_result"]
            raise Exception("CHUNKS_LEXICAL failed")

        mock_cognee = MagicMock()
        mock_cognee.search = mock_search
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
        )
        assert results is not None
        assert len(results) == 1
        assert results[0] == "good_result"

    @pytest.mark.asyncio
    async def test_searches_run_in_parallel_not_sequentially(self):
        async def delayed_search(query_type, **kwargs):
            await asyncio.sleep(0.5)
            return [f"result_{query_type.name}"]

        mock_cognee = MagicMock()
        mock_cognee.search = delayed_search
        SearchType = _make_search_type_enum()

        loop = asyncio.get_event_loop()
        start = loop.time()
        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
        )
        elapsed = loop.time() - start

        assert results is not None
        assert len(results) == 2
        assert elapsed < 0.9, f"Expected parallel execution (<0.9s), took {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_timeout_on_one_type_does_not_block_others(self):
        async def mixed_search(query_type, **kwargs):
            if query_type.name == "CHUNKS":
                return ["good_result"]
            await asyncio.sleep(5)
            return ["should_not_appear"]

        mock_cognee = MagicMock()
        mock_cognee.search = mixed_search
        SearchType = _make_search_type_enum()

        with patch(
            "python.extensions.message_loop_prompts_after._50_recall_memories.PER_SEARCH_TIMEOUT",
            0.3,
        ):
            results = await _multi_cognee_search(
                mock_cognee,
                search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
                query="test",
                top_k=10,
                datasets=["ds"],
                node_name=["main"],
                session_id="sess",
            )

        assert results is not None
        assert any(r == "good_result" for r in results)
        assert not any(r == "should_not_appear" for r in results)

    @pytest.mark.asyncio
    async def test_all_types_fail_returns_none(self):
        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=Exception("all fail"))
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
        )
        assert results is None

    @pytest.mark.asyncio
    async def test_deduplicates_results_across_types(self):
        async def dup_search(query_type, **kwargs):
            return ["shared_result", f"unique_{query_type.name}"]

        mock_cognee = MagicMock()
        mock_cognee.search = dup_search
        SearchType = _make_search_type_enum()

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[SearchType.CHUNKS, SearchType.CHUNKS_LEXICAL],
            query="test",
            top_k=10,
            datasets=["ds"],
            node_name=["main"],
            session_id="sess",
        )

        result_strs = [str(r) for r in results]
        assert result_strs.count("shared_result") == 1
        assert len(results) == 3


# --- _write_extras ---

class TestWriteExtras:
    def test_no_results_clears_extras(self):
        agent = MagicMock()
        extras = {}
        log_item = MagicMock()
        _write_extras(agent, extras, [], [], log_item)
        assert "memories" not in extras
        assert "solutions" not in extras
        log_item.update.assert_called_with(heading="No memories or solutions found")

    def test_memories_written(self):
        agent = MagicMock()
        agent.parse_prompt.return_value = "parsed_memories"
        extras = {}
        log_item = MagicMock()
        _write_extras(agent, extras, ["mem1", "mem2"], [], log_item)
        assert extras["memories"] == "parsed_memories"
        assert "solutions" not in extras

    def test_solutions_written(self):
        agent = MagicMock()
        agent.parse_prompt.return_value = "parsed_solutions"
        extras = {}
        log_item = MagicMock()
        _write_extras(agent, extras, [], ["sol1"], log_item)
        assert "memories" not in extras
        assert extras["solutions"] == "parsed_solutions"
