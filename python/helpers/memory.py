from datetime import datetime
from typing import Any, List, Optional
from python.helpers import guids

import os
import json
import asyncio

from python.helpers.print_style import PrintStyle
from python.helpers import files
from langchain_core.documents import Document
from python.helpers import knowledge_import
from python.helpers.log import Log, LogItem
from enum import Enum
from agent import Agent, AgentContext
import models
import logging
from python.helpers.cognee_init import get_cognee_setting


def _get_cognee():
    from python.helpers.cognee_init import get_cognee
    return get_cognee()


class Memory:

    class Area(Enum):
        MAIN = "main"
        FRAGMENTS = "fragments"
        SOLUTIONS = "solutions"

    _initialized: bool = False
    _datasets_cache: dict[str, str] = {}
    SEARCH_TIMEOUT = 15

    @staticmethod
    async def get(agent: Agent) -> "Memory":
        memory_subdir = get_agent_memory_subdir(agent)
        dataset_name = _subdir_to_dataset(memory_subdir)
        mem = Memory(dataset_name=dataset_name, memory_subdir=memory_subdir)
        if not Memory._initialized:
            Memory._initialized = True
            knowledge_subdirs = get_knowledge_subdirs_by_memory_subdir(
                memory_subdir, agent.config.knowledge_subdirs or []
            )
            if knowledge_subdirs:
                log_item = agent.context.log.log(
                    type="util",
                    heading=f"Initializing Cognee memory in '{memory_subdir}'",
                )
                await mem.preload_knowledge(log_item, knowledge_subdirs, memory_subdir)
        return mem

    @staticmethod
    async def get_by_subdir(
        memory_subdir: str,
        log_item: LogItem | None = None,
        preload_knowledge: bool = True,
    ) -> "Memory":
        dataset_name = _subdir_to_dataset(memory_subdir)
        mem = Memory(dataset_name=dataset_name, memory_subdir=memory_subdir)
        if preload_knowledge:
            import initialize
            agent_config = initialize.initialize_agent()
            knowledge_subdirs = get_knowledge_subdirs_by_memory_subdir(
                memory_subdir, agent_config.knowledge_subdirs or []
            )
            if knowledge_subdirs:
                await mem.preload_knowledge(log_item, knowledge_subdirs, memory_subdir)
        return mem

    @staticmethod
    async def reload(agent: Agent) -> "Memory":
        Memory._initialized = False
        Memory._datasets_cache.clear()
        return await Memory.get(agent)

    def __init__(self, dataset_name: str, memory_subdir: str):
        self.dataset_name = dataset_name
        self.memory_subdir = memory_subdir

    def _build_node_sets(self, area: str) -> list[str]:
        node_sets = [area]
        if self.memory_subdir.startswith("projects/"):
            project_name = self.memory_subdir.split("/", 1)[1]
            node_sets.append(f"project_{project_name}")
        return node_sets

    def _area_dataset(self, area: str) -> str:
        return f"{self.dataset_name}_{area}"

    async def preload_knowledge(
        self, log_item: LogItem | None, kn_dirs: list[str], memory_subdir: str
    ):
        cognee, _ = _get_cognee()

        if log_item:
            log_item.update(heading="Preloading knowledge...")

        state_dir = _state_dir(memory_subdir)
        os.makedirs(state_dir, exist_ok=True)
        index_path = os.path.join(state_dir, "knowledge_import.json")

        index: dict[str, knowledge_import.KnowledgeImport] = {}
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                index = json.load(f)

        if index:
            try:
                datasets = await cognee.datasets.list_datasets()
                if not datasets:
                    PrintStyle.warning("Cognee DB is empty but index exists — forcing full re-import")
                    if log_item:
                        log_item.stream(progress="\nCognee DB empty, re-importing all knowledge...")
                    index = {}
            except Exception:
                PrintStyle.warning("Cannot check cognee datasets — forcing full re-import")
                index = {}

        index = self._preload_knowledge_folders(log_item, kn_dirs, index)

        for file_key in index:
            entry = index[file_key]
            if entry["state"] in ["changed", "removed"] and entry.get("ids", []):
                for data_id in entry["ids"]:
                    try:
                        await _delete_data_by_id(self._area_dataset("main"), data_id)
                    except Exception:
                        pass
            if entry["state"] == "changed" and entry.get("documents"):
                new_ids = []
                for doc in entry["documents"]:
                    content = doc.page_content if hasattr(doc, "page_content") else str(doc)
                    try:
                        await cognee.add(
                            content,
                            dataset_name=self._area_dataset(entry.get("metadata", {}).get("area", "main")),
                            node_set=self._build_node_sets("knowledge"),
                        )
                        new_ids.append(guids.generate_id(10))
                    except Exception as e:
                        PrintStyle.error(f"Failed to import knowledge: {e}")
                entry["ids"] = new_ids

        index = {k: v for k, v in index.items() if v["state"] != "removed"}

        for file_key in index:
            if "documents" in index[file_key]:
                del index[file_key]["documents"]
            if "state" in index[file_key]:
                del index[file_key]["state"]
        with open(index_path, "w") as f:
            json.dump(index, f)

    def _preload_knowledge_folders(
        self,
        log_item: LogItem | None,
        kn_dirs: list[str],
        index: dict[str, knowledge_import.KnowledgeImport],
    ):
        for kn_dir in kn_dirs:
            index = knowledge_import.load_knowledge(
                log_item,
                abs_knowledge_dir(kn_dir),
                index,
                {"area": Memory.Area.MAIN.value},
                filename_pattern="*",
                recursive=False,
            )
            for area in Memory.Area:
                index = knowledge_import.load_knowledge(
                    log_item,
                    abs_knowledge_dir(kn_dir, area.value),
                    index,
                    {"area": area.value},
                    recursive=True,
                )
        return index

    def get_document_by_id(self, id: str) -> Document | None:
        return None

    async def search_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str = ""
    ) -> list[Document]:
        cognee, SearchType = _get_cognee()
        node_names = _parse_filter_to_node_names(filter)
        datasets = self._datasets_for_filter(filter)

        multi_enabled = get_cognee_setting("cognee_multi_search_enabled", True)

        if multi_enabled:
            return await self._multi_search(
                cognee, SearchType, query, limit, datasets, node_names
            )

        search_type_name = get_cognee_setting("cognee_search_type", "GRAPH_COMPLETION")
        try:
            search_type = getattr(SearchType, search_type_name)
        except AttributeError:
            search_type = SearchType.CHUNKS

        try:
            results = await cognee.search(
                query_text=query,
                query_type=search_type,
                top_k=limit,
                datasets=datasets if datasets else None,
                node_name=node_names if node_names else None,
            )
        except Exception:
            try:
                results = await cognee.search(
                    query_text=query,
                    query_type=SearchType.CHUNKS,
                    top_k=limit,
                    datasets=datasets if datasets else None,
                )
            except Exception as e:
                PrintStyle.error(f"Cognee search failed: {e}")
                return []

        return _results_to_documents(results, limit)

    async def _multi_search(
        self, cognee, SearchType, query: str, limit: int,
        datasets: list[str], node_names: list[str],
    ) -> list[Document]:
        type_names = get_cognee_setting("cognee_search_types", "GRAPH_COMPLETION,CHUNKS_LEXICAL")
        search_types = []
        for name in type_names.split(","):
            name = name.strip()
            if hasattr(SearchType, name):
                search_types.append(getattr(SearchType, name))
        if not search_types:
            search_types = [SearchType.CHUNKS]

        per_type_limit = max(limit, 10)

        async def _search_one(st):
            try:
                return await asyncio.wait_for(
                    cognee.search(
                        query_text=query,
                        query_type=st,
                        top_k=per_type_limit,
                        datasets=datasets if datasets else None,
                        node_name=node_names if node_names else None,
                    ),
                    timeout=self.SEARCH_TIMEOUT,
                )
            except asyncio.TimeoutError:
                PrintStyle.error(f"Cognee multi-search ({st.name}) timed out after {self.SEARCH_TIMEOUT}s")
                return []
            except Exception as e:
                PrintStyle.error(f"Cognee multi-search ({st.name}) failed: {e}")
                return []

        per_type_results = await asyncio.gather(*[_search_one(st) for st in search_types])

        all_results = []
        for results in per_type_results:
            if results:
                all_results.extend(results)

        if not all_results:
            try:
                all_results = await cognee.search(
                    query_text=query,
                    query_type=SearchType.CHUNKS,
                    top_k=limit,
                    datasets=datasets if datasets else None,
                )
            except Exception as e:
                PrintStyle.error(f"Cognee fallback search failed: {e}")
                return []

        docs = _results_to_documents(all_results, limit * len(search_types))
        return _deduplicate_documents(docs)[:limit]

    def _datasets_for_filter(self, filter: str) -> list[str]:
        if not filter:
            return [
                self._area_dataset(area.value)
                for area in Memory.Area
            ]

        datasets = []
        for area in Memory.Area:
            if area.value in filter:
                datasets.append(self._area_dataset(area.value))
        return datasets if datasets else [self._area_dataset(Memory.Area.MAIN.value)]

    async def delete_documents_by_query(
        self, query: str, threshold: float, filter: str = ""
    ) -> list[Document]:
        docs = await self.search_similarity_threshold(
            query=query, limit=100, threshold=threshold, filter=filter
        )
        if docs:
            ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
            for doc_id in ids:
                for area in Memory.Area:
                    try:
                        await _delete_data_by_id(self._area_dataset(area.value), doc_id)
                    except Exception:
                        pass
        return docs

    async def delete_documents_by_ids(self, ids: list[str]) -> list[Document]:
        removed = []
        for doc_id in ids:
            for area in Memory.Area:
                try:
                    await _delete_data_by_id(self._area_dataset(area.value), doc_id)
                    removed.append(Document(page_content="", metadata={"id": doc_id}))
                except Exception:
                    pass
        return removed

    async def insert_text(self, text: str, metadata: dict = {}) -> str:
        doc = Document(text, metadata=metadata)
        ids = await self.insert_documents([doc])
        return ids[0]

    async def insert_documents(self, docs: list[Document]) -> list[str]:
        cognee, _ = _get_cognee()
        ids = []
        timestamp = self.get_timestamp()
        from python.helpers.cognee_background import CogneeBackgroundWorker

        for doc in docs:
            doc_id = guids.generate_id(10)
            doc.metadata["id"] = doc_id
            doc.metadata["timestamp"] = timestamp
            area = doc.metadata.get("area", Memory.Area.MAIN.value)
            if not area:
                area = Memory.Area.MAIN.value
                doc.metadata["area"] = area

            dataset = self._area_dataset(area)
            node_sets = self._build_node_sets(area)

            meta_header = json.dumps(doc.metadata, default=str)
            enriched_text = f"[META:{meta_header}]\n{doc.page_content}"

            try:
                await cognee.add(
                    enriched_text,
                    dataset_name=dataset,
                    node_set=node_sets,
                )
                ids.append(doc_id)
                CogneeBackgroundWorker.get_instance().mark_dirty(dataset)
            except Exception as e:
                PrintStyle.error(f"Cognee insert failed for {doc_id}: {e}")

        return ids

    async def update_documents(self, docs: list[Document]) -> list:
        ids = [doc.metadata["id"] for doc in docs]
        await self.delete_documents_by_ids(ids)
        return await self.insert_documents(docs)

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
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _subdir_to_dataset(memory_subdir: str) -> str:
    return memory_subdir.replace("/", "_").replace(" ", "_").lower()


def _state_dir(memory_subdir: str) -> str:
    if memory_subdir.startswith("projects/"):
        from python.helpers.projects import get_project_meta_folder
        return files.get_abs_path(get_project_meta_folder(memory_subdir[9:]), "cognee_state")
    return files.get_abs_path("usr/cognee_state", memory_subdir)


def _parse_filter_to_node_names(filter_str: str) -> list[str]:
    if not filter_str:
        return []
    node_names = []
    for area in Memory.Area:
        if area.value in filter_str:
            node_names.append(area.value)
    return node_names


def _results_to_documents(results: Any, limit: int) -> list[Document]:
    docs = []
    if not results:
        return docs

    for result in results:
        if len(docs) >= limit:
            break

        content = ""
        metadata: dict[str, Any] = {}

        raw = result
        if hasattr(result, "search_result"):
            raw = result.search_result

        if isinstance(raw, str):
            content, metadata = _extract_metadata_from_text(raw)
        elif hasattr(raw, "text"):
            content, metadata = _extract_metadata_from_text(str(raw.text))
        elif hasattr(raw, "page_content"):
            content = raw.page_content
            metadata = getattr(raw, "metadata", {})
        elif isinstance(raw, dict):
            content = raw.get("text", raw.get("content", str(raw)))
            content, metadata = _extract_metadata_from_text(content)
        else:
            content, metadata = _extract_metadata_from_text(str(raw))

        if hasattr(result, "dataset_name") and result.dataset_name:
            metadata.setdefault("dataset", result.dataset_name)

        if not metadata.get("id"):
            metadata["id"] = guids.generate_id(10)
        if not metadata.get("area"):
            metadata["area"] = Memory.Area.MAIN.value
        if not metadata.get("timestamp"):
            metadata["timestamp"] = Memory.get_timestamp()

        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def _deduplicate_documents(docs: list[Document]) -> list[Document]:
    seen: set[str] = set()
    unique: list[Document] = []
    for doc in docs:
        key = doc.metadata.get("id", "")
        if not key:
            key = doc.page_content[:200]
        if key not in seen:
            seen.add(key)
            unique.append(doc)
    return unique


def _extract_metadata_from_text(text: str) -> tuple[str, dict]:
    if text.startswith("[META:"):
        try:
            meta_end = text.index("]\n")
            meta_json = text[6:meta_end]
            metadata = json.loads(meta_json)
            content = text[meta_end + 2:]
            return content, metadata
        except (ValueError, json.JSONDecodeError):
            pass
    return text, {"area": Memory.Area.MAIN.value}


async def _delete_data_by_id(dataset_name: str, data_id: str):
    cognee, _ = _get_cognee()
    try:
        datasets = await cognee.datasets.list_datasets()
        target = None
        for ds in datasets:
            if ds.name == dataset_name:
                target = ds
                break
        if not target:
            return False
        data_items = await cognee.datasets.list_data(target.id)
        for item in data_items:
            item_text = getattr(item, "raw_data_location", "") or getattr(item, "name", "") or ""
            if data_id in str(item_text):
                await cognee.datasets.delete_data(
                    dataset_id=target.id,
                    data_id=item.id,
                )
                return True
    except Exception as e:
        PrintStyle.error(f"Failed to delete data {data_id} from {dataset_name}: {e}")
    return False


def get_custom_knowledge_subdir_abs(agent: Agent) -> str:
    for dir in agent.config.knowledge_subdirs:
        if dir != "default":
            if dir == "custom":
                return files.get_abs_path("usr/knowledge")
            return files.get_abs_path("usr/knowledge", dir)
    raise Exception("No custom knowledge subdir set")


def reload():
    import python.helpers.cognee_init as ci
    ci._configured = False
    ci._cognee_module = None
    ci._search_type_class = None
    Memory._initialized = False
    Memory._datasets_cache.clear()


def abs_db_dir(memory_subdir: str) -> str:
    return _state_dir(memory_subdir)


def abs_knowledge_dir(knowledge_subdir: str, *sub_dirs: str) -> str:
    if knowledge_subdir.startswith("projects/"):
        from python.helpers.projects import get_project_meta_folder
        return files.get_abs_path(
            get_project_meta_folder(knowledge_subdir[9:]), "knowledge", *sub_dirs
        )
    if knowledge_subdir == "default":
        return files.get_abs_path("knowledge", *sub_dirs)
    if knowledge_subdir == "custom":
        return files.get_abs_path("usr/knowledge", *sub_dirs)
    return files.get_abs_path("usr/knowledge", knowledge_subdir, *sub_dirs)


def get_memory_subdir_abs(agent: Agent) -> str:
    subdir = get_agent_memory_subdir(agent)
    return _state_dir(subdir)


def get_agent_memory_subdir(agent: Agent) -> str:
    return get_context_memory_subdir(agent.context)


def get_context_memory_subdir(context: AgentContext) -> str:
    from python.helpers.projects import (
        get_context_memory_subdir as get_project_memory_subdir,
    )
    memory_subdir = get_project_memory_subdir(context)
    if memory_subdir:
        return memory_subdir
    return context.config.memory_subdir or "default"


def get_existing_memory_subdirs() -> list[str]:
    try:
        subdirs: set[str] = set()

        from python.helpers.projects import get_projects_parent_folder
        project_parent = get_projects_parent_folder()
        if os.path.exists(project_parent):
            for name in files.get_subdirectories(project_parent):
                subdirs.add(f"projects/{name}")

        result = sorted(subdirs)
        result.insert(0, "default")
        return result
    except Exception as e:
        PrintStyle.error(f"Failed to get memory subdirectories: {str(e)}")
        return ["default"]


def get_knowledge_subdirs_by_memory_subdir(
    memory_subdir: str, default: list[str]
) -> list[str]:
    result = list(default)
    if memory_subdir.startswith("projects/"):
        from python.helpers.projects import get_project_meta_folder
        result.append(get_project_meta_folder(memory_subdir[9:], "knowledge"))
    return result
