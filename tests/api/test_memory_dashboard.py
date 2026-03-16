"""Tests for python/api/memory_dashboard.py — dashboard cache + pagination."""

import sys
import json
import time as _time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _make_mock_dataset(name, ds_id="ds_1"):
    ds = MagicMock()
    ds.name = name
    ds.id = ds_id
    return ds


def _make_mock_data_item(raw_location, item_id="item_1"):
    item = MagicMock()
    item.raw_data_location = raw_location
    item.name = Path(raw_location).name if raw_location else ""
    item.id = item_id
    return item


def _setup_cognee(mock_cognee):
    """Wire mock cognee into cognee_init globals and sys.modules."""
    import python.helpers.cognee_init as ci
    ci._cognee_module = mock_cognee
    ci._search_type_class = MagicMock()
    sys.modules["cognee"] = mock_cognee


def _make_dashboard():
    from python.api.memory_dashboard import MemoryDashboard
    return MemoryDashboard(app=MagicMock(), thread_lock=MagicMock())


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level caches before each test."""
    import python.helpers.cognee_init as ci
    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False

    import python.helpers.memory as mem
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()

    from python.api.memory_dashboard import _dashboard_cache
    _dashboard_cache.clear()

    saved_cognee = sys.modules.get("cognee")

    yield

    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    _dashboard_cache.clear()

    if saved_cognee is not None:
        sys.modules["cognee"] = saved_cognee


def _build_meta_text(content, meta):
    return f"[META:{json.dumps(meta)}]\n{content}"


def _make_cognee_with_items(items_by_dataset: dict[str, list]):
    """Build a mock cognee whose list_datasets/list_data return items_by_dataset.

    items_by_dataset: {"default_main": [("file:///path", "id_1", "content text"), ...]}
    Each tuple: (raw_data_location, item_id, content_body)
    """
    mock_cognee = MagicMock()
    datasets = []
    data_map = {}
    for ds_name, items in items_by_dataset.items():
        ds = _make_mock_dataset(ds_name, ds_id=f"id_{ds_name}")
        datasets.append(ds)
        data_items = []
        for raw_loc, item_id, content_body in items:
            di = _make_mock_data_item(raw_loc, item_id=item_id)
            data_items.append(di)
        data_map[f"id_{ds_name}"] = data_items

    mock_cognee.datasets.list_datasets = AsyncMock(return_value=datasets)

    async def _list_data(ds_id):
        return data_map.get(ds_id, [])

    mock_cognee.datasets.list_data = AsyncMock(side_effect=_list_data)
    return mock_cognee, data_map


# ---------------------------------------------------------------------------
# Test: second call uses cache (list_data called only once)
# ---------------------------------------------------------------------------

class TestDashboardCaching:

    @pytest.mark.asyncio
    async def test_second_call_uses_cache(self, tmp_path):
        """Listing memories twice — list_data should only be called on the first call."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        result1 = await dashboard.process(req_input, MagicMock())
        call_count_after_first = mock_cognee.datasets.list_data.call_count

        result2 = await dashboard.process(req_input, MagicMock())
        call_count_after_second = mock_cognee.datasets.list_data.call_count

        assert result1["success"] is True
        assert result2["success"] is True
        assert call_count_after_first > 0
        assert call_count_after_second == call_count_after_first, \
            "Second call should use cache, not call list_data again"

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, tmp_path):
        """After TTL expires, list_data is called again."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        from python.api.memory_dashboard import _dashboard_cache, _CACHE_TTL
        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        await dashboard.process(req_input, MagicMock())
        call_count_first = mock_cognee.datasets.list_data.call_count

        for key in list(_dashboard_cache.keys()):
            cached_time, cached_data = _dashboard_cache[key]
            _dashboard_cache[key] = (cached_time - _CACHE_TTL - 1, cached_data)

        await dashboard.process(req_input, MagicMock())
        call_count_second = mock_cognee.datasets.list_data.call_count

        assert call_count_second > call_count_first, \
            "After TTL expiry, list_data should be called again"

    @pytest.mark.asyncio
    async def test_invalidate_clears_cache(self, tmp_path):
        """invalidate_dashboard_cache() forces reload on next call."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        from python.api.memory_dashboard import invalidate_dashboard_cache
        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        await dashboard.process(req_input, MagicMock())
        call_count_first = mock_cognee.datasets.list_data.call_count

        invalidate_dashboard_cache()

        await dashboard.process(req_input, MagicMock())
        call_count_second = mock_cognee.datasets.list_data.call_count

        assert call_count_second > call_count_first, \
            "After invalidation, list_data should be called again"


# ---------------------------------------------------------------------------
# Test: true pagination (offset + limit on cached data)
# ---------------------------------------------------------------------------

class TestDashboardPagination:

    def _make_items(self, tmp_path, count):
        """Create N mock items with content files on disk."""
        ds_items = []
        for i in range(count):
            meta = {
                "id": f"m{i}",
                "area": "main",
                "timestamp": f"2026-01-01 00:00:{i:02d}",
            }
            fpath = tmp_path / f"m{i}.txt"
            fpath.write_text(_build_meta_text(f"Content {i}", meta))
            ds_items.append((str(fpath), f"item_{i}", f"Content {i}"))
        return ds_items

    @pytest.mark.asyncio
    async def test_pagination_offset_limit(self, tmp_path):
        """5 items, offset=2 limit=2 → returns exactly 2 items."""
        items = self._make_items(tmp_path, 5)
        mock_cognee, _ = _make_cognee_with_items({
            "default_main": items,
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {
            "action": "search",
            "memory_subdir": "default",
            "search": "",
            "offset": 2,
            "limit": 2,
        }

        result = await dashboard.process(req_input, MagicMock())

        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_total_db_count_reflects_all_items(self, tmp_path):
        """Even with pagination, total_db_count returns full count."""
        items = self._make_items(tmp_path, 5)
        mock_cognee, _ = _make_cognee_with_items({
            "default_main": items,
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {
            "action": "search",
            "memory_subdir": "default",
            "search": "",
            "offset": 0,
            "limit": 2,
        }

        result = await dashboard.process(req_input, MagicMock())

        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert result["total_db_count"] == 5
