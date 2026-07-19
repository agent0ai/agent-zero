"""POST /api/plugins/_a0_connector/v1/skills_list."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class SkillsList(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from helpers import files, projects, skills

        project_name = str(input.get("project_name", "")).strip() or None
        skill_list = skills.list_skill_catalog(project_name=project_name or "")

        agent_profile = str(input.get("agent_profile", "")).strip() or None
        if agent_profile:
            roots: list[str] = [
                files.get_abs_path("agents", agent_profile, "skills"),
                files.get_abs_path("usr", "agents", agent_profile, "skills"),
            ]
            if project_name:
                roots.append(
                    projects.get_project_meta(project_name, "agents", agent_profile, "skills")
                )

            skill_list = [
                item
                for item in skill_list
                if any(files.is_in_dir(files.fix_dev_path(str(item["path"])), root) for root in roots)
            ]

        result = [
            {
                "name": skill["name"],
                "description": skill["description"],
                "path": str(skill["path"]),
                "origin": skill["origin"],
            }
            for skill in skill_list
        ]
        result.sort(key=lambda item: (item["name"], item["path"]))

        return {
            "ok": True,
            "data": result,
        }
