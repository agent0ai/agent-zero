import asyncio
from typing import Any, List, Sequence

from langchain_core.documents import Document


try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client import models as qmodels
except Exception:  # pragma: no cover - keep import-safe when qdrant is missing
    AsyncQdrantClient = None  # type: ignore
    qmodels = None  # type: ignore


class QdrantStore:
    """
    Minimal async wrapper around Qdrant that mirrors the FAISS interface used in Memory.
    """

    is_qdrant = True

    def __init__(
        self,
        embedder,
        collection: str,
        url: str,
        api_key: str = "",
        prefer_hybrid: bool = True,
        score_threshold: float = 0.6,
        limit: int = 20,
        timeout: int = 10,
        searchable_payload_keys: list[str] | None = None,
    ):
        if AsyncQdrantClient is None:
            raise RuntimeError(
                "qdrant-client is not installed. Add it to requirements to use Qdrant backend."
            )

        self.embedder = embedder
        self.client = AsyncQdrantClient(url=url, api_key=api_key or None, timeout=timeout)
        self.collection = collection
        self.prefer_hybrid = prefer_hybrid
        self.score_threshold = score_threshold
        self.limit = limit
        self.searchable_payload_keys = searchable_payload_keys or []
        self._collection_ready = False

    async def _ensure_collection(self):
        if self._collection_ready:
            return

        dim = len(await asyncio.to_thread(self.embedder.embed_query, "example"))
        try:
            await self.client.get_collection(self.collection)
        except Exception:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(
                    size=dim, distance=qmodels.Distance.COSINE
                ),
            )
        self._collection_ready = True

    async def aadd_documents(self, documents: list[Document], ids: Sequence[str]):
        await self._ensure_collection()
        vectors = await asyncio.to_thread(
            self.embedder.embed_documents, [d.page_content for d in documents]
        )

        points = []
        for doc, vec, pid in zip(documents, vectors, ids):
            payload = dict(doc.metadata or {})
            payload["text"] = doc.page_content
            payload["id"] = str(pid)
            points.append(
                qmodels.PointStruct(
                    id=str(pid),
                    vector=vec,
                    payload=payload,
                )
            )

        await self.client.upsert(collection_name=self.collection, points=points)
        return ids

    async def asearch(
        self,
        query: str,
        search_type: str = "similarity_score_threshold",
        k: int = 10,
        score_threshold: float | None = None,
        filter=None,
    ):
        await self._ensure_collection()
        qvec = await asyncio.to_thread(self.embedder.embed_query, query)
        res = await self.client.search(
            collection_name=self.collection,
            query_vector=qvec,
            limit=k,
            score_threshold=score_threshold,
            with_vectors=False,
            query_filter=None,  # placeholder until we add filter parsing
        )
        docs: List[Document] = []
        for point in res:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            payload["id"] = str(point.id)
            docs.append(Document(page_content=text, metadata=payload))
        if callable(filter):
            docs = [d for d in docs if filter(d.metadata)]
        return docs

    async def aget_all_docs(self, page_size: int = 256, limit: int = 1000) -> List[Document]:
        """Lightweight scroll to fetch up to `limit` docs for stats/migrations."""
        await self._ensure_collection()
        collected: List[Document] = []
        scroll = None
        while len(collected) < limit:
            res, scroll = await self.client.scroll(
                collection_name=self.collection,
                limit=min(page_size, limit - len(collected)),
                with_vectors=False,
                offset=scroll,
            )
            for point in res:
                payload = dict(point.payload or {})
                text = payload.pop("text", "")
                payload["id"] = str(point.id)
                collected.append(Document(page_content=text, metadata=payload))
            if scroll is None or not res:
                break
        return collected

    async def adelete(self, ids: Sequence[str]):
        await self._ensure_collection()
        points = qmodels.PointIdsList(points=[str(i) for i in ids])
        await self.client.delete(collection_name=self.collection, points_selector=points)

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        await self._ensure_collection()
        res = await self.client.retrieve(
            collection_name=self.collection,
            ids=[str(i) for i in ids],
            with_vectors=False,
        )
        docs: List[Document] = []
        for point in res:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            payload["id"] = str(point.id)
            docs.append(Document(page_content=text, metadata=payload))
        return docs

    # sync compatibility helpers -------------------------------------------------
    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return []
        return loop.run_until_complete(self.aget_by_ids(ids))

    def get_all_docs(self):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return {}
        try:
            docs = loop.run_until_complete(self.aget_all_docs())
            return {d.metadata.get("id"): d for d in docs if d.metadata.get("id")}
        except Exception:
            return {}

    def save_local(self, *args, **kwargs):
        # FAISS compatibility hook – nothing to persist locally.
        return None
