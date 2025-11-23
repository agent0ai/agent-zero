import asyncio
import uuid
from typing import Any, List, Sequence
from simpleeval import simple_eval

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

    def _to_uuid(self, id_str: str) -> str:
        """Convert any string ID to a deterministic UUID."""
        try:
            # If it's already a valid UUID, return it
            uuid.UUID(str(id_str))
            return str(id_str)
        except ValueError:
            # Otherwise, hash it to a UUID
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_str)))

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
        
        # Create payload indexes for searchable keys
        for key in self.searchable_payload_keys:
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name=key,
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass # Index might already exist

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
            # Store original ID in payload for reference
            payload["original_id"] = str(pid)
            # Use UUID for Qdrant point ID
            point_id = self._to_uuid(pid)
            payload["id"] = point_id
            
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=payload,
                )
            )

        await self.client.upsert(collection_name=self.collection, points=points)
        return ids

    def _parse_filter(self, filter_str: str | None):
        if not filter_str or not qmodels:
            return None
        
        try:
            # Simple parser for "key == 'value'" or "key == 'value' or key == 'value2'"
            conditions = []
            parts = filter_str.split(" or ")
            
            for part in parts:
                if "==" not in part:
                    return None # Complex filter, fallback to Python
                
                key, val = part.split("==", 1)
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                
                conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=val)
                    )
                )
            
            if not conditions:
                return None
                
            return qmodels.Filter(should=conditions)
            
        except Exception:
            return None

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
        
        q_filter = None
        if isinstance(filter, str):
            q_filter = self._parse_filter(filter)
            
        # If we fallback to python filtering, we need to fetch more results
        limit = k
        if filter and not q_filter:
            limit = k * 10

        res = await self.client.search(
            collection_name=self.collection,
            query_vector=qvec,
            limit=limit,
            score_threshold=score_threshold,
            with_vectors=False,
            query_filter=q_filter,
            # query_filter=None,  # placeholder until we add filter parsing
        )
        docs: List[Document] = []
        for point in res:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            # Restore original ID if present, else use point ID
            payload["id"] = payload.get("original_id", str(point.id))
            docs.append(Document(page_content=text, metadata=payload))
            
        # Fallback to python filtering if q_filter was not possible but filter exists
        if filter and not q_filter:
            if callable(filter):
                docs = [d for d in docs if filter(d.metadata)]
            elif isinstance(filter, str):
                 # Try to evaluate string filter
                 try:
                     docs = [d for d in docs if simple_eval(filter, names=d.metadata)]
                 except Exception:
                     pass # Failed to evaluate, return all (or empty? usually better to return all than crash, but might be wrong)

        return docs[:k]

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
                payload["id"] = payload.get("original_id", str(point.id))
                collected.append(Document(page_content=text, metadata=payload))
            if scroll is None or not res:
                break
        return collected

    async def adelete(self, ids: Sequence[str]):
        await self._ensure_collection()
        # Convert IDs to UUIDs
        points = qmodels.PointIdsList(points=[self._to_uuid(i) for i in ids])
        await self.client.delete(collection_name=self.collection, points_selector=points)

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        await self._ensure_collection()
        res = await self.client.retrieve(
            collection_name=self.collection,
            ids=[self._to_uuid(i) for i in ids],
            with_vectors=False,
        )
        docs: List[Document] = []
        for point in res:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            payload["id"] = payload.get("original_id", str(point.id))
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
