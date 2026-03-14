from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from python.helpers import files, project_validation, projects
from python.helpers.print_style import PrintStyle

LIFECYCLE_FILE = "lifecycle.json"
RUNS_DIR = "runs"

TEMPLATE_PATHS = {
    "product_development": "instruments/custom/workflow_engine/templates/product_development.json",
    "service_delivery": "instruments/custom/workflow_engine/templates/service_delivery.json",
    "ai_solutioning": "instruments/custom/workflow_engine/templates/ai_solutioning.json",
}


@dataclass
class PhaseRunOptions:
    run_visual: bool = True
    actor: str = "system"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    raw = (value or "").strip().lower()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in raw)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-_") or "phase"


def _ensure_project_exists(project_name: str) -> None:
    projects.load_basic_project_data(project_name)


def _lifecycle_path(project_name: str) -> Path:
    return Path(projects.get_project_lifecycle_folder(project_name, LIFECYCLE_FILE))


def _runs_path(project_name: str) -> Path:
    return Path(projects.get_project_lifecycle_folder(project_name, RUNS_DIR))


def _default_phase_bindings() -> dict[str, dict[str, Any]]:
    return {
        "design": {
            "name": "Design",
            "workflow_template": "product_development",
            "workflow_stage": "design",
            "visual_suite": "",
            "enabled": True,
        },
        "development": {
            "name": "Development",
            "workflow_template": "product_development",
            "workflow_stage": "mvp",
            "visual_suite": "",
            "enabled": True,
        },
        "testing": {
            "name": "Testing",
            "workflow_template": "service_delivery",
            "workflow_stage": "implementation",
            "visual_suite": "",
            "enabled": True,
        },
        "validation": {
            "name": "Validation",
            "workflow_template": "service_delivery",
            "workflow_stage": "deployment",
            "visual_suite": "",
            "enabled": True,
        },
        "ai_agent_evaluation": {
            "name": "AI Agent Evaluation",
            "workflow_template": "ai_solutioning",
            "workflow_stage": "proposal",
            "visual_suite": "",
            "enabled": True,
        },
    }


def _default_lifecycle(owner: str = "") -> dict[str, Any]:
    now = _now_iso()
    return {
        "version": 1,
        "created_at": now,
        "updated_at": now,
        "lifecycle_model": "hybrid",
        "current_phase": "design",
        "agent_eval_scope": "task_success_and_artifact_proof",
        "phase_bindings": _default_phase_bindings(),
        "triggers": {
            "manual": True,
            "scheduler": True,
        },
        "access": {
            "owner": owner,
            "collaborators": [],
        },
        "links": {
            "parent_project": "",
            "subprojects": [],
        },
        "browser": {
            "headed": True,
            "session": "",
            "cdp": "",
            "profile_name": "",
            "profiles": {},
            "per_step_timeout_seconds": 120,
        },
        "retention": {
            "max_runs": 100,
        },
        "schedules": {},
        "last_run": None,
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _ensure_lifecycle_dirs(project_name: str) -> None:
    files.create_dir(projects.get_project_lifecycle_folder(project_name))
    files.create_dir(str(_runs_path(project_name)))


def _write_lifecycle(project_name: str, data: dict[str, Any]) -> dict[str, Any]:
    data["updated_at"] = _now_iso()
    path = _lifecycle_path(project_name)
    _ensure_lifecycle_dirs(project_name)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def _run_lock_path(project_name: str) -> Path:
    return Path(projects.get_project_lifecycle_folder(project_name, "run.lock"))


def _acquire_run_lock(project_name: str) -> None:
    lock_path = _run_lock_path(project_name)
    _ensure_lifecycle_dirs(project_name)

    # Best-effort stale lock cleanup.
    if lock_path.exists():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
            lock_started = str(existing.get("started_at", "")).strip()
            if lock_started:
                then = datetime.fromisoformat(lock_started.replace("Z", "+00:00"))
                age_seconds = (datetime.now(timezone.utc) - then).total_seconds()
                if age_seconds > 3600:
                    lock_path.unlink(missing_ok=True)
        except Exception:
            pass

    payload = {
        "pid": os.getpid(),
        "started_at": _now_iso(),
    }
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, (json.dumps(payload) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
    except FileExistsError:
        raise Exception("A lifecycle run is already in progress for this project.")


def _release_run_lock(project_name: str) -> None:
    _run_lock_path(project_name).unlink(missing_ok=True)


def _apply_run_retention(project_name: str, max_runs: int) -> None:
    if max_runs <= 0:
        return
    rows: list[tuple[Path, str]] = []
    for run_file in _runs_path(project_name).glob("*.json"):
        try:
            data = json.loads(run_file.read_text(encoding="utf-8"))
            started_at = str(data.get("started_at", ""))
        except Exception:
            started_at = ""
        rows.append((run_file, started_at))

    rows.sort(key=lambda row: row[1], reverse=True)
    for run_file, _ in rows[max_runs:]:
        run_file.unlink(missing_ok=True)


def _is_allowed(lifecycle: dict[str, Any], actor: str) -> bool:
    if actor in {"", "system"}:
        return True
    access = lifecycle.get("access") if isinstance(lifecycle.get("access"), dict) else {}
    owner = str(access.get("owner", "")).strip()
    collaborators = access.get("collaborators", [])
    collab_set = {str(item).strip() for item in collaborators if str(item).strip()}
    return not owner or actor == owner or actor in collab_set


def _require_access(lifecycle: dict[str, Any], actor: str) -> None:
    if not _is_allowed(lifecycle, actor):
        raise Exception(f"Actor '{actor}' is not allowed for this project lifecycle")


def load_lifecycle(project_name: str) -> dict[str, Any]:
    _ensure_project_exists(project_name)
    _ensure_lifecycle_dirs(project_name)
    path = _lifecycle_path(project_name)
    if not path.exists():
        return _write_lifecycle(project_name, _default_lifecycle())

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Exception("Invalid lifecycle format")

    merged = _deep_merge(_default_lifecycle(), data)
    if merged != data:
        return _write_lifecycle(project_name, merged)
    return merged


def upsert_lifecycle(project_name: str, patch: dict[str, Any], actor: str = "system") -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)
    merged = _deep_merge(lifecycle, patch)
    return _write_lifecycle(project_name, merged)


def set_phase(project_name: str, phase: str, actor: str = "system") -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)
    phase_id = _slug(phase)
    bindings = lifecycle.get("phase_bindings", {})
    if phase_id not in bindings:
        raise Exception(f"Unknown lifecycle phase: {phase}")
    lifecycle["current_phase"] = phase_id
    return _write_lifecycle(project_name, lifecycle)


def set_access(
    project_name: str,
    owner: str | None = None,
    collaborators: list[str] | None = None,
    actor: str = "system",
) -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)
    access = lifecycle.setdefault("access", {})
    if owner is not None:
        access["owner"] = str(owner).strip()
    if collaborators is not None:
        access["collaborators"] = sorted({str(c).strip() for c in collaborators if str(c).strip()})
    return _write_lifecycle(project_name, lifecycle)


def link_subproject(project_name: str, subproject_name: str, actor: str = "system") -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)

    if not subproject_name:
        raise Exception("subproject_name is required")
    _ensure_project_exists(subproject_name)

    links = lifecycle.setdefault("links", {})
    subprojects = links.setdefault("subprojects", [])
    if subproject_name not in subprojects:
        subprojects.append(subproject_name)
        subprojects.sort()

    return _write_lifecycle(project_name, lifecycle)


def list_phase_runs(project_name: str, phase: str = "", limit: int = 25) -> list[dict[str, Any]]:
    _ensure_project_exists(project_name)
    _ensure_lifecycle_dirs(project_name)

    rows: list[dict[str, Any]] = []
    run_files = sorted(_runs_path(project_name).glob("*.json"), reverse=True)
    for run_file in run_files:
        try:
            data = json.loads(run_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            if phase and _slug(str(data.get("phase", ""))) != _slug(phase):
                continue
            rows.append(data)
        except Exception:
            continue

    # Prefer explicit lifecycle timestamps over filename ordering.
    rows.sort(key=lambda row: str(row.get("started_at", "")), reverse=True)
    return rows[: max(limit, 1)]


def _resolve_template_path(template_id: str) -> str:
    path = TEMPLATE_PATHS.get(template_id)
    if not path:
        raise Exception(f"Unsupported workflow template: {template_id}")
    abs_path = files.get_abs_path(path)
    if not Path(abs_path).exists():
        raise Exception(f"Workflow template not found: {template_id}")
    return abs_path


def _get_workflow_manager():
    from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager

    db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
    return WorkflowEngineManager(db_path)


def _run_visual_validation_if_configured(
    project_name: str,
    phase_binding: dict[str, Any],
    lifecycle: dict[str, Any],
    options: PhaseRunOptions,
) -> dict[str, Any] | None:
    suite_name = str(phase_binding.get("visual_suite", "")).strip()
    if not options.run_visual:
        return None
    if not suite_name:
        raise Exception(
            "Visual validation is enabled for this run but no visual_suite is configured "
            f"for phase '{phase_binding.get('name', 'unknown')}'."
        )

    browser = lifecycle.get("browser") if isinstance(lifecycle.get("browser"), dict) else {}
    profiles = browser.get("profiles", {}) if isinstance(browser.get("profiles"), dict) else {}
    actor_profile = str(profiles.get(options.actor, "")).strip() if options.actor else ""
    default_profile = str(browser.get("profile_name", "")).strip()
    profile_name = actor_profile or default_profile
    if not profile_name:
        raise Exception(
            "Visual validation requires a browser profile. Set browser.profile_name or "
            f"browser.profiles['{options.actor}'] in project lifecycle settings."
        )

    run_options = project_validation.RunOptions(
        headed=bool(browser.get("headed", True)),
        session=str(browser.get("session", "")).strip() or None,
        cdp=str(browser.get("cdp", "")).strip() or None,
        profile_name=profile_name,
        per_step_timeout_seconds=int(browser.get("per_step_timeout_seconds", 120) or 120),
    )
    return project_validation.run_suite(project_name, suite_name, run_options)


def run_phase(
    project_name: str,
    phase: str,
    options: PhaseRunOptions | None = None,
) -> dict[str, Any]:
    options = options or PhaseRunOptions()
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, options.actor)

    phase_id = _slug(phase)
    bindings = lifecycle.get("phase_bindings") if isinstance(lifecycle.get("phase_bindings"), dict) else {}
    phase_binding = bindings.get(phase_id)
    if not isinstance(phase_binding, dict):
        raise Exception(f"Unknown lifecycle phase: {phase}")
    if not bool(phase_binding.get("enabled", True)):
        raise Exception(f"Lifecycle phase is disabled: {phase}")

    run_id = f"plr_{uuid4().hex[:12]}"
    timer_start = time.monotonic()
    started_at = _now_iso()
    finished_at = started_at
    run_status = "started"
    visual_result: dict[str, Any] | None = None
    visual_error: str | None = None
    started: dict[str, Any] = {}
    template_id = str(phase_binding.get("workflow_template", "")).strip()
    workflow_name = f"{project_name}_{phase_id}_lifecycle"

    _acquire_run_lock(project_name)
    try:
        manager = _get_workflow_manager()
        template_path = _resolve_template_path(template_id)

        workflow = manager.get_workflow(name=workflow_name)
        if not workflow or "error" in workflow:
            created = manager.create_from_template(template_path, workflow_name)
            if "error" in created:
                raise Exception(created["error"])
            workflow = manager.get_workflow(name=workflow_name)

        execution_name = f"{project_name}_{phase_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        started = manager.start_workflow(
            workflow_name=workflow_name,
            execution_name=execution_name,
            context={
                "project_name": project_name,
                "phase": phase_id,
                "actor": options.actor,
                "source": "project_lifecycle",
            },
        )
        if "error" in started:
            raise Exception(started["error"])

        try:
            visual_result = _run_visual_validation_if_configured(project_name, phase_binding, lifecycle, options)
        except Exception as exc:
            visual_error = str(exc)
            run_status = "failed"
        if run_status != "failed" and isinstance(visual_result, dict):
            visual_status = str(visual_result.get("status", "")).lower()
            if visual_status in {"failed", "error"}:
                run_status = "failed"
    finally:
        finished_at = _now_iso()
        _release_run_lock(project_name)

    duration_ms = int((time.monotonic() - timer_start) * 1000)

    run_record = {
        "run_id": run_id,
        "project_name": project_name,
        "phase": phase_id,
        "actor": options.actor,
        "status": run_status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "workflow": {
            "workflow_name": workflow_name,
            "template": template_id,
            "stage": phase_binding.get("workflow_stage", ""),
            "execution": started,
        },
        "visual_validation": visual_result,
        "error": visual_error,
    }

    run_file = _runs_path(project_name) / f"{run_id}.json"
    run_file.write_text(json.dumps(run_record, indent=2) + "\n", encoding="utf-8")
    retention = lifecycle.get("retention", {}) if isinstance(lifecycle.get("retention"), dict) else {}
    max_runs = int(retention.get("max_runs", 100) or 100)
    _apply_run_retention(project_name, max_runs=max_runs)

    lifecycle["current_phase"] = phase_id
    lifecycle["last_run"] = {
        "run_id": run_id,
        "phase": phase_id,
        "status": run_record["status"],
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
    }
    _write_lifecycle(project_name, lifecycle)
    PrintStyle(font_color="blue", italic=True, padding=False).print(
        f"Lifecycle run {run_id} project={project_name} phase={phase_id} actor={options.actor} "
        f"status={run_status} duration_ms={duration_ms}"
    )

    return run_record


def _build_schedule_prompt(project_name: str, phase: str, run_visual: bool) -> str:
    visual_flag = "true" if run_visual else "false"
    return (
        "Run project lifecycle phase automation. "
        f"Use tool `project_lifecycle` with action `run_phase`, project_name `{project_name}`, "
        f"phase `{phase}`, run_visual `{visual_flag}`, actor `scheduler`."
    )


async def add_phase_schedule(
    project_name: str,
    phase: str,
    cron: str,
    timezone_name: str | None = None,
    run_visual: bool = True,
    actor: str = "system",
) -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)

    phase_id = _slug(phase)
    if phase_id not in lifecycle.get("phase_bindings", {}):
        raise Exception(f"Unknown lifecycle phase: {phase}")

    parts = [p.strip() for p in str(cron).split(" ") if p.strip()]
    if len(parts) != 5:
        raise Exception("cron must have 5 fields: minute hour day month weekday")

    from python.helpers.task_scheduler import ScheduledTask, TaskSchedule, TaskScheduler, serialize_task

    scheduler = TaskScheduler.get()
    await scheduler.reload()

    existing = (lifecycle.get("schedules") or {}).get(phase_id)
    if isinstance(existing, dict) and existing.get("task_id"):
        await scheduler.remove_task_by_uuid(str(existing["task_id"]))

    project_meta = projects.load_basic_project_data(project_name)
    schedule = TaskSchedule(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        weekday=parts[4],
        timezone=timezone_name or "UTC",
    )

    task = ScheduledTask.create(
        name=f"Lifecycle {project_name}:{phase_id}",
        system_prompt="You are running an automated project lifecycle phase task.",
        prompt=_build_schedule_prompt(project_name, phase_id, run_visual),
        schedule=schedule,
        attachments=[],
        project_name=project_name,
        project_color=project_meta.get("color") or None,
    )

    await scheduler.add_task(task)

    lifecycle.setdefault("schedules", {})[phase_id] = {
        "task_id": task.uuid,
        "cron": cron,
        "timezone": schedule.timezone,
        "run_visual": bool(run_visual),
        "updated_at": _now_iso(),
    }
    _write_lifecycle(project_name, lifecycle)

    return {
        "phase": phase_id,
        "schedule": lifecycle["schedules"][phase_id],
        "task": serialize_task(task),
    }


async def remove_phase_schedule(project_name: str, phase: str, actor: str = "system") -> dict[str, Any]:
    lifecycle = load_lifecycle(project_name)
    _require_access(lifecycle, actor)

    phase_id = _slug(phase)
    schedules = lifecycle.setdefault("schedules", {})
    current = schedules.get(phase_id)
    if not isinstance(current, dict) or not current.get("task_id"):
        return {"phase": phase_id, "removed": False, "reason": "No schedule configured"}

    from python.helpers.task_scheduler import TaskScheduler

    scheduler = TaskScheduler.get()
    await scheduler.reload()
    await scheduler.remove_task_by_uuid(str(current["task_id"]))

    del schedules[phase_id]
    _write_lifecycle(project_name, lifecycle)
    return {"phase": phase_id, "removed": True}
