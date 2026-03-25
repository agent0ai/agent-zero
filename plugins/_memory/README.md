# Memory

Provide persistent vector-based memory and knowledge retrieval for Agent Zero.

## What It Does

This plugin stores memories and knowledge embeddings in a FAISS-backed vector database, exposes tools for saving and recalling memories, and provides APIs and UI support for browsing, importing, updating, and deleting memory entries.

## Main Behavior

- **Persistent vector store**
  - Creates and loads FAISS indexes per memory subdirectory.
  - Stores embedding metadata so the index can be rebuilt if the embedding model changes.
- **Knowledge preloading**
  - Loads configured knowledge directories into memory when a database is initialized.
- **Memory tools**
  - Includes tools for saving, loading, deleting, forgetting, and behavior adjustment workflows.
- **Dashboard APIs**
  - Exposes search, delete, bulk delete, update, and subdirectory listing endpoints for the memory dashboard.
- **Scoped storage**
  - Supports different memory subdirectories so memory can be separated by context or agent scope.
- **AutoDream durable memory**
  - Periodically performs a reflective background pass over recent sessions and recent memory fragments.
  - Maintains a compact `MEMORY.md` index plus durable markdown memory files under each memory subdirectory.
  - Feeds the dream with both fresh vector memories and semantically related older vector memories so consolidation has better historical context.
  - Writes a lightweight `.dream-log.md` changelog for fast auditing of what each run created, updated, pruned, or flagged.
  - Re-imports durable memory files into vector memory with frontmatter metadata preserved, so recall benefits from the consolidated output without embedding raw YAML headers.

## Claude Code `MEMORY.md` Integration

Agent Zero's AutoDream intentionally follows the same broad pattern as Claude Code's `MEMORY.md`, but it does so per memory scope instead of assuming one global file.

- **Scoped index, not a dump**
  - Each memory scope gets its own `autodream/MEMORY.md`.
  - That file is a compact index of durable memories, not the memories themselves.
- **Durable files hold the actual content**
  - The detailed memories live in `autodream/memories/*.md`.
  - `MEMORY.md` links to those files with one-line descriptions.
- **Vector DB stays in sync**
  - Those durable markdown files are re-imported into the FAISS-backed vector store.
  - This means Agent Zero's semantic recall and the Claude-style `MEMORY.md` index are two synchronized views over the same durable memory set.
- **Compatibility model**
  - If you already use Claude Code, the generated `MEMORY.md` should feel familiar.
  - The main difference is placement: Agent Zero manages `MEMORY.md` inside each memory scope or project metadata folder rather than at a single repository root.
  - If another tool expects a root-level `MEMORY.md`, you can mirror or sync the generated index there, but Agent Zero's native source of truth remains the scoped AutoDream folder.

## Key Files

- **Core memory engine**
  - `helpers/memory.py` implements FAISS storage, index loading, embedding configuration, and knowledge preload.
- **Knowledge import**
  - `helpers/knowledge_import.py` imports external knowledge into memory storage.
- **Consolidation**
  - `helpers/memory_consolidation.py` contains memory consolidation logic.
- **AutoDream**
  - `helpers/auto_dream.py` contains session gathering, durable file generation, and background scheduling logic.
- **Tools**
  - `tools/memory_save.py`
  - `tools/memory_load.py`
  - `tools/memory_delete.py`
  - `tools/memory_forget.py`
  - `tools/behaviour_adjustment.py`
- **API**
  - `api/memory_dashboard.py` powers the memory management dashboard.
  - `api/import_knowledge.py` and `api/knowledge_reindex.py` handle knowledge import and reindexing.
- **Lifecycle**
  - `extensions/python/process_chain_end/_60_auto_dream.py` schedules periodic AutoDream runs after top-level chats complete.

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`

## Plugin Metadata

- **Name**: `_memory`
- **Title**: `Memory`
- **Description**: Provides persistent memory capabilities to Agent Zero agents.
