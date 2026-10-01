from __future__ import annotations

import sys
import asyncio
from pathlib import Path

from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._memory.helpers.memory import Memory


class FakeFaiss:
    def __init__(self, docs: list[Document]):
        self.docs = {doc.metadata["id"]: doc for doc in docs}
        self.deleted: list[str] = []

    async def asearch(self, *_args, **_kwargs):
        return []

    async def adelete(self, ids):
        for doc_id in ids:
            self.deleted.append(doc_id)
            self.docs.pop(doc_id, None)

    async def aget_by_ids(self, ids):
        return [self.docs[doc_id] for doc_id in ids if doc_id in self.docs]

    def get_all_docs(self):
        return self.docs

    def get_by_ids(self, ids):
        return [self.docs[doc_id] for doc_id in ids if doc_id in self.docs]


class FakeEmbeddings:
    def __init__(self):
        self.queries: list[str] = []

    async def aembed_query(self, query: str):
        self.queries.append(query)
        return [0.25, 0.75]


class FakeVectorSearch:
    def __init__(self):
        self.embedding_function = FakeEmbeddings()
        self.docs = [
            (Document(page_content="main", metadata={"area": "main"}), 0.8),
            (Document(page_content="solution", metadata={"area": "solutions"}), 0.7),
            (Document(page_content="weak", metadata={"area": "main"}), 0.2),
        ]
        self.embeddings: list[list[float]] = []

    async def asimilarity_search_with_score_by_vector(
        self, embedding, *, k, filter
    ):
        self.embeddings.append(embedding)
        return [(doc, score) for doc, score in self.docs if filter(doc.metadata)][:k]


def test_memory_forget_removes_exact_matches_and_derived_fragments():
    main = Document(
        page_content="User currently prefers memory cleanup token banana-397.",
        metadata={"id": "main-1", "area": "main"},
    )
    fragment = Document(
        page_content="Derived note from old preference.",
        metadata={
            "id": "fragment-1",
            "area": "fragments",
            "consolidated_from": ["main-1"],
        },
    )
    unrelated = Document(
        page_content="Unrelated memory about project setup.",
        metadata={"id": "other-1", "area": "main"},
    )
    fake_db = FakeFaiss([main, fragment, unrelated])
    memory = Memory(fake_db, memory_subdir="test")
    memory._save_db = lambda: None

    removed = asyncio.run(
        memory.delete_documents_by_query(
            query="banana-397",
            threshold=0.99,
            include_exact=True,
            cascade=True,
        )
    )

    assert {doc.metadata["id"] for doc in removed} == {"main-1", "fragment-1"}
    assert fake_db.deleted == ["main-1", "fragment-1"]
    assert set(fake_db.docs) == {"other-1"}


def test_memory_delete_cascades_even_when_original_id_is_already_missing():
    replacement = Document(
        page_content="User currently prefers concise technical answers.",
        metadata={
            "id": "replacement-1",
            "area": "main",
            "updated_from": "old-pref-1",
        },
    )
    fake_db = FakeFaiss([replacement])
    memory = Memory(fake_db, memory_subdir="test")
    memory._save_db = lambda: None

    removed = asyncio.run(
        memory.delete_documents_by_ids(["old-pref-1"], cascade=True)
    )

    assert [doc.metadata["id"] for doc in removed] == ["replacement-1"]
    assert fake_db.deleted == ["replacement-1"]
    assert fake_db.docs == {}


def test_memory_reuses_one_query_embedding_across_filtered_searches():
    fake_db = FakeVectorSearch()
    memory = Memory(fake_db, memory_subdir="test")

    async def search():
        embedding = await memory.embed_query("shared recall query")
        memories = await memory.search_similarity_threshold(
            query="shared recall query",
            limit=12,
            threshold=0.7,
            filter="area == 'main'",
            embedding=embedding,
        )
        solutions = await memory.search_similarity_threshold(
            query="shared recall query",
            limit=8,
            threshold=0.7,
            filter="area == 'solutions'",
            embedding=embedding,
        )
        return memories, solutions

    memories, solutions = asyncio.run(search())

    assert fake_db.embedding_function.queries == ["shared recall query"]
    assert fake_db.embeddings == [[0.25, 0.75], [0.25, 0.75]]
    assert [doc.page_content for doc in memories] == ["main"]
    assert [doc.page_content for doc in solutions] == ["solution"]
