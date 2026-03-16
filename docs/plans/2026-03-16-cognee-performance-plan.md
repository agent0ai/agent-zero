# Cognee Memory Performance Optimization — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce memory recall latency from 30+ seconds to under 15 seconds and optimize dashboard/delete operations.

**Architecture:** Four independent optimizations applied to the Cognee memory layer: (1) parallel search, (2) startup-only initialization, (3) dashboard caching, (4) O(1) delete. Each can be implemented and tested independently.

**Tech Stack:** Python 3.11+, asyncio, pytest, cognee >= 0.5.4

**Design doc:** `docs/plans/2026-03-16-cognee-performance-design.md`

---

### Task 1: Parallel search in `_multi_cognee_search` (recall extension)

**Files:**
- Modify: `python/extensions/message_loop_prompts_after/_50_recall_memories.py:398-436`
- Test: `tests/extensions/test_recall_memories.py` (create)

**Step 1: Write the failing test**

Create `tests/extensions/__init__.py` if it doesn't exist, then create test file:

```python
"""Tests for parallel search in _multi_cognee_search."""

import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_memory_state():
    import python.helpers.memory as mem
    import python.helpers.cognee_init as ci
    mem._cognee = None
    mem._SearchType = None
    ci._configured = False
    yield
    mem._cognee = None
    mem._SearchType = None
    ci._configured = False


class TestMultiCogneeSearchParallel:
    @pytest.mark.asyncio
    async def test_searches_run_in_parallel_not_sequentially(self):
        """Two search types with 2s delay each should complete in ~2s, not ~4s."""
        from python.extensions.message_loop_prompts_after._50_recall_memories import (
            _multi_cognee_search,
        )

        call_times = []

        async def slow_search(**kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.5)
            return [MagicMock(search_result="result")]

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=slow_search)

        SearchType = MagicMock()
        type_a = MagicMock()
        type_a.name = "CHUNKS"
        type_b = MagicMock()
        type_b.name = "CHUNKS_LEXICAL"

        start = asyncio.get_event_loop().time()
        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[type_a, type_b],
            query="test",
            top_k=10,
            datasets=["ds1"],
            node_name=["main"],
            session_id="sess1",
        )
        elapsed = asyncio.get_event_loop().time() - start

        assert results is not None
        assert len(results) >= 1
        # Parallel: should take ~0.5s. Sequential would take ~1.0s.
        assert elapsed < 0.9, f"Searches ran sequentially ({elapsed:.2f}s), expected parallel"

    @pytest.mark.asyncio
    async def test_timeout_on_one_type_does_not_block_others(self):
        """If one search type times out, others should still return results."""
        from python.extensions.message_loop_prompts_after._50_recall_memories import (
            _multi_cognee_search,
            PER_SEARCH_TIMEOUT,
        )

        call_count = 0

        async def mixed_search(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("query_type") and kwargs["query_type"].name == "SLOW":
                await asyncio.sleep(PER_SEARCH_TIMEOUT + 5)
            return [MagicMock(search_result="fast_result")]

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=mixed_search)

        fast_type = MagicMock()
        fast_type.name = "FAST"
        slow_type = MagicMock()
        slow_type.name = "SLOW"

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[fast_type, slow_type],
            query="test",
            top_k=10,
            datasets=["ds1"],
            node_name=["main"],
            session_id="sess1",
        )

        assert results is not None
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_all_types_fail_returns_none(self):
        """If all search types fail, return None."""
        from python.extensions.message_loop_prompts_after._50_recall_memories import (
            _multi_cognee_search,
        )

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=Exception("search failed"))

        type_a = MagicMock()
        type_a.name = "CHUNKS"

        results = await _multi_cognee_search(
            mock_cognee,
            search_types=[type_a],
            query="test",
            top_k=10,
            datasets=["ds1"],
            node_name=["main"],
            session_id="sess1",
        )

        assert results is None
```

**Step 2: Run test to verify it fails**

Run: `cd /path/to/agent-zero && python -m pytest tests/extensions/test_recall_memories.py -v`
Expected: `test_searches_run_in_parallel_not_sequentially` FAILS (sequential search takes > 0.9s)

**Step 3: Implement parallel search**

In `python/extensions/message_loop_prompts_after/_50_recall_memories.py`, replace the `_multi_cognee_search` function (lines 398-436):

```python
async def _multi_cognee_search(
    cognee, *, search_types, query, top_k, datasets, node_name, session_id,
    system_prompt="",
):
    search_kwargs = dict(
        query_text=query,
        top_k=top_k,
        datasets=datasets,
        node_name=node_name,
        session_id=session_id,
    )
    if system_prompt:
        search_kwargs["system_prompt"] = system_prompt

    async def _search_one(st):
        try:
            return await asyncio.wait_for(
                cognee.search(query_type=st, **search_kwargs),
                timeout=PER_SEARCH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            PrintStyle.error(f"Cognee search ({st.name}) timed out after {PER_SEARCH_TIMEOUT}s")
            return None
        except Exception as e:
            PrintStyle.error(f"Cognee search ({st.name}) failed: {e}")
            return None

    results_per_type = await asyncio.gather(
        *[_search_one(st) for st in search_types]
    )

    all_results = []
    for results in results_per_type:
        if results:
            all_results.extend(results)

    if all_results:
        seen = {}
        unique = []
        for r in all_results:
            raw = r.search_result if hasattr(r, "search_result") else r
            key = str(raw)[:200]
            if key not in seen:
                seen[key] = True
                unique.append(r)
        return unique
    return None
```

**Step 4: Run tests to verify they pass**

Run: `cd /path/to/agent-zero && python -m pytest tests/extensions/test_recall_memories.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add tests/extensions/test_recall_memories.py python/extensions/message_loop_prompts_after/_50_recall_memories.py
git commit -m "perf: parallelize _multi_cognee_search in recall extension"
```

---

### Task 2: Parallel search in `Memory._multi_search`

**Files:**
- Modify: `python/helpers/memory.py:278-323`
- Test: `tests/helpers/test_memory.py` (add to existing)

**Step 1: Write the failing test**

Add to `tests/helpers/test_memory.py`:

```python
class TestMultiSearchParallel:
    @pytest.mark.asyncio
    async def test_multi_search_runs_in_parallel(self):
        """Multi-search with 2 types should run in parallel, not sequentially."""
        from python.helpers.memory import Memory
        import python.helpers.memory as mem_mod

        call_times = []

        async def slow_search(**kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.5)
            meta = json.dumps({"id": f"id_{len(call_times)}", "area": "main"})
            return [f"[META:{meta}]\nresult_{len(call_times)}"]

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=slow_search)
        mock_search_type = MagicMock()
        type_a = MagicMock(name="CHUNKS")
        type_b = MagicMock(name="CHUNKS_LEXICAL")
        mock_search_type.CHUNKS = type_a
        mem_mod._cognee = mock_cognee
        mem_mod._SearchType = mock_search_type

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": True,
                "cognee_search_types": "CHUNKS,CHUNKS_LEXICAL",
            }.get(name, default)

            # Patch hasattr to make our mocks look like SearchType attrs
            mock_search_type.CHUNKS = type_a
            mock_search_type.CHUNKS_LEXICAL = type_b
            setattr(mock_search_type, "CHUNKS", type_a)
            setattr(mock_search_type, "CHUNKS_LEXICAL", type_b)

            memory = Memory(dataset_name="default", memory_subdir="default")
            start = asyncio.get_event_loop().time()
            results = await memory.search_similarity_threshold(
                query="test", limit=10, threshold=0.5
            )
            elapsed = asyncio.get_event_loop().time() - start

        # Parallel: ~0.5s. Sequential: ~1.0s.
        assert elapsed < 0.9, f"Multi-search ran sequentially ({elapsed:.2f}s)"

    @pytest.mark.asyncio
    async def test_multi_search_timeout_per_type(self):
        """Each search type has its own timeout; one hanging type doesn't block all."""
        from python.helpers.memory import Memory
        import python.helpers.memory as mem_mod

        async def hanging_search(**kwargs):
            if "CHUNKS_LEXICAL" in str(kwargs.get("query_type", "")):
                await asyncio.sleep(60)
            meta = json.dumps({"id": "ok_id", "area": "main"})
            return [f"[META:{meta}]\nok_result"]

        mock_cognee = MagicMock()
        mock_cognee.search = AsyncMock(side_effect=hanging_search)
        mock_search_type = MagicMock()
        type_a = MagicMock()
        type_a.name = "CHUNKS"
        type_a.__str__ = lambda self: "CHUNKS"
        type_b = MagicMock()
        type_b.name = "CHUNKS_LEXICAL"
        type_b.__str__ = lambda self: "CHUNKS_LEXICAL"
        setattr(mock_search_type, "CHUNKS", type_a)
        setattr(mock_search_type, "CHUNKS_LEXICAL", type_b)
        mem_mod._cognee = mock_cognee
        mem_mod._SearchType = mock_search_type

        with patch("python.helpers.memory.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_multi_search_enabled": True,
                "cognee_search_types": "CHUNKS,CHUNKS_LEXICAL",
            }.get(name, default)

            memory = Memory(dataset_name="default", memory_subdir="default")
            results = await asyncio.wait_for(
                memory.search_similarity_threshold(query="test", limit=10, threshold=0.5),
                timeout=20,
            )

        # Should return results from CHUNKS even though CHUNKS_LEXICAL hung
        assert isinstance(results, list)
```

**Step 2: Run test to verify it fails**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_memory.py::TestMultiSearchParallel -v`
Expected: `test_multi_search_runs_in_parallel` FAILS

**Step 3: Implement parallel `_multi_search`**

In `python/helpers/memory.py`, replace `_multi_search` method (lines 278-323):

```python
    SEARCH_TIMEOUT = 15

    async def _multi_search(
        self, cognee, SearchType, query: str, limit: int,
        datasets: list[str], node_names: list[str],
    ) -> list[Document]:
        type_names = get_cognee_setting("cognee_search_types", "GRAPH_COMPLETION,CHUNKS_LEXICAL")
        search_types = []
        for name in type_names.split(","):
            name = name.strip()
            if hasattr(SearchType, name):
                search_types.append(getattr(SearchType, name))
        if not search_types:
            search_types = [SearchType.CHUNKS]

        per_type_limit = max(limit, 10)

        async def _search_one(st):
            try:
                return await asyncio.wait_for(
                    cognee.search(
                        query_text=query,
                        query_type=st,
                        top_k=per_type_limit,
                        datasets=datasets if datasets else None,
                        node_name=node_names if node_names else None,
                    ),
                    timeout=self.SEARCH_TIMEOUT,
                )
            except asyncio.TimeoutError:
                PrintStyle.error(f"Cognee multi-search ({st.name}) timed out after {self.SEARCH_TIMEOUT}s")
                return None
            except Exception as e:
                PrintStyle.error(f"Cognee multi-search ({st.name}) failed: {e}")
                return None

        results_per_type = await asyncio.gather(
            *[_search_one(st) for st in search_types]
        )

        all_results = []
        for results in results_per_type:
            if results:
                all_results.extend(results)

        if not all_results:
            try:
                all_results = await asyncio.wait_for(
                    cognee.search(
                        query_text=query,
                        query_type=SearchType.CHUNKS,
                        top_k=limit,
                        datasets=datasets if datasets else None,
                    ),
                    timeout=self.SEARCH_TIMEOUT,
                )
            except Exception as e:
                PrintStyle.error(f"Cognee fallback search failed: {e}")
                return []

        docs = _results_to_documents(all_results, limit * len(search_types))
        return _deduplicate_documents(docs)[:limit]
```

Also add `import asyncio` to the top of the file if not already present.

**Step 4: Run tests**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_memory.py -v`
Expected: All tests PASS (including new and existing)

**Step 5: Commit**

```bash
git add python/helpers/memory.py tests/helpers/test_memory.py
git commit -m "perf: parallelize _multi_search in Memory class"
```

---

### Task 3: Move Cognee initialization to startup

**Files:**
- Modify: `python/helpers/cognee_init.py`
- Modify: `python/helpers/memory.py`
- Modify: `prepare.py`
- Test: `tests/helpers/test_cognee_init.py` (add to existing)
- Test: `tests/helpers/test_memory.py` (update existing tests)

**Step 1: Write the failing test**

Add to `tests/helpers/test_cognee_init.py`:

```python
class TestInitCognee:
    @pytest.mark.asyncio
    async def test_init_cognee_calls_configure_and_create_tables(self):
        """init_cognee() should call configure_cognee + create_db_and_tables once."""
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        mock_create = AsyncMock()

        settings = {
            "util_model_provider": "openai",
            "util_model_name": "gpt-4o-mini",
            "util_model_api_base": "",
            "embed_model_provider": "huggingface",
            "embed_model_name": "BAAI/bge-small-en-v1.5",
            "embed_model_api_base": "",
            "api_keys": {"openai": "sk-test", "huggingface": "hf-test"},
        }

        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=settings), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files, \
             patch("python.helpers.cognee_init._create_db_tables", new=mock_create):
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            await ci.init_cognee()

        mock_cognee.config.set_llm_config.assert_called_once()
        mock_create.assert_called_once()

    def test_get_cognee_raises_if_not_initialized(self):
        """get_cognee() should raise RuntimeError if init_cognee was not called."""
        import python.helpers.cognee_init as ci
        ci._cognee_module = None
        with pytest.raises(RuntimeError, match="not initialized"):
            ci.get_cognee()
```

**Step 2: Run test to verify it fails**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_cognee_init.py::TestInitCognee -v`
Expected: FAIL — `init_cognee` and `get_cognee` don't exist yet

**Step 3: Implement startup initialization**

In `python/helpers/cognee_init.py`, add at the end:

```python
_cognee_module = None
_search_type_class = None


async def _create_db_tables():
    from cognee.infrastructure.databases.relational import create_db_and_tables
    await create_db_and_tables()
    PrintStyle.standard("Cognee DB tables initialized")


async def init_cognee() -> None:
    global _cognee_module, _search_type_class
    configure_cognee()
    import cognee
    from cognee import SearchType
    _cognee_module = cognee
    _search_type_class = SearchType
    await _create_db_tables()
    PrintStyle.standard("Cognee fully initialized")


def get_cognee():
    if _cognee_module is None:
        raise RuntimeError("Cognee not initialized — call init_cognee() at startup")
    return _cognee_module, _search_type_class
```

In `python/helpers/memory.py`, replace the `_get_cognee` function and remove `_ensure_cognee_db` calls from `Memory.get()` and `Memory.get_by_subdir()`:

```python
def _get_cognee():
    from python.helpers.cognee_init import get_cognee
    return get_cognee()
```

Remove these lines from `Memory.get()`:
```python
        cognee, _ = _get_cognee()
        await _ensure_cognee_db(cognee)
```
Replace with just the memory_subdir/dataset logic (no cognee calls).

Remove these lines from `Memory.get_by_subdir()`:
```python
        cognee, _ = _get_cognee()
        await _ensure_cognee_db(cognee)
```

Remove `_with_cognee_setup_retry` wrapper from all calls — replace with direct calls:
- `memory.py`: `cognee.add(...)`, `cognee.search(...)`, `cognee.datasets.list_datasets()` — no retry wrapper
- `_50_recall_memories.py`: already uses direct `cognee.search` in `_multi_cognee_search`
- `cognee_background.py`: remove `_with_cognee_setup_retry` wrapper from `cognee.cognify`

In `prepare.py`, add cognee initialization:

```python
from python.helpers import dotenv, runtime, settings
import string
import random
import asyncio
from python.helpers.print_style import PrintStyle


PrintStyle.standard("Preparing environment...")

try:

    runtime.initialize()

    # generate random root password if not set (for SSH)
    root_pass = dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
    if not root_pass:
        root_pass = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        PrintStyle.standard("Changing root password...")
    settings.set_root_password(root_pass)

    # Initialize Cognee memory system
    try:
        from python.helpers.cognee_init import init_cognee
        asyncio.get_event_loop().run_until_complete(init_cognee())
        from python.helpers.cognee_background import CogneeBackgroundWorker
        CogneeBackgroundWorker.get_instance().start()
    except Exception as e:
        PrintStyle.error(f"Cognee initialization failed: {e}")

except Exception as e:
    PrintStyle.error(f"Error in preload: {e}")
```

**Step 4: Run all tests**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_cognee_init.py tests/helpers/test_memory.py -v`
Expected: All PASS. Note: existing tests that mock `_get_cognee` directly will need `_reset_module_state` fixture updated to set `cognee_init._cognee_module` instead of `memory._cognee`.

**Step 5: Update existing test fixtures**

The `_reset_module_state` fixture in `tests/helpers/test_memory.py` must also reset the new globals:

```python
@pytest.fixture(autouse=True)
def _reset_module_state():
    import python.helpers.memory as mem
    import python.helpers.cognee_init as ci
    old_cognee = ci._cognee_module
    old_st = ci._search_type_class
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False
    yield
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False
    ci._cognee_module = old_cognee
    ci._search_type_class = old_st
```

**Step 6: Run full test suite**

Run: `cd /path/to/agent-zero && python -m pytest tests/ -v --timeout=30`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add python/helpers/cognee_init.py python/helpers/memory.py prepare.py \
    tests/helpers/test_cognee_init.py tests/helpers/test_memory.py
git commit -m "refactor: move Cognee init to startup, remove runtime retry wrappers"
```

---

### Task 4: Dashboard caching and true pagination

**Files:**
- Modify: `python/api/memory_dashboard.py`
- Test: `tests/api/test_memory_dashboard.py` (create)

**Step 1: Write the failing test**

Create `tests/api/test_memory_dashboard.py`:

```python
"""Tests for memory dashboard caching and pagination."""

import sys
import time
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestDashboardCache:
    @pytest.mark.asyncio
    async def test_second_call_uses_cache(self):
        """Listing all memories twice should only call list_data once (cached)."""
        from python.api.memory_dashboard import MemoryDashboard

        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"

        mock_item = MagicMock()
        mock_item.raw_data_location = None
        mock_item.name = '[META:{"id":"m1","area":"main"}]\ntest content'

        list_data_mock = AsyncMock(return_value=[mock_item])

        dashboard = MemoryDashboard()
        with patch("python.api.memory_dashboard._get_cognee") as mock_gc, \
             patch("python.api.memory_dashboard._ensure_cognee_db", new=AsyncMock()), \
             patch("python.api.memory_dashboard.Memory") as MockMem:
            mock_cognee = MagicMock()
            mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
            mock_cognee.datasets.list_data = list_data_mock
            mock_gc.return_value = (mock_cognee, MagicMock())

            mem_instance = MagicMock()
            mem_instance._area_dataset = lambda area: f"default_{area}"
            MockMem.get_by_subdir = AsyncMock(return_value=mem_instance)
            MockMem.Area = MagicMock()
            MockMem.Area.__iter__ = MagicMock(return_value=iter([
                MagicMock(value="main"),
                MagicMock(value="fragments"),
                MagicMock(value="solutions"),
            ]))

            # First call
            result1 = await dashboard._search_memories({"memory_subdir": "default"})
            # Second call
            result2 = await dashboard._search_memories({"memory_subdir": "default"})

        assert result1["success"] is True
        assert result2["success"] is True
        # list_data should be called only on first request (cached for second)
        assert list_data_mock.call_count == 1


class TestDashboardPagination:
    @pytest.mark.asyncio
    async def test_offset_and_limit_applied_before_file_reads(self):
        """With offset=2, limit=1, should only process 1 item, not all."""
        from python.api.memory_dashboard import MemoryDashboard

        items = []
        for i in range(5):
            item = MagicMock()
            item.raw_data_location = None
            item.name = f'[META:{{"id":"m{i}","area":"main","timestamp":"2026-01-0{i+1}"}}]\ncontent_{i}'
            items.append(item)

        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"

        dashboard = MemoryDashboard()
        with patch("python.api.memory_dashboard._get_cognee") as mock_gc, \
             patch("python.api.memory_dashboard._ensure_cognee_db", new=AsyncMock()), \
             patch("python.api.memory_dashboard.Memory") as MockMem:
            mock_cognee = MagicMock()
            mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
            mock_cognee.datasets.list_data = AsyncMock(return_value=items)
            mock_gc.return_value = (mock_cognee, MagicMock())

            mem_instance = MagicMock()
            mem_instance._area_dataset = lambda area: f"default_{area}"
            MockMem.get_by_subdir = AsyncMock(return_value=mem_instance)
            MockMem.Area = MagicMock()
            MockMem.Area.__iter__ = MagicMock(return_value=iter([
                MagicMock(value="main"),
            ]))

            result = await dashboard._search_memories({
                "memory_subdir": "default",
                "offset": 2,
                "limit": 1,
            })

        assert result["success"] is True
        assert len(result["memories"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd /path/to/agent-zero && python -m pytest tests/api/test_memory_dashboard.py -v`
Expected: FAIL — no caching, second call hits list_data again

**Step 3: Implement caching and pagination**

In `python/api/memory_dashboard.py`, add a module-level cache and modify `_search_memories`:

```python
import time

_dashboard_cache: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 60  # seconds


def invalidate_dashboard_cache():
    """Call after insert/delete/update to clear cached data."""
    _dashboard_cache.clear()
```

Modify `_search_memories` to check cache before loading, and apply offset/limit before building the response (not after loading everything).

Modify `Memory.insert_documents`, `Memory.delete_documents_by_ids`, `Memory.update_documents` in `memory.py` to call `invalidate_dashboard_cache()` after mutations.

**Step 4: Run tests**

Run: `cd /path/to/agent-zero && python -m pytest tests/api/test_memory_dashboard.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add python/api/memory_dashboard.py python/helpers/memory.py tests/api/test_memory_dashboard.py
git commit -m "perf: add dashboard cache with TTL and true server-side pagination"
```

---

### Task 5: Optimize delete with dataset cache

**Files:**
- Modify: `python/helpers/memory.py` (function `_delete_data_by_id`)
- Test: `tests/helpers/test_memory.py` (add to existing)

**Step 1: Write the failing test**

Add to `tests/helpers/test_memory.py`:

```python
class TestDeleteOptimization:
    @pytest.mark.asyncio
    async def test_bulk_delete_single_list_data_call(self):
        """Deleting 3 IDs from same dataset should call list_data at most once per dataset."""
        from python.helpers.memory import Memory
        import python.helpers.memory as mem_mod

        mock_cognee = MagicMock()
        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"

        items = []
        for i, doc_id in enumerate(["aaa", "bbb", "ccc"]):
            item = MagicMock()
            item.raw_data_location = f"file:///data/{doc_id}.txt"
            item.name = f"{doc_id}.txt"
            item.id = f"item_{i}"
            items.append(item)

        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])
        mock_cognee.datasets.list_data = AsyncMock(return_value=items)
        mock_cognee.datasets.delete_data = AsyncMock()
        mem_mod._cognee = mock_cognee
        mem_mod._SearchType = MagicMock()

        memory = Memory(dataset_name="default", memory_subdir="default")
        removed = await memory.delete_documents_by_ids(["aaa", "bbb", "ccc"])

        # Should call list_data at most 3 times (once per area), not 9 times (3 IDs * 3 areas)
        assert mock_cognee.datasets.list_data.call_count <= 3
```

**Step 2: Run test to verify it fails**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_memory.py::TestDeleteOptimization -v`
Expected: FAIL — current code calls list_data 9 times (3 ids * 3 areas)

**Step 3: Implement optimized bulk delete**

Replace `delete_documents_by_ids` to batch deletes per dataset:

```python
    async def delete_documents_by_ids(self, ids: list[str]) -> list[Document]:
        cognee, _ = _get_cognee()
        removed = []
        id_set = set(ids)

        for area in Memory.Area:
            dataset_name = self._area_dataset(area.value)
            try:
                datasets = await cognee.datasets.list_datasets()
                target = None
                for ds in datasets:
                    if ds.name == dataset_name:
                        target = ds
                        break
                if not target:
                    continue
                data_items = await cognee.datasets.list_data(target.id)
                for item in data_items:
                    item_text = getattr(item, "raw_data_location", "") or getattr(item, "name", "") or ""
                    item_str = str(item_text)
                    for doc_id in list(id_set):
                        if doc_id in item_str:
                            await cognee.datasets.delete_data(
                                dataset_id=target.id,
                                data_id=item.id,
                            )
                            removed.append(Document(page_content="", metadata={"id": doc_id}))
                            id_set.discard(doc_id)
                            break
            except Exception as e:
                PrintStyle.error(f"Failed to delete from {dataset_name}: {e}")

        return removed
```

**Step 4: Run tests**

Run: `cd /path/to/agent-zero && python -m pytest tests/helpers/test_memory.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add python/helpers/memory.py tests/helpers/test_memory.py
git commit -m "perf: optimize bulk delete to single scan per dataset"
```

---

### Task 6: Run full test suite and verify

**Step 1: Run all tests**

Run: `cd /path/to/agent-zero && python -m pytest tests/ -v --timeout=60`
Expected: All tests PASS, no regressions

**Step 2: Final commit if any fixups needed**

```bash
git add -A
git commit -m "fix: test fixups for cognee performance optimization"
```
