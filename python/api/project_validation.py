from __future__ import annotations

from python.helpers import project_validation
from python.helpers.api import ApiHandler, Input, Output, Request


class ProjectValidation(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = str(input.get("action", "")).strip().lower()
        project_name = str(input.get("project_name", "")).strip()
        if not project_name:
            return {"ok": False, "error": "project_name is required"}

        try:
            if action == "list_suites":
                data = project_validation.list_suites(project_name)
            elif action == "load_suite":
                suite_name = str(input.get("suite_name", "")).strip()
                if not suite_name:
                    raise Exception("suite_name is required")
                data = project_validation.load_suite(project_name, suite_name)
            elif action == "save_suite":
                suite_name = str(input.get("suite_name", "")).strip()
                suite = input.get("suite")
                if not suite_name:
                    raise Exception("suite_name is required")
                if not isinstance(suite, dict):
                    raise Exception("suite is required and must be an object")
                data = project_validation.save_suite(project_name, suite_name, suite)
            elif action == "delete_suite":
                suite_name = str(input.get("suite_name", "")).strip()
                if not suite_name:
                    raise Exception("suite_name is required")
                data = project_validation.delete_suite(project_name, suite_name)
            elif action == "run_suite":
                suite_name = str(input.get("suite_name", "")).strip()
                if not suite_name:
                    raise Exception("suite_name is required")
                options = project_validation.RunOptions(
                    headed=bool(input.get("headed", True)),
                    session=str(input.get("session", "")).strip() or None,
                    cdp=str(input.get("cdp", "")).strip() or None,
                    profile_name=str(input.get("profile_name", "")).strip() or None,
                    per_step_timeout_seconds=int(input.get("per_step_timeout_seconds", 120) or 120),
                    base_url_override=str(input.get("base_url_override", "")).strip() or None,
                )
                data = project_validation.run_suite(project_name, suite_name, options)
            elif action == "list_runs":
                limit = int(input.get("limit", 25) or 25)
                data = project_validation.list_runs(project_name, limit=limit)
            elif action == "get_run":
                run_id = str(input.get("run_id", "")).strip()
                if not run_id:
                    raise Exception("run_id is required")
                data = project_validation.get_run(project_name, run_id)
            else:
                raise Exception("Invalid action")

            return {"ok": True, "data": data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
