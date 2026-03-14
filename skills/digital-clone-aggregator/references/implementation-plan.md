# Implementation Plan (Hybrid)

## Phase 0: Baseline configuration

- Enable memory/knowledge in `.env` and confirm `memory/` and `knowledge/` paths.
- Add MCP servers for: filesystem, fetch, brave-search, memory, and sqlite/postgres.
- Create an agent profile `agents/digital-clone/` with tailored prompts for architecture review and digest tone.

## Phase 1: Storage and data model

- Use FAISS memory for short-form facts, decisions, and preferences.
- Use `knowledge/` for long-form source material and curated briefs.
- Add a lightweight SQLite DB for source registry, ingestion logs, and digest history:
  - `sources(id, name, type, uri, tags, cadence)`
  - `ingestions(id, source_id, fetched_at, status, item_count)`
  - `items(id, source_id, title, url, published_at, content_hash, tags, confidence)`
  - `digests(id, created_at, window_start, window_end, summary, channels)`

## Phase 2: Ingestion pipelines

- Implement a `knowledge_ingest` instrument to:
  - Pull from RSS, web pages, GitHub, email, and documents.
  - Normalize text and dedupe by `content_hash`.
  - Save raw facts into `knowledge/` and metadata into SQLite.
- Use MCP fetch for web pages and brave-search for discovery.
- Add a scheduled trigger (cron or systemd) that calls Agent Jumbo `/api_message` to run ingestion workflows.

## Phase 3: Summarization and memory consolidation

- Add a `digest_builder` instrument to:
  - Summarize by domain (architecture, tech, business).
  - Create weekly and daily digests.
  - Store summaries in `knowledge/` and decisions in `memory/`.
- Add consolidation prompts to avoid duplicates and bias.

## Phase 4: Telegram delivery

- Create a `telegram_send` tool or instrument that:
  - Posts digests and alerts to a configured Telegram chat ID.
  - Includes links, tags, and action prompts.
- Add guardrails for message length and rate limits.

## Phase 5: Architecture decision support

- Add an `architecture_review` workflow that:
  - Ingests a problem brief
  - Generates 2-3 options with tradeoffs
  - Produces a final recommendation and an ADR-style summary

## Phase 6: Tests and validation

- Unit tests for instruments using `tests/_test_template.py`.
- E2E test for ingestion -> digest -> telegram pipeline using mock sources.
- Add `scripts/run-ci-local.sh test` to CI smoke check.
