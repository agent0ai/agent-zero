"""Document fetching, sandbox parsing and indexing with bounded timeouts."""

import asyncio
import base64
import hashlib
from pathlib import Path
import tempfile
import json
import mimetypes
import threading
from datetime import datetime
from typing import Any, Callable, List, Sequence, Tuple
from urllib.parse import quote, unquote, urlparse

from langchain_core.messages import SystemMessage, HumanMessage
import numpy as np
from langchain_core.documents import Document

from helpers import files, errors
from helpers.print_style import PrintStyle
from helpers.sandbox import SandboxMount
from agent import Agent

from plugins._document_query.helpers.fetch import FetchedDocument, fetch_public_resource
from plugins._document_query.helpers.sandbox import worker, parser_config, payload


DEFAULT_SEARCH_THRESHOLD = 0.5
DEFAULT_PARSER_CONCURRENCY = 1
SMALL_DOCUMENT_FALLBACK_MAX_CHARS = 12000
_PARSER_SEMAPHORES: dict[tuple[int, int], asyncio.Semaphore] = {}
_PARSER_SEMAPHORES_LOCK = threading.Lock()


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parser_semaphore(config: dict) -> asyncio.Semaphore:
    concurrency = _positive_int(
        config.get("parser_concurrency"),
        DEFAULT_PARSER_CONCURRENCY,
    )
    loop = asyncio.get_running_loop()
    key = (id(loop), concurrency)
    with _PARSER_SEMAPHORES_LOCK:
        semaphore = _PARSER_SEMAPHORES.get(key)
        if semaphore is None:
            semaphore = asyncio.Semaphore(concurrency)
            _PARSER_SEMAPHORES[key] = semaphore
        return semaphore


def _load_config(agent: Agent) -> dict:
    """Load plugin config with fallback to defaults."""
    from helpers.plugins import get_plugin_config
    return get_plugin_config("_document_query", agent=agent) or {}


class DocumentQueryStore:
    """FAISS Store for document query results."""

    CONTEXT_DATA_KEY = "_document_query_store"
    _GET_LOCK = threading.RLock()

    @classmethod
    def get(cls, agent: Agent):
        if not agent or not agent.config:
            raise ValueError("Agent and agent config must be provided")

        context = getattr(agent, "context", None)
        if context is None:
            return cls(agent)

        with cls._GET_LOCK:
            store = context.get_data(cls.CONTEXT_DATA_KEY, recursive=False)
            if not isinstance(store, cls):
                store = cls(agent)
                context.set_data(cls.CONTEXT_DATA_KEY, store, recursive=False)
            else:
                store.agent = agent
                store.config = _load_config(agent)
            return store

    def __init__(self, agent: Agent):
        self.agent = agent
        self.config = _load_config(agent)
        self._directory = tempfile.TemporaryDirectory(prefix="a0-doc-query-")
        self.index_mount = SandboxMount(Path(self._directory.name), "/index", read_only=False)
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = self.agent.get_embedding_model()
        return self._model

    def settings(self):
        config, mounts = parser_config(self.config)
        return config, [self.index_mount, *mounts]

    async def _call(self, operation, **fields):
        _, mounts = self.settings()
        return await worker.acall({"operation": operation, **fields}, mounts=mounts)

    @staticmethod
    def normalize_uri(uri: str) -> str:
        normalized = uri.strip()
        parsed = urlparse(normalized)
        scheme = parsed.scheme or "file"
        if scheme == "file":
            path = files.fix_dev_path(
                normalized.removeprefix("file://").removeprefix("file:")
            )
            normalized = f"file://{path}"
        elif scheme in ["http", "https"]:
            normalized = normalized.replace("http://", "https://")
        return normalized

    async def add_document(self, text: str, document_uri: str, metadata: dict | None = None):
        uri = self.normalize_uri(document_uri)
        try:
            config, _ = self.settings()
            chunks = await self._call("split", text=text, config=config)
            if not chunks:
                return False, []
            vectors = np.asarray(await self.model.aembed_documents(chunks), dtype="<f4")
            if vectors.ndim != 2 or len(vectors) != len(chunks) or not np.isfinite(vectors).all():
                raise ValueError("Invalid document embeddings")
            ids = await self._call(
                "put", uri=uri, chunks=chunks, dimension=vectors.shape[1],
                vectors=base64.b64encode(vectors.tobytes()).decode("ascii"),
                metadata={**(metadata or {}), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            )
            return True, ids
        except Exception as exc:
            PrintStyle.error(f"Error indexing {uri}: {errors.format_error(exc)}")
            return False, []

    async def get_document(self, document_uri: str) -> Document | None:
        chunks = await self._get_document_chunks(document_uri)
        if not chunks:
            return None
        metadata = {k: v for k, v in chunks[0].metadata.items() if k not in {"chunk_index", "total_chunks"}}
        return Document(page_content="\n".join(doc.page_content for doc in chunks), metadata=metadata)

    async def _get_document_chunks(self, document_uri: str) -> list[Document]:
        rows = await self._call("chunks", uri=self.normalize_uri(document_uri))
        return [Document(**row) for row in rows]

    async def document_exists(self, document_uri: str) -> bool:
        return await self._call("exists", uri=self.normalize_uri(document_uri))

    async def delete_document(self, document_uri: str) -> bool:
        return await self._call("delete", uri=self.normalize_uri(document_uri))

    async def search_documents(self, query: str, limit=10, threshold=0.5, filter="", *, uris=None):
        if not query or limit <= 0:
            return []
        try:
            vector = await self.model.aembed_query(query)
            rows = await self._call("search", vector=vector, limit=limit, threshold=threshold, filter=filter, uris=uris)
            return [Document(**row) for row in rows]
        except Exception as exc:
            PrintStyle.error(f"Error searching documents: {exc}")
            return []

    async def search_document(self, document_uri: str, query: str, limit=10, threshold=0.5):
        return await self.search_documents(query, limit, threshold, uris=[self.normalize_uri(document_uri)])

    async def list_documents(self) -> list[str]:
        return await self._call("list")


class DocumentQueryHelper:

    def __init__(
        self,
        agent: Agent,
        progress_callback: Callable[[str], None] | None = None,
        stream_callback: Callable[[str], None] | None = None,
    ):
        self.agent = agent
        self.store = DocumentQueryStore.get(agent)
        self.progress_callback = progress_callback or (lambda x: None)
        self.stream_callback = stream_callback
        self.destination = "local"
        self._destination_uris: dict[str, str] = {}
        self.store_lock = asyncio.Lock()
        self.config = self.store.config

    async def document_qa(
        self, document_uris: List[str] | str, questions: Sequence[str] | str
    ) -> Tuple[bool, str]:
        if isinstance(document_uris, str):
            document_uris = [document_uris]
        if isinstance(questions, str):
            questions = [questions]
        self.progress_callback(f"Starting Q&A process for {len(document_uris)} documents")
        await self.agent.handle_intervention()

        gather_timeout = self.config.get("gather_timeout", 120)
        try:
            document_contents = await asyncio.wait_for(
                asyncio.gather(
                    *[self.document_get_content(uri, True) for uri in document_uris]
                ),
                timeout=gather_timeout,
            )
        except asyncio.TimeoutError:
            raise ValueError(f"Document indexing timed out after {gather_timeout}s")

        await self.agent.handle_intervention()
        search_threshold = self.config.get("search_threshold", DEFAULT_SEARCH_THRESHOLD)
        search_limit = self.config.get("search_limit", 100)
        selected_chunks = {}
        normalized_uris = [
            self._destination_uris.get(uri) or self.store.normalize_uri(uri)
            for uri in document_uris
        ]
        intro_chunk_count = _positive_int(
            self.config.get("context_intro_chunks"),
            2,
        )
        for uri in normalized_uris:
            for chunk in await self._get_document_intro_chunks(uri, intro_chunk_count):
                selected_chunks[chunk.metadata["id"]] = chunk

        for question in questions:
            self.progress_callback(f"Optimizing query: {question}")
            await self.agent.handle_intervention()
            system_content = self.agent.parse_prompt("fw.document_query.optimize_query.md")
            optimized_query = (
                await self.agent.call_utility_model(
                    system=system_content, message=f'Search Query: "{question}"',
                )
            ).strip()

            await self.agent.handle_intervention()
            self.progress_callback(f"Searching documents with query: {optimized_query}")
            chunks = await self.store.search_documents(
                query=optimized_query, limit=search_limit,
                threshold=search_threshold, uris=normalized_uris,
            )
            self.progress_callback(f"Found {len(chunks)} chunks")
            for chunk in chunks:
                selected_chunks[chunk.metadata["id"]] = chunk

        if not selected_chunks:
            fallback_content = self._small_document_fallback_content(
                document_uris,
                document_contents,
            )
            if fallback_content:
                self.progress_callback(
                    "No matching chunks found; using extracted document content"
                )
                ai_response = await self._answer_questions_from_content(
                    fallback_content,
                    questions,
                    "extracted document content",
                )
                self.progress_callback(f"Q&A process completed")
                return True, ai_response

            self.progress_callback("No relevant content found in the documents")
            content = f"!!! No content found for documents: {json.dumps(document_uris)} matching queries: {json.dumps(questions)}"
            return False, content

        content = "\n\n----\n\n".join(
            [chunk.page_content for chunk in selected_chunks.values()]
        )
        ai_response = await self._answer_questions_from_content(
            content,
            questions,
            f"{len(selected_chunks)} chunks",
        )
        self.progress_callback(f"Q&A process completed")
        return True, ai_response

    async def _answer_questions_from_content(
        self,
        content: str,
        questions: Sequence[str],
        context_label: str,
    ) -> str:
        self.progress_callback(
            f"Processing {len(questions)} questions in context of {context_label}"
        )
        await self.agent.handle_intervention()
        questions_str = "\n".join([f" *  {question}" for question in questions])
        qa_system_message = self.agent.parse_prompt("fw.document_query.system_prompt.md")
        qa_user_message = f"# Document:\n{content}\n\n# Queries:\n{questions_str}"
        stream_callback = getattr(self, "stream_callback", None)

        async def stream_answer(chunk: str, total: str):
            stream_callback(total)

        stream_kwargs = {"response_callback": stream_answer} if stream_callback else {}
        ai_response, _reasoning = await self.agent.call_chat_model(
            messages=[
                SystemMessage(content=qa_system_message),
                HumanMessage(content=qa_user_message),
            ],
            explicit_caching=False,
            **stream_kwargs,
        )
        return str(ai_response)

    @staticmethod
    def _small_document_fallback_content(
        document_uris: Sequence[str],
        document_contents: Sequence[str],
        max_chars: int = SMALL_DOCUMENT_FALLBACK_MAX_CHARS,
    ) -> str:
        blocks = []
        for document_uri, document_content in zip(document_uris, document_contents):
            text = (document_content or "").strip()
            if text:
                blocks.append(f"# Source: {document_uri}\n\n{text}")

        if not blocks:
            return ""

        content = "\n\n----\n\n".join(blocks)
        if len(content) > max_chars:
            return ""
        return content

    async def _get_document_intro_chunks(
        self,
        document_uri: str,
        limit: int,
    ) -> list[Document]:
        if limit <= 0:
            return []
        if not hasattr(self.store, "_get_document_chunks"):
            return []
        chunks = await self.store._get_document_chunks(document_uri)
        return sorted(chunks, key=lambda chunk: chunk.metadata.get("chunk_index", 0))[
            :limit
        ]

    async def document_get_content(
        self, document_uri: str, add_to_db: bool = False
    ) -> str:
        self.progress_callback(f"Fetching document content")
        await self.agent.handle_intervention()
        parsed = urlparse(document_uri)
        if self.destination == "local" or (parsed.scheme and parsed.scheme != "file" and len(parsed.scheme) != 1):
            document = await fetch_public_resource(
                document_uri, self.config, self.agent.handle_intervention,
            )
        else:
            from helpers import destination_files

            path = unquote(parsed.path) if parsed.scheme == "file" else document_uri
            mime, encoding = mimetypes.guess_type(path)
            if not mime or encoding:
                raise ValueError(f"Unsupported document type: {path}")
            data = await destination_files.read(
                self.agent, self.destination, path,
                limit=int(self.config.get("max_remote_bytes", 50 * 1024 * 1024)),
            )
            revision = hashlib.sha256(data).hexdigest()
            uri = f"destination-file://{quote(str(self.agent.context.id), safe='')}/{quote(self.destination, safe='')}/{revision}/{quote(path.lstrip('/'), safe='/')}"
            document = FetchedDocument(uri=uri, source_uri=document_uri, scheme="file", mimetype=mime, content=data)
            self._destination_uris[document_uri] = self.store.normalize_uri(uri)

        document_uri_norm = self.store.normalize_uri(document.uri)
        await self.agent.handle_intervention()
        exists = await self.store.document_exists(document_uri_norm)
        document_content = ""

        if not exists:
            await self.agent.handle_intervention()
            document_content = await self._parse_document(
                document, self.config.get("per_document_timeout", 60)
            )
            if add_to_db:
                self.progress_callback(f"Indexing document")
                await self.agent.handle_intervention()
                async with self.store_lock:
                    success, ids = await self.store.add_document(
                        document_content, document_uri_norm
                    )
                if not success:
                    self.progress_callback(f"Failed to index document")
                    raise ValueError(f"Failed to index document: {document_uri_norm}")
                self.progress_callback(f"Indexed {len(ids)} chunks")
        else:
            await self.agent.handle_intervention()
            doc = await self.store.get_document(document_uri_norm)
            if doc:
                document_content = doc.page_content
            else:
                raise ValueError(f"Document not found: {document_uri_norm}")
        return document_content

    async def _parse_document(self, document: FetchedDocument, timeout: float) -> str:
        async with _parser_semaphore(self.config):
            self.progress_callback("Parsing document content in sandbox")
            config, mounts = self.store.settings()
            return await worker.acall(payload(document, config), timeout=timeout, mounts=mounts)
