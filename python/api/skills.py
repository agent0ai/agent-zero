"""
Skills API - REST endpoints for Agent Skills management
Provides discovery, search, installation, and metadata access
"""

from python.helpers.api import ApiHandler, Request, Response
from python.helpers import errors
from python.helpers.agent_skills import get_integration, AgentSkillsIntegration
from pathlib import Path
from typing import Optional


class SkillsList(ApiHandler):
    """
    GET /api/skills/list
    List all available skills
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            integration = get_integration()

            # Trigger discovery
            force_refresh = input.get("refresh", False)
            integration.discover_and_register(force_refresh)

            # Get all skills
            skills = integration.get_available_skills_for_agent()

            return {
                "success": True,
                "skills": skills,
                "count": len(skills)
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsSearch(ApiHandler):
    """
    POST /api/skills/search
    Search for skills by query
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            query = input.get("query", "")

            if not query:
                return {
                    "success": False,
                    "error": "Query parameter is required"
                }

            integration = get_integration()
            results = integration.search_skills(query)

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "query": query
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsGet(ApiHandler):
    """
    GET /api/skills/get
    Get details of a specific skill
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            skill_name = input.get("name", "")

            if not skill_name:
                return {
                    "success": False,
                    "error": "Skill name is required"
                }

            integration = get_integration()
            skill_details = integration.get_skill_details(skill_name)

            if not skill_details:
                return {
                    "success": False,
                    "error": f"Skill '{skill_name}' not found"
                }

            return {
                "success": True,
                "skill": skill_details
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsDiscover(ApiHandler):
    """
    POST /api/skills/discover
    Force skill discovery/refresh
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            integration = get_integration()

            # Force discovery
            integration.discover_and_register(force_refresh=True)

            # Get stats
            stats = integration.get_stats()

            return {
                "success": True,
                "message": "Skills discovered successfully",
                "stats": stats
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsInstall(ApiHandler):
    """
    POST /api/skills/install
    Install a skill from a path
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            skill_path = input.get("path", "")
            target = input.get("target", "project")  # "project" or "global"

            if not skill_path:
                return {
                    "success": False,
                    "error": "Skill path is required"
                }

            if target not in ["project", "global"]:
                return {
                    "success": False,
                    "error": "Target must be 'project' or 'global'"
                }

            integration = get_integration()
            path = Path(skill_path)

            success = integration.install_skill_from_path(path, target)

            if success:
                return {
                    "success": True,
                    "message": f"Skill installed successfully to {target}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to install skill"
                }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsStats(ApiHandler):
    """
    GET /api/skills/stats
    Get skill system statistics
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            integration = get_integration()
            stats = integration.get_stats()

            return {
                "success": True,
                "stats": stats
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }


class SkillsByTrigger(ApiHandler):
    """
    POST /api/skills/by-trigger
    Get skills matching a trigger/context
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            trigger = input.get("trigger", "")

            if not trigger:
                return {
                    "success": False,
                    "error": "Trigger parameter is required"
                }

            integration = get_integration()
            skills = integration.get_skills_by_context(trigger)

            # Convert to dict representation
            skills_data = [skill.to_dict() for skill in skills]

            return {
                "success": True,
                "skills": skills_data,
                "count": len(skills_data),
                "trigger": trigger
            }

        except Exception as e:
            return {
                "success": False,
                "error": errors.error_text(e)
            }
