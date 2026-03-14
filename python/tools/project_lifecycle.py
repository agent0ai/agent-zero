from __future__ import annotations

import json
from typing import Any

from python.helpers import project_lifecycle
from python.helpers.tool import Response, Tool


class ProjectLifecycle(Tool):
    """
    Project lifecycle automation across design/development/testing/validation/agent-eval phases.

    Actions:
    - get
    - upsert
    - set_phase
    - set_access
    - link_subproject
    - run_phase
    - list_phase_runs
    - add_phase_schedule
    - remove_phase_schedule
    """

    async def execute(self, **kwargs) -> Response:
        action = str(self.args.get("action", "")).strip().lower()
        project_name = str(self.args.get("project_name", "")).strip()
        actor = str(self.args.get("actor", "system")).strip() or "system"
        if not project_name:
            return Response(message="Error: project_name is required", break_loop=False)

        try:
            if action == "get":
                data = project_lifecycle.load_lifecycle(project_name)
                return Response(
                    message=f"Loaded lifecycle for project '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "lifecycle": data},
                )

            if action == "upsert":
                patch = self.args.get("lifecycle")
                patch_obj = self._parse_json_obj(patch)
                data = project_lifecycle.upsert_lifecycle(project_name, patch_obj, actor=actor)
                return Response(
                    message=f"Updated lifecycle for project '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "lifecycle": data},
                )

            if action == "set_phase":
                phase = str(self.args.get("phase", "")).strip()
                if not phase:
                    raise Exception("phase is required")
                data = project_lifecycle.set_phase(project_name, phase=phase, actor=actor)
                return Response(
                    message=f"Set current phase to '{phase}' for '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "lifecycle": data},
                )

            if action == "set_access":
                owner = self.args.get("owner")
                collaborators = self.args.get("collaborators")
                collab_list: list[str] | None = None
                if collaborators is not None:
                    if isinstance(collaborators, str):
                        collab_list = [c.strip() for c in collaborators.split(",") if c.strip()]
                    elif isinstance(collaborators, list):
                        collab_list = [str(c).strip() for c in collaborators if str(c).strip()]
                    else:
                        raise Exception("collaborators must be an array or comma-separated string")

                data = project_lifecycle.set_access(
                    project_name,
                    owner=str(owner).strip() if owner is not None else None,
                    collaborators=collab_list,
                    actor=actor,
                )
                return Response(
                    message=f"Updated access policy for project '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "lifecycle": data},
                )

            if action == "link_subproject":
                subproject_name = str(self.args.get("subproject_name", "")).strip()
                if not subproject_name:
                    raise Exception("subproject_name is required")
                data = project_lifecycle.link_subproject(project_name, subproject_name=subproject_name, actor=actor)
                return Response(
                    message=f"Linked subproject '{subproject_name}' to '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "lifecycle": data},
                )

            if action == "run_phase":
                phase = str(self.args.get("phase", "")).strip()
                if not phase:
                    raise Exception("phase is required")
                options = project_lifecycle.PhaseRunOptions(
                    run_visual=str(self.args.get("run_visual", "true")).strip().lower() in {"1", "true", "yes", "on"},
                    actor=actor,
                )
                run = project_lifecycle.run_phase(project_name, phase=phase, options=options)
                status = str(run.get("status", "")).strip().lower() or "unknown"
                message = (
                    f"Lifecycle phase run completed for '{project_name}' phase '{phase}'. "
                    f"Run ID: {run.get('run_id')} | Status: {status}"
                )
                if status == "failed" and run.get("error"):
                    message += f" | Error: {run.get('error')}"
                return Response(
                    message=message,
                    break_loop=False,
                    additional={"project_name": project_name, "run": run},
                )

            if action == "list_phase_runs":
                phase = str(self.args.get("phase", "")).strip()
                limit = int(self.args.get("limit", 25) or 25)
                runs = project_lifecycle.list_phase_runs(project_name, phase=phase, limit=limit)
                return Response(
                    message=f"Found {len(runs)} lifecycle runs for '{project_name}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "runs": runs},
                )

            if action == "add_phase_schedule":
                phase = str(self.args.get("phase", "")).strip()
                cron = str(self.args.get("cron", "")).strip()
                if not phase:
                    raise Exception("phase is required")
                if not cron:
                    raise Exception("cron is required")
                run_visual = str(self.args.get("run_visual", "true")).strip().lower() in {"1", "true", "yes", "on"}
                timezone_name = str(self.args.get("timezone", "")).strip() or None
                data = await project_lifecycle.add_phase_schedule(
                    project_name,
                    phase=phase,
                    cron=cron,
                    timezone_name=timezone_name,
                    run_visual=run_visual,
                    actor=actor,
                )
                return Response(
                    message=f"Created schedule for '{project_name}' phase '{phase}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "schedule": data},
                )

            if action == "remove_phase_schedule":
                phase = str(self.args.get("phase", "")).strip()
                if not phase:
                    raise Exception("phase is required")
                data = await project_lifecycle.remove_phase_schedule(project_name, phase=phase, actor=actor)
                return Response(
                    message=f"Removed schedule for '{project_name}' phase '{phase}'.",
                    break_loop=False,
                    additional={"project_name": project_name, "schedule": data},
                )

            return Response(
                message=(
                    "Unknown action. Use one of: get, upsert, set_phase, set_access, "
                    "link_subproject, run_phase, list_phase_runs, add_phase_schedule, remove_phase_schedule"
                ),
                break_loop=False,
            )
        except Exception as exc:
            return Response(message=f"Project lifecycle error: {exc}", break_loop=False)

    def _parse_json_obj(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str) and raw.strip():
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        raise Exception("Expected JSON object payload")
