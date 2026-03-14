from __future__ import annotations

import json
from typing import Any

from python.helpers import project_validation
from python.helpers.tool import Response, Tool


def _parse_json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    raise Exception("Expected JSON object payload")


class VisualValidation(Tool):
    """
    Project-scoped visual validation using agent-browser.

    Actions:
    - list_suites
    - load_suite
    - save_suite
    - delete_suite
    - run_suite
    - list_runs
    - get_run
    """

    async def execute(self, **kwargs) -> Response:
        action = str(self.args.get("action", "")).strip().lower()
        project_name = str(self.args.get("project_name", "")).strip()
        if not project_name:
            return Response(message="Error: project_name is required", break_loop=False)

        handlers = {
            "list_suites": self._list_suites,
            "load_suite": self._load_suite,
            "save_suite": self._save_suite,
            "delete_suite": self._delete_suite,
            "run_suite": self._run_suite,
            "list_runs": self._list_runs,
            "get_run": self._get_run,
        }
        handler = handlers.get(action)
        if not handler:
            return Response(
                message=(
                    "Unknown action. Use one of: list_suites, load_suite, save_suite, "
                    "delete_suite, run_suite, list_runs, get_run"
                ),
                break_loop=False,
            )

        try:
            payload = await handler(project_name)
        except Exception as exc:
            return Response(message=f"Visual validation error: {exc}", break_loop=False)

        message = payload.pop("_message", "Done")
        return Response(message=message, break_loop=False, additional=payload)

    async def _list_suites(self, project_name: str) -> dict[str, Any]:
        suites = project_validation.list_suites(project_name)
        lines = [f"Suites for project '{project_name}': {len(suites)}"]
        for suite in suites:
            lines.append(f"- {suite.get('name')} ({suite.get('slug')}) [{suite.get('steps_count')} steps]")
        return {"_message": "\n".join(lines), "project_name": project_name, "suites": suites}

    async def _load_suite(self, project_name: str) -> dict[str, Any]:
        suite_name = str(self.args.get("suite_name", "")).strip()
        if not suite_name:
            raise Exception("suite_name is required")
        suite = project_validation.load_suite(project_name, suite_name)
        return {
            "_message": f"Loaded suite '{suite.get('name', suite_name)}' for project '{project_name}'.",
            "project_name": project_name,
            "suite": suite,
        }

    async def _save_suite(self, project_name: str) -> dict[str, Any]:
        suite_name = str(self.args.get("suite_name", "")).strip()
        suite_payload = self.args.get("suite")
        if not suite_name:
            raise Exception("suite_name is required")
        if suite_payload is None:
            raise Exception("suite payload is required")
        suite_data = _parse_json_object(suite_payload)
        saved = project_validation.save_suite(project_name, suite_name, suite_data)
        return {
            "_message": f"Saved suite '{saved.get('name', suite_name)}' for project '{project_name}'.",
            "project_name": project_name,
            "suite": saved,
        }

    async def _delete_suite(self, project_name: str) -> dict[str, Any]:
        suite_name = str(self.args.get("suite_name", "")).strip()
        if not suite_name:
            raise Exception("suite_name is required")
        deleted = project_validation.delete_suite(project_name, suite_name)
        return {
            "_message": f"Deleted suite '{deleted}' for project '{project_name}'.",
            "project_name": project_name,
            "suite_name": deleted,
        }

    async def _run_suite(self, project_name: str) -> dict[str, Any]:
        suite_name = str(self.args.get("suite_name", "")).strip()
        if not suite_name:
            raise Exception("suite_name is required")

        options = project_validation.RunOptions(
            headed=str(self.args.get("headed", "true")).strip().lower() in {"1", "true", "yes", "on"},
            session=str(self.args.get("session", "")).strip() or None,
            cdp=str(self.args.get("cdp", "")).strip() or None,
            profile_name=str(self.args.get("profile_name", "")).strip() or None,
            per_step_timeout_seconds=int(self.args.get("per_step_timeout_seconds", 120) or 120),
            base_url_override=str(self.args.get("base_url_override", "")).strip() or None,
        )

        run = project_validation.run_suite(project_name, suite_name, options)
        status = run.get("status", "unknown")
        run_id = run.get("run_id")
        return {
            "_message": (
                f"Run complete for suite '{suite_name}' on project '{project_name}'. "
                f"Status: {status}. Run ID: {run_id}."
            ),
            "project_name": project_name,
            "run": run,
        }

    async def _list_runs(self, project_name: str) -> dict[str, Any]:
        try:
            limit = int(self.args.get("limit", 25))
        except Exception:
            limit = 25
        runs = project_validation.list_runs(project_name, limit=limit)
        lines = [f"Recent visual validation runs for '{project_name}': {len(runs)}"]
        for run in runs:
            lines.append(
                f"- {run.get('run_id')} | {run.get('suite_name')} | {run.get('status')} | {run.get('started_at')}"
            )
        return {"_message": "\n".join(lines), "project_name": project_name, "runs": runs}

    async def _get_run(self, project_name: str) -> dict[str, Any]:
        run_id = str(self.args.get("run_id", "")).strip()
        if not run_id:
            raise Exception("run_id is required")
        run = project_validation.get_run(project_name, run_id)
        return {
            "_message": f"Loaded run '{run_id}' for project '{project_name}'.",
            "project_name": project_name,
            "run": run,
        }
