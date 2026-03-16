# Cognee Memory Performance Optimization

**Date:** 2026-03-16
**Status:** Approved
**Problem:** 30+ second delays on memory recall during chat; slow dashboard with 500+ memories

## Context

Agent Zero uses Cognee for persistent memory (vector search, knowledge graphs, document storage). Current setup: SQLite backend, GRAPH_COMPLETION + CHUNKS_LEXICAL multi-search, background cognify/memify worker. Memory recall runs on every N-th message loop iteration.

## Root Causes

1. **Sequential search across types** — `_multi_cognee_search` iterates search types one by one; with 15s timeout per type, two types = 30s worst case
2. **Runtime initialization on every request** — `Memory.get()` calls `_get_cognee()` + `_ensure_cognee_db()` + retry wrappers on every operation
3. **Dashboard loads all records** — no server-side pagination; reads every file from disk for 500+ items
4. **O(n) delete** — `_delete_data_by_id` scans all items in dataset to find target by string match
5. **SQLite contention** — concurrent reads during background cognify writes cause lock timeouts

## Design

### 1. Parallel search in `_multi_cognee_search`

**File:** `python/extensions/message_loop_prompts_after/_50_recall_memories.py`

Replace sequential `for st in search_types` loop with `asyncio.gather`. Each search type runs in parallel with its own 15s timeout. Failed/timed-out types return empty results without blocking others.

Applies to both `_multi_cognee_search` (recall) and `Memory._multi_search` (tool/dashboard).

**File:** `python/helpers/memory.py`

Same change in `_multi_search` — parallel `asyncio.gather` with per-type timeouts.

### 2. Move Cognee initialization to application startup

**File:** `python/helpers/cognee_init.py`

- Add `async def init_cognee()` — calls `configure_cognee()` + `create_db_and_tables()` once
- `get_cognee()` becomes a simple getter that raises if not initialized

**File:** `prepare.py` (or equivalent startup path)

- Call `await init_cognee()` after settings are loaded
- Start `CogneeBackgroundWorker`

**Files:** `python/helpers/memory.py`, `_50_recall_memories.py`, `memory_dashboard.py`

- Remove `_get_cognee()` / `_ensure_cognee_db()` calls from `Memory.get()`, `Memory.get_by_subdir()`
- Remove `_with_cognee_setup_retry` wrapper from all cognee calls — direct `cognee.search()`, `cognee.add()` instead
- If SQLite disappears at runtime, treat as fatal error (log + raise), not silent recovery

### 3. Dashboard caching and pagination

**File:** `python/api/memory_dashboard.py`

- **In-memory cache with TTL:** Cache `list_data()` results + parsed content for 60 seconds. ~1-5MB for 500 records.
- **Cache invalidation:** Clear on insert/delete/update via Memory class.
- **True server-side pagination:** Apply offset/limit before reading file content, not after loading everything.
- **Parallel file reads:** Batch `_read_data_item_content` calls with `asyncio.gather` (batches of 50).

### 4. O(1) delete via ID mapping

**File:** `python/helpers/memory.py`

- **Dataset cache:** Use `_datasets_cache` (already exists, unused) to map `dataset_name → dataset_object`. Invalidate on new dataset creation.
- **ID mapping:** On `cognee.add()`, store mapping `our_doc_id → cognee_item_id`. On delete, use direct `cognee.datasets.delete_data()` without scanning.
- **Bulk delete fallback:** If mapping unavailable, do single `list_data()` scan for all IDs at once instead of N separate scans.

## Files Changed

| File | Changes |
|------|---------|
| `python/helpers/cognee_init.py` | Add `init_cognee()`, simplify `get_cognee()` |
| `python/helpers/memory.py` | Remove runtime init, parallel `_multi_search`, dataset cache, ID mapping for delete |
| `python/helpers/cognee_background.py` | No changes (started from startup instead) |
| `python/api/memory_dashboard.py` | Add TTL cache, true pagination, parallel file reads |
| `python/extensions/message_loop_prompts_after/_50_recall_memories.py` | Parallel `_multi_cognee_search` |
| `prepare.py` | Call `init_cognee()` at startup |

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Chat recall latency | 30+ seconds | 5-15 seconds |
| Dashboard load (500 items) | 10-20 seconds | <2s (cached), <5s (cold) |
| Delete single item | O(n) scan | O(1) lookup |
| Bulk delete 10 items | 10 * O(n) scans | 1 scan or O(1) lookups |
| Runtime init overhead per request | lock + guard + try/except | zero |

## Testing

- Existing test suite (~2400 tests) covers memory operations
- Add integration tests for parallel search (mock cognee.search with delays)
- Add tests for cache invalidation in dashboard
- Add startup init test (verify cognee ready before first request)

## Risks

- **SQLite concurrency:** Parallel searches may increase lock contention. Mitigated by existing WAL mode (if enabled) or by keeping individual search timeouts.
- **Cache staleness:** 60s TTL means dashboard may show stale data for up to a minute after changes. Acceptable for browsing UI.
- **Cognee API compatibility:** ID mapping depends on `cognee.add()` return value. Need to verify what Cognee 0.5.4+ returns.
