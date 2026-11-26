from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any

from agent import AgentContext
from helpers import files, projects, skills, team_access
from helpers.api import ApiHandler, Request, Response
from helpers.persist_chat import save_tmp_chat
from helpers.team_store import get_store


class SkillsCatalog(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "list") or "list").strip().lower()
        context_id = str(input.get("context_id", "") or "").strip()
        project_name = str(input.get("project_name", "") or "").strip()

        member = team_access.request_scope()
        context = AgentContext.get(context_id) if context_id else None
        project_scope = member is not None or team_access.is_team_chat(context)
        if project_scope:
            scope = team_access.request_chat_scope(context) if context else member
            if scope is None or (context_id and (not context or not team_access.can_send(scope, context))):
                return Response("Chat access denied.", 403)
            project_name = projects.get_context_project_name(context) if context else project_name
            if project_name not in scope.project_ids:
                return Response("Project access denied.", 403)

        try:
            if action == "list":
                return self._build_state(context_id=context_id, project_name=project_name, project_scope=project_scope)
            if action in {"activate", "hide", "show"}:
                with self.thread_lock if project_scope else nullcontext():
                    if project_scope:
                        current_scope = team_access.request_chat_scope(context) if context else None
                        if not context or current_scope is None or not team_access.can_send(current_scope, context):
                            return Response("Chat access denied.", 403)
                        if context.is_running() or get_store().active_run(context.id):
                            return Response("Wait for the current run before changing skills.", 409)
                    if action == "activate":
                        return self._activate(input, context_id=context_id, project_scope=project_scope)
                    if action == "hide":
                        return self._hide(input, context_id=context_id, project_scope=project_scope)
                    return self._show(input, context_id=context_id, project_scope=project_scope)
            if action == "deactivate":
                return self._deactivate(input, context_id=context_id)
            if action == "clear":
                return self._clear(context_id=context_id)
            if action == "get_doc":
                return self._get_doc(input, context_id=context_id, project_name=project_name, project_scope=project_scope)
            return {"ok": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _activate(self, input: dict, *, context_id: str, project_scope: bool = False) -> dict[str, Any]:
        context = self._require_context(context_id)
        skill_entry = self._require_skill_entry(input)
        agent = context.get_agent()
        skill = self._resolve_catalog_skill(skill_entry, context=context, project_scope=project_scope)
        skill_name = str(skill.get("name") or skill_entry.get("name") or "").strip()
        if not skill_name:
            raise ValueError("Skill name is required")

        skill_path = str(skill.get("path") or skill_entry.get("path") or "").strip()
        if not self._visible_skill_loaded(agent, skill_name):
            content = skills.load_skill_for_agent(skill_name=skill_path if project_scope else skill_name, agent=agent)
            if content.startswith("Error:"):
                raise ValueError(content)
            agent.hist_add_tool_result(
                "skills_tool",
                content,
                skill_instructions={
                    "name": skill_name,
                    "path": skill_path,
                    "source": "skills_page:load",
                    "content_included": True,
                },
            )
        skills.add_loaded_skill_name(agent, skill_name)
        save_tmp_chat(context)
        return self._build_state(context_id=context.id, project_scope=project_scope)

    def _deactivate(self, input: dict, *, context_id: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "Loaded skills are kept in chat history and cannot be removed.",
        }

    def _hide(self, input: dict, *, context_id: str, project_scope: bool = False) -> dict[str, Any]:
        context = self._require_context(context_id)
        skill_entry = self._require_skill_entry(input)
        if project_scope:
            skill_entry = self._resolve_catalog_skill(skill_entry, context=context, project_scope=True)
        skills.hide_chat_skill(context.get_agent(), skill_entry)
        save_tmp_chat(context)
        return self._build_state(context_id=context.id, project_scope=project_scope)

    def _show(self, input: dict, *, context_id: str, project_scope: bool = False) -> dict[str, Any]:
        context = self._require_context(context_id)
        skill_entry = self._require_skill_entry(input)
        if project_scope:
            skill_entry = self._resolve_catalog_skill(skill_entry, context=context, project_scope=True)
        skills.show_chat_skill(context.get_agent(), skill_entry)
        save_tmp_chat(context)
        return self._build_state(context_id=context.id, project_scope=project_scope)

    def _clear(self, *, context_id: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "Loaded skills are kept in chat history and cannot be removed.",
        }

    def _build_state(
        self,
        *,
        context_id: str = "",
        project_name: str = "",
        project_scope: bool = False,
    ) -> dict[str, Any]:
        context = AgentContext.get(context_id) if context_id else None
        agent = context.get_agent() if context else None

        if context and not project_name:
            project_name = projects.get_context_project_name(context) or ""

        catalog = skills.list_skill_catalog(project_name=project_name, agent=agent, project_scope=project_scope)
        catalog_by_key = {self._entry_key(skill): skill for skill in catalog}
        catalog_by_name = {
            str(skill.get("name") or "").strip().lower(): skill for skill in catalog
        }

        loaded_entries = skills.get_loaded_skill_entries(agent)
        scope_entries = skills.get_scope_active_skills(agent)
        scope_hidden_entries = skills.get_scope_hidden_skills(agent)
        chat_entries = skills.get_chat_active_skills(context)
        disabled_entries = skills.get_chat_disabled_skills(context)
        visible_entries = skills.get_chat_visible_skills(context)
        hidden_entries = skills.get_hidden_skills(agent)

        state = {
            "ok": True,
            "context_available": bool(context),
            "context_id": context.id if context else "",
            "project_name": project_name,
            "skills": catalog,
            "max_active_skills": skills.get_max_active_skills(
                agent=agent,
                project_name=project_name,
            ),
            "active_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Loaded in chat history",
                )
                for entry in loaded_entries
                if (key := self._entry_key(entry))
            ],
            "scope_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Scope default",
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
            "hidden_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source=(
                        "Hidden default"
                        if self._entry_matches_any(entry, scope_hidden_entries)
                        else "Hidden in chat"
                    ),
                )
                for entry in hidden_entries
            ],
            "scope_hidden_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Hidden default",
                )
                for entry in scope_hidden_entries
            ],
            "visible_skills": [
                self._serialize_entry(
                    entry,
                    catalog_by_key,
                    catalog_by_name,
                    state_source="Visible in chat",
                )
                for entry in visible_entries
            ],
        }
        if project_scope:
            for key, entries in state.items():
                if key != "skills" and isinstance(entries, list):
                    state[key] = [entry for entry in entries if not entry.get("missing")]
        return state

    def _get_doc(
        self,
        input: dict,
        *,
        context_id: str = "",
        project_name: str = "",
        project_scope: bool = False,
    ) -> dict[str, Any]:
        context = AgentContext.get(context_id) if context_id else None
        agent = context.get_agent() if context else None

        if context and not project_name:
            project_name = projects.get_context_project_name(context) or ""

        skill_entry = self._require_skill_entry(input)
        requested_key = self._entry_key(skill_entry)
        catalog = skills.list_skill_catalog(project_name=project_name, agent=agent, project_scope=project_scope)
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

    def _visible_skill_loaded(self, agent: Any, skill_name: str) -> bool:
        output = getattr(getattr(agent, "history", None), "output", None)
        if not callable(output):
            return False
        return any(
            skills.skill_instruction_name(message) == skill_name
            for message in output()
        )

    def _resolve_catalog_skill(
        self,
        entry: dict[str, Any],
        *,
        context: AgentContext,
        project_scope: bool = False,
    ) -> dict[str, Any]:
        agent = context.get_agent()
        project_name = projects.get_context_project_name(context) or ""
        catalog = skills.list_skill_catalog(project_name=project_name, agent=agent, project_scope=project_scope)
        match = next(
            (item for item in catalog if self._entry_matches_any(entry, [item])),
            None,
        )
        if match is None and project_scope:
            raise ValueError("Skill not found in this project.")
        return match or entry

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

    def _filter_hidden_entries(
        self,
        entries: list[dict[str, Any]],
        hidden_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            entry
            for entry in entries
            if not self._entry_matches_any(entry, hidden_entries)
        ]

    def _entry_matches_any(
        self,
        entry: dict[str, Any],
        entries: list[dict[str, Any]],
    ) -> bool:
        keys = {
            str(entry.get("path") or "").strip().lower(),
            str(entry.get("name") or "").strip().lower(),
        }
        keys.discard("")
        if not keys:
            return False

        for candidate in entries:
            candidate_keys = {
                str(candidate.get("path") or "").strip().lower(),
                str(candidate.get("name") or "").strip().lower(),
            }
            candidate_keys.discard("")
            if keys & candidate_keys:
                return True
        return False

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
