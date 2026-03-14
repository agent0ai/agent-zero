---
name: digital-clone-aggregator
description: Build and operate an Agent Jumbo profile that acts as a knowledge aggregator and digital clone of a solution architect, including multi-source ingestion, vector memory + database storage, tech/news/business briefs, and Telegram delivery. Use when asked to set up, evolve, or troubleshoot Agent Jumbo as a personal knowledge hub, architecture advisor, or always-on news/technology/business digest.
---

# Digital Clone Aggregator

## Core workflow

1. Confirm objectives, cadence, and priority domains (architecture, tech, business).
2. Choose an ingestion architecture from `references/architecture-options.md`.
3. Follow the phased implementation plan in `references/implementation-plan.md`.
4. Use the templates in `references/templates.md` to shape digests, alerts, and architecture reviews.
5. Store long-term knowledge in `knowledge/` and concise facts/decisions in `memory/`.

## Implementation guardrails

- Prefer Agent Jumbo native features: memory (FAISS), knowledge (RAG), workflow_engine, instruments, and MCP servers.
- Keep ingestion deterministic: log source, timestamp, topic, and confidence per item.
- Separate source facts from synthesis to avoid hallucinations in long-term memory.
- Telegram delivery must be summarized, actionable, and include source links.

## When extending

- Add new sources as MCP servers or instruments, not ad-hoc scripts.
- Add structured schemas for any new DB tables or vector metadata.
- Add tests for new instruments or tools under `tests/`.
