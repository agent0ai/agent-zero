import asyncio
import json
import os
from pathlib import Path
import re
from typing import Any

from helpers import guids
from helpers.print_style import PrintStyle
from helpers import files, plugins, projects
from helpers.localization import Localization
from langchain_core.documents import Document
from . import knowledge_import
from helpers.log import LogItem
from .native_store import NativeStore
from enum import Enum
from agent import Agent, AgentContext
import models
from simpleeval import simple_eval


class Memory:

    class Area(Enum):
        MAIN = "main"
        FRAGMENTS = "fragments"
        SOLUTIONS = "solutions"

    index: dict[str, "NativeStore"] = {}

    @staticmethod
    def _get_embedding_config(agent=None):
        from plugins._model_config.helpers.model_config import get_embedding_model_config_object
        return get_embedding_model_config_object(agent)

    @staticmethod
    async def get(agent: Agent):
        memory_subdir = get_agent_memory_subdir(agent)
        if Memory.index.get(memory_subdir) is None:
            log_item = agent.context.log.log(
                type="util",
                heading=f"Initializing VectorDB in '/{memory_subdir}'",
            )
            db, created = Memory.initialize(
                log_item,
                Memory._get_embedding_config(agent),
                memory_subdir,
                False,
            )
            Memory.index[memory_subdir] = db
            wrap = Memory(db, memory_subdir=memory_subdir)
            knowledge_subdirs = get_knowledge_subdirs_by_memory_subdir(
                memory_subdir, agent.config.knowledge_subdirs or []
            )
            if knowledge_subdirs:
                await wrap.preload_knowledge(log_item, knowledge_subdirs, memory_subdir)
            return wrap
        else:
            return Memory(
                db=Memory.index[memory_subdir],
                memory_subdir=memory_subdir,
            )

    @staticmethod
    async def get_by_subdir(
        memory_subdir: str,
        log_item: LogItem | None = None,
        preload_knowledge: bool = True,
    ):
        if not Memory.index.get(memory_subdir):
            import initialize

            agent_config = initialize.initialize_agent()
            model_config = Memory._get_embedding_config()
            db, _created = Memory.initialize(
                log_item=log_item,
                model_config=model_config,
                memory_subdir=memory_subdir,
                in_memory=False,
            )
            wrap = Memory(db, memory_subdir=memory_subdir)
            if preload_knowledge:
                knowledge_subdirs = get_knowledge_subdirs_by_memory_subdir(
                    memory_subdir, agent_config.knowledge_subdirs or []
                )
                if knowledge_subdirs:
                    await wrap.preload_knowledge(
                        log_item, knowledge_subdirs, memory_subdir
                    )
            Memory.index[memory_subdir] = db
        return Memory(db=Memory.index[memory_subdir], memory_subdir=memory_subdir)

    @staticmethod
    async def reload(agent: Agent):
        memory_subdir = get_agent_memory_subdir(agent)
        if Memory.index.get(memory_subdir):
            del Memory.index[memory_subdir]
        return await Memory.get(agent)

    @staticmethod
    def initialize(
        log_item: LogItem | None,
        model_config: models.ModelConfig,
        memory_subdir: str,
        in_memory=False,
    ) -> tuple[NativeStore, bool]:

        PrintStyle.standard("Initializing VectorDB...")

        if log_item:
            log_item.stream(progress="\nInitializing VectorDB")

        model = models.get_embedding_model(model_config.provider, model_config.name, **model_config.build_kwargs())
        identity = [model_config.provider, model_config.name]
        cache = None if in_memory else files.get_abs_path("tmp/memory/embeddings")
        db = NativeStore(abs_db_dir(memory_subdir), model, identity, files.safe_file_name("_".join(identity)), cache)
        return db, db.initialize()

    def __init__(
        self,
        db: NativeStore,
        memory_subdir: str,
    ):
        self.db = db
        self.memory_subdir = memory_subdir

    async def preload_knowledge(
        self, log_item: LogItem | None, kn_dirs: list[str], memory_subdir: str
    ):
        if log_item:
            log_item.update(heading="Preloading knowledge...")

        # db abs path
        db_dir = abs_db_dir(memory_subdir)

        # Load the index file if it exists
        index_path = files.get_abs_path(db_dir, "knowledge_import.json")

        # make sure directory exists
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        index: dict[str, knowledge_import.KnowledgeImport] = {}
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                index = json.load(f)

        # preload knowledge folders
        index = await asyncio.to_thread(self._preload_knowledge_folders, log_item, kn_dirs, index)

        for record in index.values():
            if record["state"] == "changed":
                record["ids"] = await self.insert_documents(record["documents"], delete_ids=record.get("ids", []))
            elif record["state"] == "removed" and record.get("ids"):
                await self.delete_documents_by_ids(record["ids"])

        # remove index where state="removed"
        index = {k: v for k, v in index.items() if v["state"] != "removed"}

        # strip state and documents from index and save it
        for file in index:
            if "documents" in index[file]:
                del index[file]["documents"]  # type: ignore
            if "state" in index[file]:
                del index[file]["state"]  # type: ignore
        with open(index_path, "w") as f:
            json.dump(index, f)

    def _preload_knowledge_folders(
        self,
        log_item: LogItem | None,
        kn_dirs: list[str],
        index: dict[str, knowledge_import.KnowledgeImport],
    ):
        # load knowledge folders, subfolders by area
        for kn_dir in kn_dirs:
            # everything in the root of the knowledge goes to main
            index = knowledge_import.load_knowledge(
                log_item,
                abs_knowledge_dir(kn_dir),
                index,
                {"area": Memory.Area.MAIN.value},
                filename_pattern="*",
                recursive=False,
            )
            # subdirectories go to their folders
            for area in Memory.Area:
                index = knowledge_import.load_knowledge(
                    log_item,
                    # files.get_abs_path("knowledge", kn_dir, area.value),
                    abs_knowledge_dir(kn_dir, area.value),
                    index,
                    {"area": area.value},
                    recursive=True,
                )

        return index

    def get_document_by_id(self, id: str) -> Document | None:
        return next(iter(self.db.get_by_ids(id)), None)

    async def embed_query(self, query: str) -> list[float]:
        return await self.db.embedding_function.aembed_query(query)

    async def search_similarity_threshold(
        self,
        query: str,
        limit: int,
        threshold: float,
        filter: str = "",
        embedding: list[float] | None = None,
    ):
        scored = await self.search_similarity_threshold_with_scores(query, limit, threshold, filter, embedding)
        return [doc for doc, _ in scored]

    async def search_similarity_threshold_with_scores(
        self, query: str, limit: int, threshold: float, filter: str = "",
        embedding: list[float] | None = None,
    ) -> list[tuple[Document, float]]:
        if embedding is None:
            embedding = await self.embed_query(query)
        predicate = Memory._get_comparator(filter) if filter else None
        hits = await asyncio.to_thread(self.db.search, embedding, limit, predicate)
        return [(doc, score) for doc, raw in hits if (score := Memory._cosine_normalizer(raw)) >= threshold]

    async def delete_documents_by_query(
        self,
        query: str,
        threshold: float,
        filter: str = "",
        *,
        include_exact: bool = False,
        cascade: bool = False,
    ):
        k = 100
        removed = []
        removed_ids: set[str] = set()

        while True:
            # Perform similarity search with score
            docs = await self.search_similarity_threshold(
                query, limit=k, threshold=threshold, filter=filter
            )
            removed += docs

            # Extract document IDs and filter based on score
            document_ids = [result.metadata["id"] for result in docs]
            removed_ids.update(str(doc_id) for doc_id in document_ids)

            # Delete documents with IDs over the threshold score
            if document_ids:
                await self.db.adelete(ids=document_ids)

            # If fewer than K document IDs, break the loop
            if len(document_ids) < k:
                break

        if include_exact:
            exact_docs = self._find_exact_query_docs(query, filter, removed_ids)
            if exact_docs:
                exact_ids = [doc.metadata["id"] for doc in exact_docs]
                await self.db.adelete(ids=exact_ids)
                removed += exact_docs
                removed_ids.update(str(doc_id) for doc_id in exact_ids)

        if cascade and removed_ids:
            related_docs = self._find_related_docs_by_ids(removed_ids)
            if related_docs:
                related_ids = [doc.metadata["id"] for doc in related_docs]
                await self.db.adelete(ids=related_ids)
                removed += related_docs
                removed_ids.update(str(doc_id) for doc_id in related_ids)

        return removed

    async def delete_documents_by_ids(
        self, ids: list[str], *, cascade: bool = False, filter: str = ""
    ):
        rem_docs = self.db.get_by_ids(
            ids
        )  # existing docs to remove (prevents error)
        rem_ids = [doc.metadata["id"] for doc in rem_docs]

        if cascade:
            related_docs = self._find_related_docs_by_ids(set(ids) | set(rem_ids))
            if related_docs:
                existing = {doc.metadata["id"] for doc in rem_docs}
                rem_docs.extend(
                    doc for doc in related_docs if doc.metadata["id"] not in existing
                )

        if rem_docs:
            rem_ids = [doc.metadata["id"] for doc in rem_docs]  # ids to remove
            await self.db.adelete(ids=rem_ids)

        return rem_docs

    async def insert_text(self, text, metadata: dict = {}):
        doc = Document(text, metadata=metadata)
        ids = await self.insert_documents([doc])
        return ids[0]

    async def insert_documents(self, docs: list[Document], *, delete_ids=()):
        ids = [self._generate_doc_id() for _ in range(len(docs))]
        timestamp = self.get_timestamp()

        if ids:
            for doc, id in zip(docs, ids):
                doc.metadata["id"] = id  # add ids to documents metadata
                doc.metadata["timestamp"] = timestamp  # add timestamp
                if not doc.metadata.get("area", ""):
                    doc.metadata["area"] = Memory.Area.MAIN.value

        if ids or delete_ids:
            await asyncio.to_thread(self.db.put, docs, delete_ids=delete_ids)
        return ids

    async def update_documents(self, docs: list[Document]):
        ids = [doc.metadata["id"] for doc in docs]
        await asyncio.to_thread(self.db.put, docs, replace=True)
        return ids

    def _generate_doc_id(self):
        while True:
            doc_id = guids.generate_id(10)  # random ID
            if not self.db.get_by_ids(doc_id):  # check if exists
                return doc_id

    def _find_exact_query_docs(
        self, query: str, filter: str, skip_ids: set[str]
    ) -> list[Document]:
        needle = _normalize_memory_match_text(query)
        if len(needle) < 3:
            return []

        docs: list[Document] = []
        comparator = Memory._get_comparator(filter) if filter else None
        for doc in self.db.get_all_docs().values():
            doc_id = str(doc.metadata.get("id", ""))
            if not doc_id or doc_id in skip_ids:
                continue
            if comparator and not comparator(doc.metadata):
                continue
            haystack = _normalize_memory_match_text(
                f"{doc.page_content}\n{json.dumps(doc.metadata, sort_keys=True, default=str)}"
            )
            if needle in haystack:
                docs.append(doc)
        return docs

    def _find_related_docs_by_ids(
        self, ids: set[str], filter: str = ""
    ) -> list[Document]:
        ids = {str(doc_id) for doc_id in ids if str(doc_id)}
        if not ids:
            return []

        docs: list[Document] = []
        comparator = Memory._get_comparator(filter) if filter else None
        for doc in self.db.get_all_docs().values():
            doc_id = str(doc.metadata.get("id", ""))
            if not doc_id or doc_id in ids:
                continue
            if comparator and not comparator(doc.metadata):
                continue
            if _metadata_references_any(doc.metadata, ids):
                docs.append(doc)
        return docs

    @staticmethod
    def _get_comparator(condition: str):
        _FILTER_SAFE = re.compile(
            r"^[a-zA-Z0-9_\-\.\ \t'\"=<>!()\[\],:\+]+$"
        )
        if len(condition) > 512 or not _FILTER_SAFE.match(condition):
            PrintStyle.error(
                f"Memory filter rejected (unsafe characters or too long): {condition!r}"
            )
            return lambda _data: False

        def comparator(data: dict[str, Any]):
            try:
                result = simple_eval(condition, names=data, functions={})
                return result
            except Exception as e:
                PrintStyle.error(f"Error evaluating condition: {e}")
                return False

        return comparator

    @staticmethod
    def _cosine_normalizer(val: float) -> float:
        res = (1 + val) / 2
        res = max(
            0, min(1, res)
        )  # float precision can cause values like 1.0000000596046448
        return float(res)  # native float, not numpy scalar (JSON serializable)

    @staticmethod
    def format_docs_plain(docs: list[Document]) -> list[str]:
        result = []
        for doc in docs:
            text = ""
            for k, v in doc.metadata.items():
                text += f"{k}: {v}\n"
            text += f"Content: {doc.page_content}"
            result.append(text)
        return result

    @staticmethod
    def get_timestamp():
        return Localization.get().now_iso(timespec="seconds")


def get_custom_knowledge_subdir_abs(agent: Agent) -> str:
    for dir in agent.config.knowledge_subdirs:
        if dir != "default":
            if dir == "custom":
                return files.get_abs_path("usr/knowledge")
            return files.get_abs_path("usr/knowledge", dir)
    raise Exception("No custom knowledge subdir set")


def reload():
    # clear the memory index, this will force all DBs to reload
    Memory.index = {}


def _normalize_memory_match_text(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def _metadata_references_any(value: Any, ids: set[str]) -> bool:
    if isinstance(value, dict):
        return any(_metadata_references_any(item, ids) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_metadata_references_any(item, ids) for item in value)
    text = str(value or "").strip()
    if not text:
        return False
    if text in ids:
        return True
    return any(doc_id in text.split(",") for doc_id in ids)


def abs_db_dir(memory_subdir: str) -> str:
    # patch for projects, this way we don't need to re-work the structure of memory subdirs
    if memory_subdir.startswith("projects/"):
        from helpers.projects import get_project_meta

        return files.get_abs_path(get_project_meta(memory_subdir[9:]), "memory")
    # standard subdirs
    return files.get_abs_path("usr/memory", memory_subdir)


def abs_knowledge_dir(knowledge_subdir: str, *sub_dirs: str) -> str:
    # patch for projects, this way we don't need to re-work the structure of knowledge subdirs
    if knowledge_subdir.startswith("projects/"):
        from helpers.projects import get_project_meta

        return files.get_abs_path(
            get_project_meta(knowledge_subdir[9:]), "knowledge", *sub_dirs
        )
    # standard subdirs
    if knowledge_subdir == "default":
        return files.get_abs_path("knowledge", *sub_dirs)
    if knowledge_subdir == "custom":
        return files.get_abs_path("usr/knowledge", *sub_dirs)
    return files.get_abs_path("usr/knowledge", knowledge_subdir, *sub_dirs)


def get_memory_subdir_abs(agent: Agent) -> str:
    subdir = get_agent_memory_subdir(agent)
    return abs_db_dir(subdir)


def get_agent_memory_subdir(agent: Agent) -> str:
    config = plugins.get_plugin_config("_memory", agent)

    if not config:
        return "default"
    
    # Check if project isolation is enabled and we are in a project
    if config.get("project_memory_isolation", True):
        project_name = projects.get_context_project_name(agent.context)
        if project_name:
            return "projects/" + project_name

    # Fallback to configured subdir or default
    return config.get("agent_memory_subdir", "") or "default"


def get_context_memory_subdir(context: AgentContext) -> str:
    agent = context.get_agent()
    return get_agent_memory_subdir(agent)


def get_existing_memory_subdirs() -> list[str]:
    try:
        from helpers.projects import (
            get_project_meta,
            get_projects_parent_folder,
        )

        # Get subdirectories from memory folder
        subdirs = files.get_subdirectories("usr/memory")

        project_subdirs = files.get_subdirectories(get_projects_parent_folder())
        for project_subdir in project_subdirs:
            folder = Path(get_project_meta(project_subdir), "memory")
            if (folder / NativeStore.filename).exists() or (folder / "index.pkl").exists():
                subdirs.append(f"projects/{project_subdir}")

        # Ensure 'default' is always available
        if "default" not in subdirs:
            subdirs.insert(0, "default")

        return subdirs
    except Exception as e:
        PrintStyle.error(f"Failed to get memory subdirectories: {str(e)}")
        return ["default"]


def get_knowledge_subdirs_by_memory_subdir(
    memory_subdir: str, default: list[str]
) -> list[str]:
    if memory_subdir.startswith("projects/"):
        from helpers.projects import get_project_meta

        default.append(get_project_meta(memory_subdir[9:], "knowledge"))
    return default
