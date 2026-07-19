# vector_db.py DOX

## Purpose

- Own the `vector_db.py` helper module.
- This module wraps FAISS vector storage, retrieval, and comparator behavior.
- Keep this file-level DOX profile synchronized with `vector_db.py` because this directory is intentionally flat.

## Ownership

- `vector_db.py` owns the runtime implementation.
- `vector_db.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `MyFaiss` (`FAISS`)
  - `get_by_ids(self, ids: Sequence[str]) -> List[Document]`
  - `async aget_by_ids(self, ids: Sequence[str]) -> List[Document]`
  - `get_all_docs(self) -> dict[str, Document]`
- `VectorDB` (no explicit base class)
  - `async search_by_similarity_threshold(self, query: str, limit: int, threshold: float, filter: str=...)`
  - `async search_by_metadata(self, filter: str, limit: int=...) -> list[Document]`
  - `async insert_documents(self, docs: list[Document])`
  - `async delete_documents_by_ids(self, ids: list[str])`
- Top-level functions:
- `format_docs_plain(docs: list[Document]) -> list[str]`
- `cosine_normalizer(val: float) -> float`
- `get_comparator(condition: str)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion.
- Imported dependency areas include: `agent`, `faiss`, `helpers`, `langchain.embeddings`, `langchain.storage`, `langchain_community.docstore.in_memory`, `langchain_community.vectorstores`, `langchain_community.vectorstores.utils`, `langchain_core.documents`, `simpleeval`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.get_by_ids`, `agent.get_embedding_model`, `self._get_embeddings`, `faiss.IndexFlatIP`, `MyFaiss`, `get_comparator`, `self.db.get_all_docs`, `InMemoryByteStore`, `CacheBackedEmbeddings.from_bytes_store`, `self.db.asearch`, `comparator`, `guids.generate_id`, `zip`, `self.db.add_documents`, `self.db.aget_by_ids`, `simple_eval`, `self.embeddings.embed_query`, `InMemoryDocstore`, `self.db.adelete`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
