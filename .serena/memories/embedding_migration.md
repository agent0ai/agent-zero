# Embedding Migration (Azure OpenAI via LiteLLM Proxy)

## Status: Implemented (branch `feat/embedding-migration`)

## What Changed (7 files, +52/-23 lines)

### Phase 1: Bug Fixes (P0)
- `models.py`: Added `EMBEDDING_BATCH_SIZE = 16` constant; batched `embed_documents()` for Azure compatibility
- `python/helpers/memory.py`: Added `model_config=model_config` to `get_embedding_model()` call (enables rate limiting); batched re-index with progress logging; imported `EMBEDDING_BATCH_SIZE`

### Phase 2: Env Config + Provider
- `conf/model_providers.yaml`: Added `litellm_proxy` provider (maps to `litellm_provider: openai`)
- `python/helpers/memory.py`: `embedding.json` now stores+checks `model_kwargs` — dimension changes trigger re-index; uses `.get()` for backward compat

### Phase 3: Threshold Tuning
- `python/tools/memory_load.py`: `DEFAULT_THRESHOLD` configurable via `A0_SET_MEMORY_LOAD_THRESHOLD` (default 0.55)
- `python/helpers/document_query.py`: `DEFAULT_SEARCH_THRESHOLD` configurable via `A0_SET_DOCUMENT_SEARCH_THRESHOLD` (default 0.35)
- `python/helpers/memory_consolidation.py`: `replace_similarity_threshold` configurable via `A0_SET_CONSOLIDATION_REPLACE_THRESHOLD` (default 0.75)

### Phase 4: Preload Optimization
- `preload.py`: All embedding providers validated at startup (not just HuggingFace)

### Phase 5: Lazy Import
- `models.py`: `sentence_transformers` import moved from top-level to inside `LocalSentenceTransformerWrapper.__init__`

## Configuration (.env)
```bash
# LiteLLM Proxy path (recommended):
A0_SET_EMBED_MODEL_PROVIDER=litellm_proxy
A0_SET_EMBED_MODEL_NAME=text-embedding-3-small
A0_SET_EMBED_MODEL_API_BASE=https://your-proxy/v1
API_KEY_LITELLM_PROXY=your-key
A0_SET_EMBED_MODEL_KWARGS={"dimensions": 1536}

# Thresholds (optional tuning):
A0_SET_MEMORY_RECALL_SIMILARITY_THRESHOLD=0.55
A0_SET_MEMORY_MEMORIZE_REPLACE_THRESHOLD=0.75
A0_SET_MEMORY_LOAD_THRESHOLD=0.55
A0_SET_DOCUMENT_SEARCH_THRESHOLD=0.35
A0_SET_CONSOLIDATION_REPLACE_THRESHOLD=0.75
```

## Key Design Decisions
- Client sends standard OpenAI-format requests; proxy handles Azure-specific routing (api_version, deployment names)
- `dimensions` passes through as standard OpenAI API parameter
- Env-var thresholds evaluate at module import time → require server restart
- Consolidation `similarity_threshold` driven by `A0_SET_MEMORY_LOAD_THRESHOLD` (callers override ConsolidationConfig default)
- Batch size 16 is conservative for Azure OpenAI compatibility

## Plan Documentation
- Full plan: `.scratchpad/embedding-plan/` (8 files)
- Bot42 review: `.scratchpad/embedding-plan-review.md`
