from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent import AgentContext, AgentContextType
from helpers import files, plugins
from helpers.defer import DeferredTask, THREAD_BACKGROUND
from helpers.dirty_json import DirtyJson
from helpers.print_style import PrintStyle
from helpers import yaml as yaml_helper
from initialize import initialize_agent


PLUGIN_NAME = "_memory"

AUTO_DREAM_DIR = "autodream"
AUTO_DREAM_MEMORIES_DIR = "memories"
AUTO_DREAM_INDEX_FILE = "MEMORY.md"
AUTO_DREAM_STATE_FILE = "state.json"
AUTO_DREAM_LOG_FILE = ".dream-log.md"

MAX_RECENT_SESSIONS = 8
MAX_SESSION_CHARS = 4000
MAX_EXISTING_MEMORY_FILES = 24
MAX_EXISTING_MEMORY_CHARS = 2500
MAX_RECENT_VECTOR_MEMORIES = 16
MAX_RECENT_VECTOR_MEMORY_CHARS = 700
MAX_RELATED_VECTOR_MEMORIES = 12
MAX_RELATED_VECTOR_MEMORY_CHARS = 700
MAX_VECTOR_QUERY_COUNT = 8
MAX_VECTOR_QUERY_CHARS = 220
MAX_ORPHAN_CANDIDATES = 4
MAX_INDEX_PROMPT_CHARS = 6000
AUTO_DREAM_LOG_MAX_ENTRIES = 40
RELATED_VECTOR_THRESHOLD = 0.58
RELATED_VECTOR_PER_QUERY = 4
MIN_ORPHAN_OVERLAP = 0.5

_RUNNING_SUBDIRS: set[str] = set()
_RUNNING_LOCK = threading.Lock()
_TASKS: dict[str, DeferredTask] = {}


@dataclass
class DreamMemoryFile:
    file_name: str
    title: str
    description: str
    updated_at: datetime | None
    content: str


@dataclass
class DreamSession:
    context_id: str
    project_name: str | None
    agent_profile: str
    created_at: datetime
    last_message_at: datetime
    first_prompt: str
    transcript: str


def schedule_auto_dream(
    context_id: str,
    project_name: str | None,
    agent_profile: str,
    memory_subdir: str,
) -> bool:
    with _RUNNING_LOCK:
        if memory_subdir in _RUNNING_SUBDIRS:
            return False
        _RUNNING_SUBDIRS.add(memory_subdir)

    task = DeferredTask(thread_name=THREAD_BACKGROUND)
    task.start_task(
        _run_auto_dream,
        context_id=context_id,
        project_name=project_name,
        agent_profile=agent_profile,
        memory_subdir=memory_subdir,
    )
    _TASKS[memory_subdir] = task
    return True


async def _run_auto_dream(
    context_id: str,
    project_name: str | None,
    agent_profile: str,
    memory_subdir: str,
) -> None:
    background_context: AgentContext | None = None
    try:
        config = plugins.get_plugin_config(
            PLUGIN_NAME,
            project_name=project_name or "",
            agent_profile=agent_profile or "",
        ) or {}
        if not config.get("memory_memorize_enabled"):
            return
        if not config.get("memory_auto_dream_enabled"):
            return

        state = load_auto_dream_state(memory_subdir)
        last_dream_at = parse_iso_datetime(state.get("last_dream_at"))
        recent_sessions = load_recent_sessions(memory_subdir, last_dream_at)

        if not should_run_auto_dream(
            last_dream_at=last_dream_at,
            recent_session_count=len(recent_sessions),
            min_hours=int(config.get("memory_auto_dream_min_hours", 8) or 8),
            min_sessions=int(config.get("memory_auto_dream_min_sessions", 3) or 3),
        ):
            return

        background_context = AgentContext(
            config=initialize_agent(
                {"agent_profile": agent_profile} if agent_profile else None
            ),
            name="Memory AutoDream",
            type=AgentContextType.BACKGROUND,
        )
        if project_name:
            from helpers import projects

            projects.activate_project(
                background_context.id,
                project_name,
                mark_dirty=False,
            )

        agent = background_context.agent0

        existing_files = load_existing_memory_files(memory_subdir)
        memory_scope = describe_memory_scope(memory_subdir)
        orphan_candidates = find_orphan_candidates(memory_subdir)
        current_index = truncate_for_prompt(
            read_memory_index(memory_subdir),
            MAX_INDEX_PROMPT_CHARS,
        )
        recent_vector_memories = await load_recent_vector_memories(
            memory_subdir=memory_subdir,
            last_dream_at=last_dream_at,
        )
        related_vector_memories = await load_related_vector_memories(
            memory_subdir=memory_subdir,
            recent_sessions=recent_sessions,
            existing_memory_ids={
                str(item.get("id", "")).strip()
                for item in recent_vector_memories
                if str(item.get("id", "")).strip()
            },
        )

        system = agent.read_prompt("memory.autodream.sys.md")
        message = agent.read_prompt(
            "memory.autodream.msg.md",
            line_limit=int(config.get("memory_auto_dream_line_limit", 120) or 120),
            memory_scope=json.dumps(memory_scope, ensure_ascii=False, indent=2),
            current_index=current_index or "_No existing index_",
            existing_memories=json.dumps(
                [
                    {
                        "path": item.file_name,
                        "title": item.title,
                        "description": item.description,
                        "updated_at": serialize_datetime(item.updated_at),
                        "content": truncate_for_prompt(
                            item.content, MAX_EXISTING_MEMORY_CHARS
                        ),
                    }
                    for item in existing_files[:MAX_EXISTING_MEMORY_FILES]
                ],
                ensure_ascii=False,
                indent=2,
            ),
            recent_sessions=json.dumps(
                [
                    {
                        "context_id": session.context_id,
                        "project_name": session.project_name,
                        "agent_profile": session.agent_profile,
                        "created_at": serialize_datetime(session.created_at),
                        "last_message_at": serialize_datetime(session.last_message_at),
                        "first_prompt": session.first_prompt,
                        "transcript": session.transcript,
                    }
                    for session in recent_sessions[:MAX_RECENT_SESSIONS]
                ],
                ensure_ascii=False,
                indent=2,
            ),
            recent_vector_memories=json.dumps(
                recent_vector_memories,
                ensure_ascii=False,
                indent=2,
            ),
            related_vector_memories=json.dumps(
                related_vector_memories,
                ensure_ascii=False,
                indent=2,
            ),
            orphan_candidates=json.dumps(
                orphan_candidates,
                ensure_ascii=False,
                indent=2,
            ),
        )

        response = await agent.call_utility_model(
            system=system,
            message=message,
            background=True,
        )
        plan = DirtyJson.parse_string((response or "").strip())
        if not isinstance(plan, dict):
            raise ValueError("AutoDream model response was not a JSON object.")

        result = await apply_auto_dream_plan(
            memory_subdir=memory_subdir,
            plan=plan,
            line_limit=int(config.get("memory_auto_dream_line_limit", 120) or 120),
            run_metadata={
                "memory_scope": memory_scope,
                "orphan_candidates": orphan_candidates,
                "recent_session_count": len(recent_sessions),
                "recent_vector_count": len(recent_vector_memories),
                "related_vector_count": len(related_vector_memories),
            },
        )

        save_auto_dream_state(
            memory_subdir,
            {
                "schema_version": 2,
                "last_dream_at": datetime.now(timezone.utc).isoformat(),
                "last_status": "updated" if result["changed"] else "noop",
                "last_summary": result["summary"],
                "last_session_count": len(recent_sessions),
                "last_recent_vector_count": len(recent_vector_memories),
                "last_related_vector_count": len(related_vector_memories),
                "memory_file_count": result["memory_file_count"],
                "last_created_files": result["created_files"],
                "last_updated_files": result["updated_files"],
                "last_deleted_files": result["deleted_files"],
                "last_orphan_candidates": [
                    item.get("memory_subdir", "") for item in orphan_candidates
                ],
                "last_log_path": get_autodream_log_path(memory_subdir),
            },
        )

        if result["changed"] and result["summary"]:
            context = AgentContext.get(context_id)
            if context:
                context.log.log(
                    type="util",
                    heading="AutoDream updated durable memory",
                    content=result["summary"],
                    update_progress="none",
                )
    except Exception as exc:
        PrintStyle.error(f"AutoDream failed for '{memory_subdir}': {exc}")
    finally:
        with _RUNNING_LOCK:
            _RUNNING_SUBDIRS.discard(memory_subdir)
        _TASKS.pop(memory_subdir, None)
        if background_context:
            AgentContext.remove(background_context.id)


async def apply_auto_dream_plan(
    memory_subdir: str,
    plan: dict[str, Any],
    line_limit: int,
    run_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memories_dir = Path(get_autodream_memories_dir(memory_subdir))
    memories_dir.mkdir(parents=True, exist_ok=True)

    summary = str(plan.get("summary", "") or "").strip()
    raw_changes = plan.get("changes", [])
    if not isinstance(raw_changes, list):
        raw_changes = []

    created_files: list[str] = []
    updated_files: list[str] = []
    deleted_files: list[str] = []
    existing_file_names = {
        item.file_name for item in load_existing_memory_files(memory_subdir)
    }
    current_scope = (
        run_metadata.get("memory_scope", {}) if isinstance(run_metadata, dict) else {}
    )

    for change in raw_changes:
        if not isinstance(change, dict):
            continue

        action = str(change.get("action", "") or "").strip().lower()
        title = str(change.get("title", "") or "").strip()
        description = collapse_single_line(change.get("description", ""))
        raw_path = str(change.get("path", "") or "").strip()
        file_name = (
            normalize_memory_filename(raw_path or title or "memory")
            if action == "delete"
            else select_memory_file_name(raw_path, title, existing_file_names)
        )
        file_path = memories_dir / file_name

        if action == "delete":
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(file_name)
                existing_file_names.discard(file_name)
            continue

        if action != "upsert":
            continue
        if not title:
            continue

        frontmatter = {
            "title": title,
            "description": description,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "memory_scope": memory_subdir,
        }
        grounding = str(change.get("grounding", "") or "").strip().lower()
        if grounding in {"grounded", "inferred"}:
            frontmatter["grounding"] = grounding
        source_context_ids = normalize_string_list(change.get("source_context_ids", []))
        if source_context_ids:
            frontmatter["source_context_ids"] = source_context_ids
        source_first_prompts = normalize_string_list(
            change.get("source_first_prompts", [])
        )
        if source_first_prompts:
            frontmatter["source_first_prompts"] = source_first_prompts[:8]
        source_memory_ids = normalize_string_list(change.get("source_memory_ids", []))
        if source_memory_ids:
            frontmatter["source_memory_ids"] = source_memory_ids[:12]
        canonical_name = collapse_single_line(current_scope.get("canonical_name", ""))
        if canonical_name:
            frontmatter["canonical_scope_name"] = canonical_name
        project_title = collapse_single_line(current_scope.get("project_title", ""))
        if project_title:
            frontmatter["project_title"] = project_title

        body = format_memory_body(title, str(change.get("content", "") or ""))
        rendered = (
            "---\n"
            + yaml_helper.dumps(frontmatter).strip()
            + "\n---\n\n"
            + body
            + ("\n" if not body.endswith("\n") else "")
        )

        previous = file_path.read_text(encoding="utf-8") if file_path.exists() else None
        file_path.write_text(rendered, encoding="utf-8")
        if previous is None:
            created_files.append(file_name)
        elif previous != rendered:
            updated_files.append(file_name)
        existing_file_names.add(file_name)

    memory_files = load_existing_memory_files(memory_subdir)
    memory_index = render_memory_index(memory_files, line_limit=line_limit)
    Path(get_autodream_index_path(memory_subdir)).write_text(
        memory_index, encoding="utf-8"
    )

    changed = bool(created_files or updated_files or deleted_files)
    if changed:
        await reload_memory_with_autodream(memory_subdir)

    if not summary:
        if changed:
            summary = build_change_summary(created_files, updated_files, deleted_files)
        else:
            summary = "AutoDream found no durable memory changes to apply."

    append_auto_dream_log(
        memory_subdir=memory_subdir,
        summary=summary,
        created_files=created_files,
        updated_files=updated_files,
        deleted_files=deleted_files,
        run_metadata=run_metadata or {},
    )

    return {
        "summary": summary,
        "changed": changed,
        "memory_file_count": len(memory_files),
        "created_files": created_files,
        "updated_files": updated_files,
        "deleted_files": deleted_files,
    }


async def reload_memory_with_autodream(memory_subdir: str) -> None:
    from plugins._memory.helpers.memory import Memory

    clear_autodream_knowledge_import_cache(memory_subdir)
    Memory.index.pop(memory_subdir, None)
    await Memory.get_by_subdir(memory_subdir, preload_knowledge=True)


async def load_recent_vector_memories(
    memory_subdir: str,
    last_dream_at: datetime | None,
) -> list[dict[str, Any]]:
    from plugins._memory.helpers.memory import Memory

    db = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
    docs = list(db.db.get_all_docs().values())
    recent: list[dict[str, Any]] = []
    for doc in docs:
        metadata = doc.metadata or {}
        if metadata.get("autodream_source"):
            continue
        if metadata.get("knowledge_source"):
            continue

        timestamp = parse_memory_timestamp(metadata.get("timestamp", ""))
        if last_dream_at and timestamp and timestamp <= last_dream_at:
            continue

        recent.append(
            {
                "id": metadata.get("id", ""),
                "area": metadata.get("area", ""),
                "timestamp": metadata.get("timestamp", ""),
                "source_file": metadata.get("source_file", ""),
                "content": truncate_for_prompt(
                    str(doc.page_content or ""), MAX_RECENT_VECTOR_MEMORY_CHARS
                ),
            }
        )

    recent.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return recent[:MAX_RECENT_VECTOR_MEMORIES]


async def load_related_vector_memories(
    memory_subdir: str,
    recent_sessions: list[DreamSession],
    existing_memory_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    queries = build_related_vector_queries(recent_sessions)
    if not queries:
        return []

    from plugins._memory.helpers.memory import Memory

    db = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
    related: list[dict[str, Any]] = []
    seen_ids = set(existing_memory_ids or [])

    for query in queries:
        docs = await db.search_similarity_threshold(
            query=query,
            limit=RELATED_VECTOR_PER_QUERY,
            threshold=RELATED_VECTOR_THRESHOLD,
        )
        for doc in docs:
            metadata = doc.metadata or {}
            if metadata.get("autodream_source") or metadata.get("knowledge_source"):
                continue

            doc_id = str(metadata.get("id", "") or "").strip()
            if not doc_id or doc_id in seen_ids:
                continue

            seen_ids.add(doc_id)
            related.append(
                {
                    "id": doc_id,
                    "area": metadata.get("area", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "matched_query": query,
                    "source_file": metadata.get("source_file", ""),
                    "content": truncate_for_prompt(
                        str(doc.page_content or ""),
                        MAX_RELATED_VECTOR_MEMORY_CHARS,
                    ),
                }
            )
            if len(related) >= MAX_RELATED_VECTOR_MEMORIES:
                return related

    return related


def should_run_auto_dream(
    last_dream_at: datetime | None,
    recent_session_count: int,
    min_hours: int,
    min_sessions: int,
) -> bool:
    if recent_session_count <= 0:
        return False
    if last_dream_at is None:
        return True

    hours_since = (datetime.now(timezone.utc) - last_dream_at).total_seconds() / 3600
    if min_sessions > 0 and recent_session_count >= min_sessions:
        return True
    if min_hours > 0 and hours_since >= min_hours:
        return True
    return False


def load_recent_sessions(
    target_memory_subdir: str,
    last_dream_at: datetime | None,
) -> list[DreamSession]:
    chats_root = Path(files.get_abs_path("usr/chats"))
    if not chats_root.exists():
        return []

    sessions: list[DreamSession] = []
    for chat_file in chats_root.glob("*/chat.json"):
        try:
            payload = json.loads(chat_file.read_text(encoding="utf-8"))
            if str(payload.get("type", "")).lower() != AgentContextType.USER.value:
                continue

            context_data = payload.get("data", {}) or {}
            project_name = context_data.get("project")
            agent_profile = str(context_data.get("agent_profile", "") or "")
            if (
                resolve_memory_subdir(
                    project_name=project_name,
                    agent_profile=agent_profile,
                )
                != target_memory_subdir
            ):
                continue

            last_message_at = parse_iso_datetime(payload.get("last_message"))
            if last_message_at is None:
                continue
            if last_dream_at and last_message_at <= last_dream_at:
                continue

            created_at = parse_iso_datetime(payload.get("created_at")) or last_message_at

            history_payload = get_primary_history_payload(payload)
            first_prompt = extract_first_user_prompt(history_payload)
            transcript = truncate_for_prompt(
                render_history_text(history_payload),
                MAX_SESSION_CHARS,
            )
            if not first_prompt and not transcript:
                continue

            sessions.append(
                DreamSession(
                    context_id=str(payload.get("id", "") or chat_file.parent.name),
                    project_name=project_name,
                    agent_profile=agent_profile,
                    created_at=created_at,
                    last_message_at=last_message_at,
                    first_prompt=first_prompt,
                    transcript=transcript,
                )
            )
        except Exception:
            continue

    sessions.sort(key=lambda item: item.last_message_at)
    return sessions


def load_existing_memory_files(memory_subdir: str) -> list[DreamMemoryFile]:
    memories_dir = Path(get_autodream_memories_dir(memory_subdir))
    if not memories_dir.exists():
        return []

    files_out: list[DreamMemoryFile] = []
    for path in memories_dir.glob("*.md"):
        try:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            title = str(meta.get("title", "") or path.stem).strip() or path.stem
            description = collapse_single_line(meta.get("description", ""))
            updated_at = parse_iso_datetime(meta.get("updated_at"))
            files_out.append(
                DreamMemoryFile(
                    file_name=path.name,
                    title=title,
                    description=description,
                    updated_at=updated_at,
                    content=body.strip(),
                )
            )
        except Exception:
            continue

    files_out.sort(
        key=lambda item: (
            serialize_datetime(item.updated_at) if item.updated_at else "",
            item.title.lower(),
        ),
        reverse=True,
    )
    return files_out


def describe_memory_scope(memory_subdir: str) -> dict[str, Any]:
    scope: dict[str, Any] = {
        "memory_subdir": memory_subdir,
        "autodream_root": get_autodream_root(memory_subdir),
        "canonical_name": memory_subdir.rsplit("/", 1)[-1] or memory_subdir or "default",
        "canonical_slug": slugify_text(memory_subdir.rsplit("/", 1)[-1] or memory_subdir or "default"),
    }

    if not memory_subdir.startswith("projects/"):
        return scope

    project_name = memory_subdir[9:]
    scope["project_name"] = project_name
    scope["canonical_name"] = project_name
    scope["canonical_slug"] = slugify_text(project_name)

    try:
        from helpers import projects

        scope["project_folder"] = projects.get_project_folder(project_name)
        project_data = projects.load_basic_project_data(project_name)
        project_title = collapse_single_line(project_data.get("title", ""))
        project_description = collapse_single_line(project_data.get("description", ""))
        if project_title:
            scope["project_title"] = project_title
        if project_description:
            scope["project_description"] = truncate_for_prompt(project_description, 200)
    except Exception:
        pass

    return scope


def find_orphan_candidates(memory_subdir: str) -> list[dict[str, Any]]:
    if not memory_subdir.startswith("projects/"):
        return []

    current_project_name = memory_subdir[9:]
    current_tokens = slug_tokens(current_project_name)
    if not current_tokens:
        return []

    try:
        from helpers import projects

        projects_root = Path(projects.get_projects_parent_folder())
    except Exception:
        return []

    if not projects_root.exists():
        return []

    candidates: list[dict[str, Any]] = []
    for project_dir in projects_root.iterdir():
        if not project_dir.is_dir():
            continue

        sibling_project_name = project_dir.name
        if sibling_project_name == current_project_name:
            continue

        sibling_tokens = slug_tokens(sibling_project_name)
        overlap = score_token_overlap(current_tokens, sibling_tokens)
        if overlap < MIN_ORPHAN_OVERLAP:
            continue

        memories_dir = Path(
            projects.get_project_meta(
                sibling_project_name,
                "memory",
                AUTO_DREAM_DIR,
                AUTO_DREAM_MEMORIES_DIR,
            )
        )
        if not memories_dir.exists():
            continue

        memory_files = [path for path in memories_dir.glob("*.md") if path.is_file()]
        if not memory_files:
            continue

        latest_update = max((path.stat().st_mtime for path in memory_files), default=0.0)
        candidates.append(
            {
                "memory_subdir": f"projects/{sibling_project_name}",
                "project_name": sibling_project_name,
                "autodream_root": str(memories_dir.parent),
                "memory_file_count": len(memory_files),
                "overlap_score": round(overlap, 2),
                "shared_tokens": sorted(current_tokens & sibling_tokens),
                "last_updated_at": (
                    datetime.fromtimestamp(latest_update, tz=timezone.utc).isoformat()
                    if latest_update
                    else ""
                ),
            }
        )

    candidates.sort(
        key=lambda item: (
            item.get("overlap_score", 0),
            item.get("last_updated_at", ""),
        ),
        reverse=True,
    )
    return candidates[:MAX_ORPHAN_CANDIDATES]


def render_memory_index(
    memory_files: list[DreamMemoryFile],
    line_limit: int,
) -> str:
    lines = ["# Memory Index", ""]
    if not memory_files:
        lines.append("No durable memories indexed yet.")
        return "\n".join(lines) + "\n"

    max_entries = max(1, line_limit - 3)
    visible_entries = memory_files[:max_entries]
    hidden_entries = len(memory_files) - len(visible_entries)

    for item in visible_entries:
        title = collapse_single_line(item.title)
        description = collapse_single_line(item.description) or "Durable memory"
        lines.append(f"- [{title}](memories/{item.file_name}): {description}")

    if hidden_entries > 0:
        lines.append(
            f"- Additional memories hidden to respect the line limit: {hidden_entries}"
        )

    return "\n".join(lines) + "\n"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].strip() == "---":
        end_index = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_index = i
                break
        if end_index > 0:
            meta_text = "\n".join(lines[1:end_index])
            body_text = "\n".join(lines[end_index + 1 :]).strip()
            meta = yaml_helper.loads(meta_text) or {}
            if isinstance(meta, dict):
                return meta, body_text
    return {}, text.strip()


def save_auto_dream_state(memory_subdir: str, state: dict[str, Any]) -> None:
    Path(get_autodream_state_path(memory_subdir)).parent.mkdir(
        parents=True, exist_ok=True
    )
    Path(get_autodream_state_path(memory_subdir)).write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_auto_dream_state(memory_subdir: str) -> dict[str, Any]:
    path = Path(get_autodream_state_path(memory_subdir))
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_memory_index(memory_subdir: str) -> str:
    path = Path(get_autodream_index_path(memory_subdir))
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def append_auto_dream_log(
    memory_subdir: str,
    summary: str,
    created_files: list[str],
    updated_files: list[str],
    deleted_files: list[str],
    run_metadata: dict[str, Any],
) -> None:
    path = Path(get_autodream_log_path(memory_subdir))
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = render_auto_dream_log_entry(
        summary=summary,
        created_files=created_files,
        updated_files=updated_files,
        deleted_files=deleted_files,
        run_metadata=run_metadata,
    )

    existing_entries = parse_auto_dream_log_entries(
        path.read_text(encoding="utf-8") if path.exists() else ""
    )
    merged_entries = [entry, *existing_entries][:AUTO_DREAM_LOG_MAX_ENTRIES]
    header = "# AutoDream Log\n\nNewest runs first.\n\n"
    path.write_text(header + "\n\n".join(merged_entries).rstrip() + "\n", encoding="utf-8")


def render_auto_dream_log_entry(
    summary: str,
    created_files: list[str],
    updated_files: list[str],
    deleted_files: list[str],
    run_metadata: dict[str, Any],
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"## {timestamp}"]
    if summary:
        lines.append(f"- Summary: {collapse_single_line(summary)}")

    scope = run_metadata.get("memory_scope", {}) if isinstance(run_metadata, dict) else {}
    scope_name = collapse_single_line(scope.get("canonical_name", ""))
    if scope_name:
        lines.append(f"- Scope: {scope_name} ({scope.get('memory_subdir', '')})")

    lines.append(
        "- Inputs: "
        + ", ".join(
            [
                f"{int(run_metadata.get('recent_session_count', 0) or 0)} sessions",
                f"{int(run_metadata.get('recent_vector_count', 0) or 0)} recent vector memories",
                f"{int(run_metadata.get('related_vector_count', 0) or 0)} related vector memories",
            ]
        )
    )

    lines.extend(render_log_file_line("Created", created_files))
    lines.extend(render_log_file_line("Updated", updated_files))
    lines.extend(render_log_file_line("Pruned", deleted_files))

    orphan_candidates = run_metadata.get("orphan_candidates", [])
    if isinstance(orphan_candidates, list) and orphan_candidates:
        parts = []
        for item in orphan_candidates[:MAX_ORPHAN_CANDIDATES]:
            if not isinstance(item, dict):
                continue
            label = str(item.get("memory_subdir", "") or item.get("project_name", "")).strip()
            if not label:
                continue
            count = int(item.get("memory_file_count", 0) or 0)
            parts.append(f"{label} ({count} files)")
        if parts:
            lines.append(f"- Rename / orphan hints: {', '.join(parts)}")

    return "\n".join(lines).strip()


def parse_auto_dream_log_entries(text: str) -> list[str]:
    stripped = str(text or "").strip()
    if not stripped:
        return []

    entries: list[str] = []
    current: list[str] = []
    for line in stripped.splitlines():
        if line.startswith("# AutoDream Log"):
            continue
        if line.strip() == "Newest runs first.":
            continue
        if line.startswith("## "):
            if current:
                entries.append("\n".join(current).strip())
            current = [line]
            continue
        if current:
            current.append(line)

    if current:
        entries.append("\n".join(current).strip())
    return [entry for entry in entries if entry]


def render_log_file_line(label: str, file_names: list[str]) -> list[str]:
    if not file_names:
        return [f"- {label}: none"]
    return [f"- {label}: {', '.join(file_names)}"]


def clear_autodream_knowledge_import_cache(memory_subdir: str) -> None:
    from plugins._memory.helpers.memory import abs_db_dir

    index_path = Path(abs_db_dir(memory_subdir)) / "knowledge_import.json"
    if not index_path.exists():
        return

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(index, dict):
        return

    autodream_dir = Path(get_autodream_memories_dir(memory_subdir)).resolve()
    filtered_index: dict[str, Any] = {}
    changed = False

    for key, value in index.items():
        try:
            file_path = Path(str(key)).resolve()
        except Exception:
            file_path = Path(str(key))
        if file_path == autodream_dir or autodream_dir in file_path.parents:
            changed = True
            continue
        filtered_index[key] = value

    if changed:
        index_path.write_text(
            json.dumps(filtered_index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def get_primary_history_payload(chat_payload: dict[str, Any]) -> dict[str, Any]:
    agents = chat_payload.get("agents", []) or []
    if not agents:
        return {}

    history_json = agents[0].get("history", "")
    if not history_json:
        return {}

    try:
        history_payload = json.loads(history_json)
    except Exception:
        return {}
    return history_payload if isinstance(history_payload, dict) else {}


def extract_first_user_prompt(history_payload: dict[str, Any]) -> str:
    for output in iter_history_outputs(history_payload):
        if not output["ai"]:
            text = collapse_whitespace(output["text"])
            if text:
                return text
    return ""


def render_history_text(history_payload: dict[str, Any]) -> str:
    lines: list[str] = []
    for output in iter_history_outputs(history_payload):
        role = "assistant" if output["ai"] else "user"
        text = collapse_whitespace(output["text"])
        if text:
            lines.append(f"{role}: {text}")
    return "\n".join(lines)


def iter_history_outputs(history_payload: dict[str, Any]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    if not history_payload:
        return outputs

    for bulk in history_payload.get("bulks", []) or []:
        outputs.extend(record_outputs(bulk))
    for topic in history_payload.get("topics", []) or []:
        outputs.extend(record_outputs(topic))
    outputs.extend(record_outputs(history_payload.get("current", {})))
    return outputs


def record_outputs(record: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(record, dict):
        return []

    cls = record.get("_cls")
    if cls == "Message":
        content = record.get("summary") or record.get("content")
        text = stringify_history_content(content)
        return [{"ai": bool(record.get("ai")), "text": text}] if text else []

    if cls == "Topic":
        if record.get("summary"):
            return [
                {
                    "ai": False,
                    "text": stringify_history_content(record.get("summary")),
                }
            ]
        outputs: list[dict[str, Any]] = []
        for message in record.get("messages", []) or []:
            outputs.extend(record_outputs(message))
        return outputs

    if cls == "Bulk":
        if record.get("summary"):
            return [
                {
                    "ai": False,
                    "text": stringify_history_content(record.get("summary")),
                }
            ]
        outputs = []
        for nested in record.get("records", []) or []:
            outputs.extend(record_outputs(nested))
        return outputs

    return []


def stringify_history_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict) and "raw_content" in content:
        preview = content.get("preview")
        if isinstance(preview, str) and preview:
            return preview
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def resolve_memory_subdir(project_name: str | None, agent_profile: str) -> str:
    config = plugins.get_plugin_config(
        PLUGIN_NAME,
        project_name=project_name or "",
        agent_profile=agent_profile or "",
    ) or {}
    if project_name and config.get("project_memory_isolation", True):
        return f"projects/{project_name}"
    return config.get("agent_memory_subdir", "") or "default"


def get_autodream_root(memory_subdir: str) -> str:
    if memory_subdir.startswith("projects/"):
        from helpers.projects import get_project_meta

        return files.get_abs_path(
            get_project_meta(memory_subdir[9:]),
            "memory",
            AUTO_DREAM_DIR,
        )
    return files.get_abs_path("usr/memory", memory_subdir, AUTO_DREAM_DIR)


def get_autodream_memories_dir(memory_subdir: str) -> str:
    return str(Path(get_autodream_root(memory_subdir)) / AUTO_DREAM_MEMORIES_DIR)


def get_autodream_index_path(memory_subdir: str) -> str:
    return str(Path(get_autodream_root(memory_subdir)) / AUTO_DREAM_INDEX_FILE)


def get_autodream_state_path(memory_subdir: str) -> str:
    return str(Path(get_autodream_root(memory_subdir)) / AUTO_DREAM_STATE_FILE)


def get_autodream_log_path(memory_subdir: str) -> str:
    return str(Path(get_autodream_root(memory_subdir)) / AUTO_DREAM_LOG_FILE)


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def parse_memory_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except Exception:
        return parse_iso_datetime(value)


def serialize_datetime(value: datetime | None) -> str:
    return value.astimezone(timezone.utc).isoformat() if value else ""


def truncate_for_prompt(text: str, max_chars: int) -> str:
    text = str(text or "").strip()
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.6)
    tail = max_chars - head - 9
    return text[:head].rstrip() + "\n...\n" + text[-tail:].lstrip()


def normalize_memory_filename(value: str) -> str:
    safe = files.safe_file_name(
        (value or "").replace("\\", "/").split("/")[-1].strip()
    )
    safe = safe.lower().strip(" ._") or "memory"
    if not safe.endswith(".md"):
        safe += ".md"
    return safe


def select_memory_file_name(
    raw_path: str,
    title: str,
    existing_file_names: set[str],
) -> str:
    normalized_path = normalize_memory_filename(raw_path) if raw_path else ""
    title_file_name = normalize_memory_filename(title or normalized_path or "memory")

    if normalized_path and normalized_path in existing_file_names:
        return ensure_unique_memory_filename(
            normalized_path,
            existing_file_names,
            allow_existing=True,
        )

    if not normalized_path and title_file_name in existing_file_names:
        return ensure_unique_memory_filename(
            title_file_name,
            existing_file_names,
            allow_existing=True,
        )

    return ensure_unique_memory_filename(
        title_file_name,
        existing_file_names,
        allow_existing=False,
    )


def ensure_unique_memory_filename(
    file_name: str,
    existing_file_names: set[str],
    allow_existing: bool,
) -> str:
    if allow_existing and file_name in existing_file_names:
        return file_name
    if file_name not in existing_file_names:
        return file_name

    stem = file_name[:-3] if file_name.endswith(".md") else file_name
    suffix = ".md" if file_name.endswith(".md") else ""
    counter = 2
    while True:
        candidate = f"{stem}-{counter}{suffix}"
        if candidate not in existing_file_names:
            return candidate
        counter += 1


def build_related_vector_queries(recent_sessions: list[DreamSession]) -> list[str]:
    queries: list[str] = []
    seen: set[str] = set()

    for session in reversed(recent_sessions[-MAX_RECENT_SESSIONS:]):
        candidates = [session.first_prompt, extract_transcript_focus(session.transcript)]
        for candidate in candidates:
            query = truncate_single_line(candidate, MAX_VECTOR_QUERY_CHARS)
            if not query:
                continue
            token_count = len(slug_tokens(query))
            if token_count < 2:
                continue
            normalized = query.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            queries.append(query)
            if len(queries) >= MAX_VECTOR_QUERY_COUNT:
                return queries

    return queries


def extract_transcript_focus(transcript: str) -> str:
    user_lines = []
    for line in str(transcript or "").splitlines():
        if line.lower().startswith("user:"):
            user_lines.append(line.split(":", 1)[1].strip())
        if len(user_lines) >= 2:
            break
    return " ".join(user_lines)


def truncate_single_line(value: Any, max_chars: int) -> str:
    text = collapse_single_line(value)
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.strip()


def slugify_text(value: Any) -> str:
    normalized = normalize_memory_filename(str(value or "memory"))
    return normalized[:-3] if normalized.endswith(".md") else normalized


def slug_tokens(value: Any) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", str(value or "").lower()) if len(token) > 1}


def score_token_overlap(current_tokens: set[str], sibling_tokens: set[str]) -> float:
    if not current_tokens or not sibling_tokens:
        return 0.0
    return len(current_tokens & sibling_tokens) / max(
        len(current_tokens),
        len(sibling_tokens),
    )


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = collapse_single_line(item)
        if text and text not in result:
            result.append(text)
    return result


def collapse_single_line(value: Any) -> str:
    return collapse_whitespace(value).replace("\n", " ")


def collapse_whitespace(value: Any) -> str:
    return " ".join(str(value or "").split())


def format_memory_body(title: str, content: str) -> str:
    stripped = str(content or "").strip()
    if not stripped:
        return f"# {title}\n"
    if stripped.startswith("#"):
        return stripped + ("\n" if not stripped.endswith("\n") else "")
    return f"# {title}\n\n{stripped}\n"


def build_change_summary(
    created_files: list[str],
    updated_files: list[str],
    deleted_files: list[str],
) -> str:
    parts: list[str] = []
    if created_files:
        parts.append(f"created {len(created_files)}")
    if updated_files:
        parts.append(f"updated {len(updated_files)}")
    if deleted_files:
        parts.append(f"pruned {len(deleted_files)}")
    if not parts:
        return "AutoDream found no durable memory changes to apply."
    return "AutoDream " + ", ".join(parts) + " durable memory files."
