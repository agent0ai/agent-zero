"""
API endpoint for the Workflow Dashboard UI.
Provides aggregated data for workflows, executions, skills, and learning paths.
"""

from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
import os


class WorkflowDashboard(ApiHandler):
    """API handler for the workflow dashboard."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Import the workflow manager
            from instruments.custom.workflow_engine.workflow_manager import (
                WorkflowEngineManager,
            )

            # Get database path
            db_path = files.get_abs_path(
                "./instruments/custom/workflow_engine/data/workflow.db"
            )

            # Ensure data directory exists
            data_dir = os.path.dirname(db_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)

            # Initialize manager
            manager = WorkflowEngineManager(db_path)

            # Get statistics
            stats = manager.get_stats()

            # Get recent executions (limit 5)
            recent_executions = manager.get_recent_executions(limit=5)

            # Get workflows
            workflows = manager.list_workflows()

            # Get top skills (by level, limit 5)
            top_skills = manager.get_top_skills(limit=5)

            # Get learning paths
            learning_paths = manager.list_learning_paths()

            # Get recent audit logs
            audit_logs = manager.get_audit_logs(limit=20)

            return {
                "success": True,
                "stats": {
                    "total_workflows": stats.get("total_workflows", 0),
                    "total_executions": stats.get("total_executions", 0),
                    "total_skills": stats.get("total_skills", 0),
                    "total_learning_paths": stats.get("total_learning_paths", 0),
                    "executions_by_status": stats.get("executions_by_status", {}),
                },
                "recent_executions": recent_executions,
                "top_skills": top_skills,
                "workflows": workflows,
                "learning_paths": learning_paths,
                "audit_logs": audit_logs,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": {
                    "total_workflows": 0,
                    "total_executions": 0,
                    "total_skills": 0,
                    "total_learning_paths": 0,
                    "executions_by_status": {},
                },
                "recent_executions": [],
                "top_skills": [],
                "workflows": [],
                "learning_paths": [],
                "audit_logs": [],
            }
