"""
Migrate existing FAISS memory indices into Qdrant.

Usage:
  python scripts/migrate_faiss_to_qdrant.py

Requirements:
  - Qdrant running (see docker/run/docker-compose.qdrant.yml)
  - qdrant-client installed (in requirements.txt)
"""

import asyncio
import os
from typing import List

from langchain_core.documents import Document

import models
from python.helpers import files
from python.helpers.memory import Memory, abs_db_dir
from python.helpers.memory_config import reset_memory_config


async def migrate_subdir(memory_subdir: str):
    # Force FAISS for reading
    os.environ["A0_MEMORY_BACKEND"] = "faiss"
    reset_memory_config()
    src = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
    docs = list(src.db.get_all_docs().values())

    # Prepare Qdrant target
    os.environ["A0_MEMORY_BACKEND"] = "qdrant"
    reset_memory_config()
    # re-initialize for qdrant
    tgt = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

    if not docs:
        print(f"[skip] {memory_subdir}: no docs found.")
        return

    # Insert preserving metadata
    await tgt.insert_documents(docs)
    print(f"[done] {memory_subdir}: migrated {len(docs)} docs.")


async def main():
    # discover subdirs (excluding embeddings)
    subdirs = files.get_subdirectories("memory", exclude="embeddings")
    # also include project memory folders if present
    for sub in list(subdirs):
        if sub.startswith("projects/"):
            continue
    for subdir in subdirs:
        # ensure FAISS index exists
        if not files.exists(abs_db_dir(subdir), "index.faiss"):
            continue
        await migrate_subdir(subdir)


if __name__ == "__main__":
    asyncio.run(main())
