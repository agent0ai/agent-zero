import asyncio
from pathlib import PurePosixPath
from threading import Event

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from helpers import projects, team_projects, team_runs
from helpers.defer import EventLoopThread
from helpers.tool import Response
from plugins._memory.helpers.memory import Memory


_THREAD = "TeamMemory"
_locks: dict[str, asyncio.Lock] = {}
_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}


async def execute_tool(agent, action: str, data: dict) -> Response:
    try:
        run, scope = team_runs.executing_scope(agent.context)
        name = projects.get_context_project_name(agent.context)
        outcome = await operate(name, scope, action, data, context_id=run.context_id)
        if action == "load":
            result = "\n\n".join(Memory.format_docs_plain(outcome["documents"])) or "No matching project memories."
        elif action == "save":
            result = f"Saved project memory {outcome['id']}."
        else:
            result = f"Deleted {outcome['count']} project memories."
        return Response(message=result, break_loop=False)
    except (PermissionError, ValueError) as error:
        return Response(message=str(error), break_loop=False)


async def operate(name: str, scope, action: str, data: dict, *, context_id: str | None = None) -> dict:
    if action not in ("load", "search", "save", "delete", "update", "reindex"):
        raise ValueError("Unsupported project memory action.")
    with team_projects.project_lock(name, scope) as project_id:
        pass
    cancelled = Event()
    future = EventLoopThread(_THREAD).run_coroutine(_perform(name, project_id, scope, action, data, context_id, cancelled))
    pending = asyncio.wrap_future(future)
    try:
        return await asyncio.shield(pending)
    except asyncio.CancelledError:
        cancelled.set()
        # A turn owns its reservation until an in-flight memory operation stops.
        try:
            await pending
        except Exception:
            pass
        raise


async def _perform(name, project_id, scope, action, data, context_id, cancelled):
    async with _locks.setdefault(project_id, asyncio.Lock()):
        if cancelled.is_set():
            raise ValueError("Project memory operation cancelled.")
        with team_projects.project_lock(name, scope) as current_id:
            if project_id != current_id:
                raise PermissionError("Project memory access denied.")
            knowledge = _collect_knowledge(name) if action == "reindex" else None
        memory = await Memory.get_by_subdir(f"team/{project_id}", preload_knowledge=False)
        if cancelled.is_set():
            raise ValueError("Project memory operation cancelled.")
        if action == "search":
            return await _apply(memory, action, data, knowledge)
        with team_projects.activity(f"memory.{action}", scope.account_id, project_id, context_id=context_id):
            return await _apply(memory, action, data, knowledge)


def _collect_knowledge(name):
    pending = [""]
    documents = []
    total = 0
    directories = 0
    while pending:
        directory = pending.pop()
        directories += 1
        if directories > 512:
            raise ValueError("The project knowledge tree has too many directories.")
        entries = team_projects.file_action(name, "list", {"path": directory, "area": "knowledge"})["entries"]
        for entry in entries:
            path = entry["path"]
            if entry["directory"]:
                pending.append(path)
            elif PurePosixPath(path).suffix.lower() in _TEXT_EXTENSIONS:
                total += entry["size"]
                if total > 2 * 1024 * 1024 or len(documents) >= 128:
                    raise ValueError("A reindex accepts up to 128 text files and 2 MiB of project knowledge.")
                loaded = team_projects.file_action(name, "read", {"path": path, "area": "knowledge"})
                documents.append((path, loaded["content"]))
    return documents


async def _reindex(memory, knowledge):
    old = [identifier for identifier, doc in memory.db.get_all_docs().items() if "knowledge_source" in doc.metadata]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1600, chunk_overlap=160)
    docs = [
        Document(page_content=chunk, metadata={"knowledge_source": path})
        for path, content in knowledge
        for chunk in splitter.split_text(content)
    ]
    await memory.insert_documents(docs)
    if old:
        await memory.delete_documents_by_ids(old)
    return {"count": len(knowledge)}


async def _apply(memory, action, data, knowledge):
    if action == "reindex":
        return await _reindex(memory, knowledge)
    if action in ("load", "search"):
        query = data.get("query") or data.get("search") or ""
        if not isinstance(query, str) or len(query) > 12_000:
            raise ValueError("Enter a query up to 12,000 characters.")
        limit = int(data.get("limit", 10) or 10)
        threshold = float(data.get("threshold", 0.6))
        if not 1 <= limit <= 100 or not 0 <= threshold <= 1:
            raise ValueError("Choose a valid memory limit and threshold.")
        if action == "load" and not query.strip():
            raise ValueError("Enter a memory search query.")
        documents = await memory.search_similarity_threshold(query=query, limit=limit, threshold=threshold) if query.strip() else list(memory.db.get_all_docs().values())[::-1]
        if area := data.get("area"):
            documents = [doc for doc in documents if doc.metadata.get("area") == area]
        return {"documents": documents[:limit], "total": len(memory.db.get_all_docs())}
    if action in ("save", "update"):
        text = data.get("text") or data.get("content")
        if not isinstance(text, str) or not text.strip() or len(text) > 12_000:
            raise ValueError("Enter memory text up to 12,000 characters.")
        if action == "save":
            return {"id": await memory.insert_text(text, {})}
        current = memory.get_document_by_id(data.get("memory_id", ""))
        if not current or "knowledge_source" in current.metadata:
            raise ValueError("Choose an existing project memory.")
        if "previous_text" in data and current.page_content != data["previous_text"]:
            raise team_projects.RevisionConflict("This memory has changed. Refresh it before saving.")
        await memory.update_documents([Document(page_content=text, metadata=dict(current.metadata))])
        return {"id": current.metadata["id"]}
    ids = data.get("ids") or data.get("memory_ids") or [data.get("memory_id")]
    if isinstance(ids, str):
        ids = [item.strip() for item in ids.split(",") if item.strip()]
    if not isinstance(ids, list) or not 1 <= len(ids) <= 100 or not all(isinstance(item, str) and item for item in ids):
        raise ValueError("Choose up to 100 saved memory IDs.")
    docs = memory.db.get_all_docs()
    targets = [identifier for identifier in set(ids) if identifier in docs and "knowledge_source" not in docs[identifier].metadata]
    return {"count": len(await memory.delete_documents_by_ids(targets)) if targets else 0}
