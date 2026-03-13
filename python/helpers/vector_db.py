from typing import Any, List, Sequence

from langchain_core.documents import Document
from simpleeval import simple_eval

from agent import Agent
from python.helpers import guids
from python.helpers.cognee_init import configure_cognee


class VectorDB:

    _session_counter: int = 0

    def __init__(self, agent: Agent, cache: bool = True):
        self.agent = agent
        self._docs: dict[str, Document] = {}
        VectorDB._session_counter += 1
        self._dataset_name = f"docquery_{guids.generate_id(6)}_{VectorDB._session_counter}"
        self._cognee_initialized = False

    def _ensure_cognee(self):
        if not self._cognee_initialized:
            configure_cognee()
            self._cognee_initialized = True

    def get_all_docs(self) -> dict[str, Document]:
        return self._docs

    async def search_by_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str = ""
    ):
        self._ensure_cognee()
        from python.helpers.memory import _get_cognee
        cognee, SearchType = _get_cognee()

        comparator = get_comparator(filter) if filter else None

        try:
            results = await cognee.search(
                query_text=query,
                query_type=SearchType.CHUNKS,
                top_k=limit * 3,
                datasets=[self._dataset_name],
            )
        except Exception:
            return []

        docs = []
        if not results:
            return docs

        for result in results:
            if len(docs) >= limit:
                break

            raw = result
            if hasattr(result, "search_result"):
                raw = result.search_result

            content = str(raw) if not isinstance(raw, str) else raw
            if content.startswith("[DOCMETA:"):
                try:
                    meta_end = content.index("]\n")
                    import json
                    metadata = json.loads(content[9:meta_end])
                    content = content[meta_end + 2:]
                except (ValueError, Exception):
                    metadata = {}
            else:
                metadata = {}

            if comparator and not comparator(metadata):
                continue

            doc = Document(page_content=content, metadata=metadata)
            docs.append(doc)

        return docs

    async def search_by_metadata(self, filter: str, limit: int = 0) -> list[Document]:
        comparator = get_comparator(filter)
        result = []
        for doc in self._docs.values():
            if comparator(doc.metadata):
                result.append(doc)
                if limit > 0 and len(result) >= limit:
                    break
        return result

    async def insert_documents(self, docs: list[Document]):
        self._ensure_cognee()
        from python.helpers.memory import _get_cognee
        cognee, _ = _get_cognee()

        ids = [guids.generate_id() for _ in range(len(docs))]
        import json

        for doc, doc_id in zip(docs, ids):
            doc.metadata["id"] = doc_id
            self._docs[doc_id] = doc

            meta_header = json.dumps(doc.metadata, default=str)
            enriched = f"[DOCMETA:{meta_header}]\n{doc.page_content}"

            try:
                await cognee.add(
                    enriched,
                    dataset_name=self._dataset_name,
                )
            except Exception:
                pass

        return ids

    async def delete_documents_by_ids(self, ids: list[str]):
        rem_docs = [self._docs[doc_id] for doc_id in ids if doc_id in self._docs]
        for doc_id in ids:
            self._docs.pop(doc_id, None)
        return rem_docs


def format_docs_plain(docs: list[Document]) -> list[str]:
    result = []
    for doc in docs:
        text = ""
        for k, v in doc.metadata.items():
            text += f"{k}: {v}\n"
        text += f"Content: {doc.page_content}"
        result.append(text)
    return result


def get_comparator(condition: str):
    def comparator(data: dict[str, Any]):
        try:
            result = simple_eval(condition, names=data)
            return result
        except Exception:
            return False

    return comparator
