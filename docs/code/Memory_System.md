---
tags: [component, memory, storage]
---

# Memory System

Agent Zero uses a hybrid memory system.

## Types

1.  **Fragments**: Small pieces of info.
2.  **Solutions**: Saved successful workflows.
3.  **Vector DB**: For semantic search (using ChromaDB/etc).

## Location

- `memory/` directory stores the persistent data.
- `python/helpers/memory.py` (likely) manages the logic.

## Relations

- [[Agent Core]] reads/writes memory during the loop.
- [[Prompts System]] injects memory into context.

