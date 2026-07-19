from __future__ import annotations

from pathlib import Path
from typing import Any

from agent import AgentContext
from helpers import files, projects, skills
from helpers.api import ApiHandler, Request, Response
from helpers.persist_chat import save_tmp_chat


class SkillsCatalog(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "list") or "list").strip().lower()
        context_id = str(input.get("context_id", "") or "").strip()
        project_name = str(input.get("project_name", "") or "").strip()

        try:
            if action == "list":
                return self._build_state(context_id=context_id, project_name=project_name)
            if action == "activate":
                return self._activate(input, context_id=context_id)
            if action == "deactivate":
                return self._deactivate(input, context_id=context_id)
            if action == "clear":
                return self._clear(context_id=context_id)
            if action == "get_doc":
                return self._get_doc(input, context_id=context_id, project_name=project_name)
            return {"ok": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _activate(self, input: dict, *, context_id: str) -> dict[str, Any]:
        context = self._require_context(context_id)
        skill_entry = self._require_skill_entry(input)
        skills.activate_chat_skill(context.get_agent(), skill_entry)
        save_tmp_chat(context)
        return self._build_state(context_id=context.id)

    def _deactivate(self, input: dict, *, context_id: str) -> dict[str, Any]:
        context = self._require_context(context_id)
        skill_entry = self._require_skill_entry(input)
        skills.deactivate_chat_skill(context.get_agent(), skill_entry)
        skills.unload_agent_skill(context.get_agent(), skill_entry)
        save_tmp_chat(context)
        return self._build_state(context_id=context.id)

    def _clear(self, *, context_id: str) -> dict[str, Any]:
        context = self._require_context(context_id)
        skills.clear_chat_skill_overrides(context.get_agent())
        save_tmp_chat(context)
        return self._build_state(context_id=context.id)

    def _build_state(
        self,
        *,
        context_id: str = "",
        project_name: str = "",
    ) -> dict[str, Any]:
        context = AgentContext.get(context_id) if context_id else None
        agent = context.get_agent() if context else None

        if context and not project_name:
            project_name = projects.get_context_project_name(context) or ""

        catalog = skills.list_skill_catalog(project_name=project_name, agent=agent)
        catalog_by_key = {self._entry_key(skill): skill for skill in catalog}
        catalog_by_name = {
            str(skill.get("name") or "").strip().lower(): skill for skill in catalog
        }

        scope_entries = skills.get_scope_active_skills(agent)
        chat_entries = skills.get_chat_active_skills(context)
        disabled_entries = skills.get_chat_disabled_skills(context)
        active_entries = self._merge_entries(
            skills.get_active_skills(agent),
            self._get_loaded_skill_entries(agent),
        )

        scope_keys = {
            self._entry_key(entry) for entry in scope_entries if self._entry_key(entry)
        }
        chat_keys = {
            self._entry_key(entry) for entry in chat_entries if self._entry_key(entry)
        }

        return {
            "ok": True,
            "context_available": bool(context),
            "context_id": context.id if context else "",
            "project_name": project_name,
            "skills": catalog,
            "max_active_skills": skills.get_max_active_skills(),
            "active_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source=(
                        "Pinned + chat"
                        if key in scope_keys and key in chat_keys
                        else "Pinned default"
                        if key in scope_keys
                        else "Chat"
                    ),
                )
                for entry in active_entries
                if (key := self._entry_key(entry))
            ],
            "scope_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Pinned default",
                )
                for entry in scope_entries
            ],
            "chat_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Chat",
                )
                for entry in chat_entries
            ],
            "disabled_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Hidden in chat",
                )
                for entry in disabled_entries
            ],
        }

    def _get_doc(
        self,
        input: dict,
        *,
        context_id: str = "",
        project_name: str = "",
    ) -> dict[str, Any]:
        context = AgentContext.get(context_id) if context_id else None
        agent = context.get_agent() if context else None

        if context and not project_name:
            project_name = projects.get_context_project_name(context) or ""

        skill_entry = self._require_skill_entry(input)
        requested_key = self._entry_key(skill_entry)
        catalog = skills.list_skill_catalog(project_name=project_name, agent=agent)
        skill = next(
            (item for item in catalog if self._entry_key(item) == requested_key),
            None,
        )
        if not skill and skill_entry.get("name"):
            requested_name = str(skill_entry.get("name") or "").strip().lower()
            skill = next(
                (item for item in catalog if str(item.get("name") or "").strip().lower() == requested_name),
                None,
            )

        if not skill:
            raise ValueError("Skill not found in the current list")

        skill_path = str(skill.get("path") or "").strip()
        skill_md_path = Path(files.fix_dev_path(skill_path)) / "SKILL.md"
        if not skill_md_path.is_file():
            raise FileNotFoundError("SKILL.md not found")

        return {
            "ok": True,
            "filename": f"{skill.get('name') or skill_md_path.parent.name} / SKILL.md",
            "content": skill_md_path.read_text(encoding="utf-8", errors="replace"),
        }

    def _require_context(self, context_id: str) -> AgentContext:
        if not context_id:
            raise ValueError("context_id is required")

        context = AgentContext.get(context_id)
        if not context:
            raise ValueError("Context not found")
        return context

    def _require_skill_entry(self, input: dict) -> dict[str, str]:
        entries = skills.normalize_active_skills([input.get("skill")])
        if not entries:
            raise ValueError("skill is required")
        return entries[0]

    def _entry_key(self, entry: dict[str, Any]) -> str:
        return str(entry.get("path") or entry.get("name") or "").strip().lower()

    def _get_loaded_skill_entries(self, agent: Any | None) -> list[dict[str, str]]:
        if not agent:
            return []

        return skills.get_loaded_skill_entries(agent)

    def _merge_entries(
        self,
        *entry_groups: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()

        for entries in entry_groups:
            for entry in entries:
                key = self._entry_key(entry)
                if not key or key in seen:
                    continue
                seen.add(key)
                merged.append(entry)

        return merged

    def _serialize_entry(
        self,
        entry: dict[str, Any],
        catalog_by_key: dict[str, dict[str, Any]],
        catalog_by_name: dict[str, dict[str, Any]],
        *,
        state_source: str,
    ) -> dict[str, Any]:
        key = self._entry_key(entry)
        match = catalog_by_key.get(key)

        if not match:
            name_key = str(entry.get("name") or "").strip().lower()
            if name_key:
                match = catalog_by_name.get(name_key)

        if match:
            return {
                **match,
                "state_source": state_source,
                "missing": False,
            }

        path = str(entry.get("path") or "").strip()
        fallback_name = str(entry.get("name") or "").strip()
        if not fallback_name and path:
            fallback_name = Path(path).name or path

        return {
            "name": fallback_name or "(unnamed skill)",
            "description": "",
            "path": path,
            "origin": "Unavailable",
            "state_source": state_source,
            "missing": True,
        }
