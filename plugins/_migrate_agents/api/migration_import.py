from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path, PurePosixPath

from agent import AgentContext
from helpers import files, persist_chat, projects as a0_projects
from helpers.api import ApiHandler, Input, Output, Request, Response
from plugins._migrate_agents.api.migration_preview import uploaded_files
from plugins._migrate_agents.helpers.migration import Asset, Project, build_a0_chat, parse_bundle


def _slug(value: str, fallback: str) -> str:
    result = re.sub(r"[^a-z0-9_-]+", "_", value.lower()).strip("_")
    return (result or fallback)[:80]


def _unique_dir(parent: Path, name: str) -> Path:
    candidate = parent / name
    index = 2
    while candidate.exists():
        candidate = parent / f"{name}_{index}"
        index += 1
    return candidate


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _knowledge_path(run_root: Path, asset: Asset) -> Path:
    source = PurePosixPath(asset.path)
    name = _slug("_".join(source.parts[-3:]), "knowledge")
    if not name.endswith(".md"):
        name += ".md"
    return run_root / name


def import_knowledge(source: str, category: str, assets: list[Asset]) -> list[str]:
    if not assets:
        return []
    base = Path(files.get_abs_path("usr", "knowledge", "_migrate_agents", source, category))
    run = _unique_dir(base, time.strftime("%Y%m%d_%H%M%S"))
    written: list[str] = []
    for asset in assets:
        destination = _knowledge_path(run, asset)
        header = (
            f"# Imported from {source}\n\n"
            f"> Original path: `{asset.path}`  \n"
            "> Imported by Migrate Agents. Review before sharing.\n\n"
        ).encode()
        _atomic_write(destination, header + asset.data)
        written.append(files.deabsolute_path(str(destination)))
    return written


def import_skills(source: str, skills: dict[str, list[Asset]]) -> list[str]:
    base = Path(files.get_abs_path("usr", "skills", "_migrate_agents", source))
    written: list[str] = []
    for name, assets in skills.items():
        destination = _unique_dir(base, _slug(name, "skill"))
        for asset in assets:
            relative = PurePosixPath(asset.path)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe skill path: {asset.path}")
            _atomic_write(destination.joinpath(*relative.parts), asset.data)
        written.append(files.deabsolute_path(str(destination)))
    return written


def import_projects(source: str, items: list[Project]) -> tuple[list[str], dict[str, str]]:
    parent = Path(a0_projects.get_projects_parent_folder())
    written: list[str] = []
    chat_projects: dict[str, str] = {}
    for item in items:
        base = _slug(f"{source}_{item.title}", f"{source}_project")
        name = base
        index = 2
        while (parent / name).exists():
            name = f"{base}_{index}"
            index += 1
        a0_projects.create_project(
            name,
            {
                "title": item.title,
                "description": f"Imported from {source}. Original workspace: {item.path}",
                "instructions": "",
                "include_agents_md": True,
                "color": "#6366f1",
                "git_url": "",
            },
        )
        written.append(name)
        chat_projects.update({chat_id: name for chat_id in item.conversation_ids})
    return written, chat_projects


def import_chats(source: str, conversations, chat_projects: dict[str, str] | None = None) -> list[str]:
    payloads = [json.dumps(build_a0_chat(item, source), ensure_ascii=False) for item in conversations]
    if not payloads:
        return []
    ctxids = persist_chat.load_json_chats(payloads)
    if len(ctxids) != len(conversations):
        raise RuntimeError("Imported chat count does not match the migration preview")
    chat_projects = chat_projects or {}
    for ctxid, conversation in zip(ctxids, conversations):
        context = AgentContext.get(ctxid)
        if context is None:
            raise RuntimeError(f"Imported chat was not loaded: {ctxid}")
        project_name = chat_projects.get(conversation.source_id)
        if project_name:
            a0_projects.activate_project(ctxid, project_name)
        else:
            persist_chat.save_tmp_chat(context)
    return ctxids


class MigrationImport(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            source = str(request.form.get("source") or "").strip().lower()
            include_chats = request.form.get("include_chats", "true").lower() == "true"
            include_projects = request.form.get("include_projects", "true").lower() == "true"
            legacy_knowledge = request.form.get("include_knowledge", "true")
            include_memories = request.form.get("include_memories", legacy_knowledge).lower() == "true"
            include_instructions = request.form.get("include_instructions", legacy_knowledge).lower() == "true"
            include_skills = request.form.get("include_skills", "true").lower() == "true"
            bundle = parse_bundle(source, uploaded_files(request))
            project_names, chat_projects = import_projects(source, bundle.projects) if include_projects else ([], {})
            ctxids = import_chats(source, bundle.conversations, chat_projects) if include_chats else []
            memories = import_knowledge(source, "memories", bundle.memories) if include_memories else []
            instructions = import_knowledge(source, "instructions", bundle.instructions) if include_instructions else []
            skills = import_skills(source, bundle.skills) if include_skills else []
            return {
                "ok": True,
                "ctxids": ctxids,
                "projects": project_names,
                "memories": memories,
                "instructions": instructions,
                "knowledge": [*memories, *instructions],
                "skills": skills,
                "summary": {
                    "chats": len(ctxids),
                    "projects": len(project_names),
                    "memories": len(memories),
                    "instructions": len(instructions),
                    "knowledge": len(memories) + len(instructions),
                    "skills": len(skills),
                    "redactions": bundle.redactions,
                },
                "warnings": bundle.warnings,
            }
        except ValueError as exc:
            return Response(str(exc), 400)
