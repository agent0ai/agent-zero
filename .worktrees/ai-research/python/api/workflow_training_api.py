"""
API endpoint for Workflow Training operations.
Handles skills, learning paths, and training modules.
"""

import os

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class WorkflowTrainingApi(ApiHandler):
    """API handler for workflow training operations."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "")

        try:
            # Import the workflow manager
            from instruments.custom.workflow_engine.workflow_manager import (
                WorkflowEngineManager,
            )
            from instruments.custom.workflow_engine.workflow_visualizer import (
                WorkflowVisualizer,
            )

            # Get database path
            db_path = files.get_abs_path(
                "./instruments/custom/workflow_engine/data/workflow.db"
            )

            # Ensure data directory exists
            data_dir = os.path.dirname(db_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)

            # Initialize manager and visualizer
            manager = WorkflowEngineManager(db_path)
            visualizer = WorkflowVisualizer()

            # Route to appropriate handler
            if action == "list_skills":
                category = input.get("category")
                skills = manager.list_skills(category=category)
                return {"success": True, "skills": skills}

            elif action == "get_skill":
                skill_id = input.get("skill_id")
                if not skill_id:
                    return {"success": False, "error": "skill_id required"}

                skill = manager.get_skill(skill_id)
                if skill and "error" not in skill:
                    return {"success": True, "skill": skill}
                return {"success": False, "error": skill.get("error", "Skill not found") if skill else "Skill not found"}

            elif action == "get_proficiency":
                agent_id = input.get("agent_id", "agent_0")
                proficiency = manager.get_agent_proficiency(agent_id)
                return {"success": True, "proficiency": proficiency}

            elif action == "list_paths":
                target_role = input.get("target_role")
                paths = manager.list_learning_paths(target_role=target_role)
                return {"success": True, "paths": paths}

            elif action == "get_path":
                path_id = input.get("path_id")
                if not path_id:
                    return {"success": False, "error": "path_id required"}

                path = manager.get_learning_path(path_id)
                if path and "error" not in path:
                    return {"success": True, "path": path}
                return {"success": False, "error": path.get("error", "Learning path not found") if path else "Learning path not found"}

            elif action == "get_progress":
                path_id = input.get("path_id")
                agent_id = input.get("agent_id", "agent_0")

                if not path_id:
                    return {"success": False, "error": "path_id required"}

                progress = manager.get_learning_progress(path_id, agent_id)
                return {"success": True, "progress": progress}

            elif action == "get_module":
                module_id = input.get("module_id")
                if not module_id:
                    return {"success": False, "error": "module_id required"}

                module = manager.get_training_module(module_id)
                if module:
                    return {"success": True, "module": module}
                return {"success": False, "error": "Training module not found"}

            elif action == "skill_report":
                agent_id = input.get("agent_id", "agent_0")
                skills = manager.get_agent_proficiency(agent_id)
                chart = visualizer.generate_skill_chart(skills)
                return {"success": True, "skills": skills, "chart": chart}

            elif action == "training_dashboard":
                stats = manager.get_stats()
                skills = manager.get_top_skills(limit=5)
                dashboard = visualizer.generate_dashboard(stats, skills=skills)
                return {"success": True, "dashboard": dashboard}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
