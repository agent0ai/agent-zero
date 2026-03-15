# Cognee Integration Refactor — Design

## Problem

The current Cognee integration has 7 critical bugs, uses unreliable env-var-based configuration instead of the official `cognee.config.*` API, and doesn't utilize several key Cognee capabilities (temporal knowledge, system_prompt in search, chunk tuning).

The most visible symptom: `cognee.search()` hangs on SQLite `log_query()` causing 30s timeouts on every agent message.

## Scope

5 files, 7 bug fixes, 4 new capabilities.

## Changes by File

### 1. `python/helpers/cognee_init.py` — Config Rewrite

**Current:** Sets `os.environ["LLM_PROVIDER"]`, etc. Silent `except Exception: pass`.

**New:** Use `cognee.config.*` API:
- `cognee.config.set_llm_config(...)` — provider, model, key, endpoint from Agent Zero `util_model_*` settings
- `cognee.config.set_vector_db_config(...)` — from `embed_model_*` settings
- `cognee.config.set_chunk_size()` / `set_chunk_overlap()` — new settings `cognee_chunk_size` (default 512), `cognee_chunk_overlap` (default 50)
- `cognee.config.set_data_root_directory()` / `set_system_root_directory()` — keep existing paths
- Replace silent `except Exception: pass` with `PrintStyle.error(...)` logging
- Add `gemini` and `ollama` to `_PROVIDER_MAP`

### 2. `python/helpers/memory.py` — Bug Fixes

| Bug | Fix |
|-----|-----|
| `insert_documents` marks success on failure | Move `ids.append(doc_id)` inside try block, after `cognee.add()` |
| `_get_cognee()` not thread-safe | Add `threading.Lock()` around lazy init |
| `get_knowledge_subdirs_by_memory_subdir` mutates default list | Copy list before appending |
| `_delete_data_by_id` wrong match logic | Use proper Cognee data item attributes |
| `search_similarity_threshold` ignores threshold | Post-filter results by score |

### 3. `python/extensions/message_loop_prompts_after/_50_recall_memories.py` — Resilience + system_prompt

Already has two-phase search. Add:
- Per-search `asyncio.wait_for()` timeout (15s) — already done
- Fallback wrapped in try/except with timeout — already done
- Pass `system_prompt` from agent context to `cognee.search()` for LLM-based search types
- Error logging instead of silent `except: pass` — already done

### 4. `python/extensions/message_loop_prompts_after/_91_recall_wait.py` — Graceful error handling

Already has TimeoutError/CancelledError/Exception catching. No further changes needed.

### 5. `python/helpers/cognee_background.py` — Settings + Temporal

- Read settings from `get_settings()` instead of `get_default_value` (env-only)
- Add `temporal_cognify` parameter: `await cognee.cognify(temporal_cognify=temporal_enabled)`
- Handle memify failures without aborting the loop

### 6. `python/api/memory_dashboard.py` — Edge Cases

- Guard `cognee.visualize_graph()` with hasattr/try-except
- Wrap all Cognee calls in try/except with logging
- Add basic pagination for `list_data`

## New Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `cognee_chunk_size` | `512` | Chunk size for cognify |
| `cognee_chunk_overlap` | `50` | Chunk overlap |
| `cognee_temporal_enabled` | `true` | Enable temporal knowledge graph |

Existing settings that now get properly forwarded to Cognee:
- `util_model_provider` / `util_model_name` / `util_model_api_base` → Cognee LLM
- `embed_model_provider` / `embed_model_name` / `embed_model_api_base` → Cognee embedding
- `api_keys` → Cognee API keys

## Non-Goals

- Changing vector/graph DB backends (stay with LanceDB + Kuzu defaults)
- Adding file/URL ingestion to `cognee.add()` (only text for now)
- Modifying the FAISS migration script (stable, completed)
