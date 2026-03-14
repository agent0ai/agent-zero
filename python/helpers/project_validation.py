from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from python.helpers import files, projects


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    raw = (value or "").strip().lower()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in raw)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-_") or "suite"


def _project_exists(name: str) -> None:
    projects.load_basic_project_data(name)


def _suites_dir(project_name: str) -> Path:
    return Path(projects.get_project_validation_folder(project_name, "suites"))


def _runs_dir(project_name: str) -> Path:
    return Path(projects.get_project_validation_folder(project_name, "runs"))


def _profiles_dir(project_name: str) -> Path:
    return Path(projects.get_project_validation_folder(project_name, "profiles"))


def _suite_path(project_name: str, suite_name: str) -> Path:
    return _suites_dir(project_name) / f"{_slug(suite_name)}.json"


def _run_path(project_name: str, run_id: str) -> Path:
    return _runs_dir(project_name) / run_id / "run.json"


def _ensure_validation_dirs(project_name: str) -> None:
    files.create_dir(str(_suites_dir(project_name)))
    files.create_dir(str(_runs_dir(project_name)))
    files.create_dir(str(_profiles_dir(project_name)))


def list_suites(project_name: str) -> list[dict[str, Any]]:
    _project_exists(project_name)
    _ensure_validation_dirs(project_name)

    suites: list[dict[str, Any]] = []
    for path in sorted(_suites_dir(project_name).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            suites.append(
                {
                    "name": data.get("name", path.stem),
                    "slug": path.stem,
                    "description": data.get("description", ""),
                    "steps_count": len(data.get("steps", [])) if isinstance(data.get("steps"), list) else 0,
                    "updated_at": data.get("updated_at", ""),
                }
            )
        except Exception:
            continue
    return suites


def load_suite(project_name: str, suite_name: str) -> dict[str, Any]:
    _project_exists(project_name)
    path = _suite_path(project_name, suite_name)
    if not path.exists():
        raise Exception(f"Suite not found: {suite_name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Exception(f"Invalid suite format: {suite_name}")
    return data


def save_suite(project_name: str, suite_name: str, suite_data: dict[str, Any]) -> dict[str, Any]:
    _project_exists(project_name)
    _ensure_validation_dirs(project_name)

    steps = suite_data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise Exception("Suite must include a non-empty 'steps' list")

    path = _suite_path(project_name, suite_name)
    previous: dict[str, Any] = {}
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(previous, dict):
                previous = {}
        except Exception:
            previous = {}

    payload = {
        "name": suite_data.get("name", suite_name),
        "description": suite_data.get("description", ""),
        "base_url": suite_data.get("base_url", ""),
        "created_at": previous.get("created_at", _now_iso()),
        "updated_at": _now_iso(),
        "steps": steps,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def delete_suite(project_name: str, suite_name: str) -> str:
    _project_exists(project_name)
    path = _suite_path(project_name, suite_name)
    if not path.exists():
        raise Exception(f"Suite not found: {suite_name}")
    path.unlink()
    return suite_name


def list_runs(project_name: str, limit: int = 25) -> list[dict[str, Any]]:
    _project_exists(project_name)
    _ensure_validation_dirs(project_name)

    rows: list[dict[str, Any]] = []
    run_files = sorted(_runs_dir(project_name).glob("*/run.json"), reverse=True)
    for run_file in run_files[: max(limit, 1)]:
        try:
            data = json.loads(run_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                rows.append(data)
        except Exception:
            continue
    return rows


def get_run(project_name: str, run_id: str) -> dict[str, Any]:
    _project_exists(project_name)
    path = _run_path(project_name, run_id)
    if not path.exists():
        raise Exception(f"Run not found: {run_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Exception(f"Invalid run format: {run_id}")
    return data


@dataclass
class RunOptions:
    headed: bool = True
    session: str | None = None
    cdp: str | None = None
    profile_name: str | None = None
    per_step_timeout_seconds: int = 120
    base_url_override: str | None = None


def _build_prefix(project_name: str, options: RunOptions) -> list[str]:
    cmd = ["agent-browser"]
    if options.headed:
        cmd.append("--headed")
    if options.session:
        cmd.extend(["--session", options.session])
    if options.cdp:
        cmd.extend(["--cdp", options.cdp])
    if options.profile_name:
        profile_dir = _profiles_dir(project_name) / _slug(options.profile_name)
        files.create_dir(str(profile_dir))
        cmd.extend(["--profile", str(profile_dir)])
    return cmd


def _run_browser_command(
    project_name: str,
    options: RunOptions,
    command: list[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    full_cmd = _build_prefix(project_name, options) + command
    proc = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": full_cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
    }


def run_suite(project_name: str, suite_name: str, options: RunOptions) -> dict[str, Any]:
    _project_exists(project_name)
    _ensure_validation_dirs(project_name)
    suite = load_suite(project_name, suite_name)

    run_id = f"vr_{uuid4().hex[:12]}"
    run_dir = _runs_dir(project_name) / run_id
    artifacts_dir = run_dir / "artifacts"
    files.create_dir(str(artifacts_dir))

    suite_steps = suite.get("steps", [])
    if not isinstance(suite_steps, list) or not suite_steps:
        raise Exception("Suite has no steps")

    run_record: dict[str, Any] = {
        "run_id": run_id,
        "project_name": project_name,
        "suite_name": suite.get("name", suite_name),
        "suite_slug": _slug(suite_name),
        "status": "running",
        "started_at": _now_iso(),
        "ended_at": None,
        "options": {
            "headed": options.headed,
            "session": options.session,
            "cdp": options.cdp,
            "profile_name": options.profile_name,
            "base_url_override": options.base_url_override,
        },
        "steps": [],
    }

    base_url = options.base_url_override or suite.get("base_url", "")
    failed = False

    for idx, step in enumerate(suite_steps, start=1):
        if not isinstance(step, dict):
            continue
        action = str(step.get("action", "")).strip().lower()
        args = step.get("args", [])
        if not isinstance(args, list):
            args = []

        if action == "open" and base_url and args:
            first = str(args[0])
            if first.startswith("/"):
                args[0] = base_url.rstrip("/") + first

        if action == "screenshot":
            default_name = step.get("path") or f"step-{idx:02d}.png"
            artifact_path = artifacts_dir / str(default_name)
            args = [str(artifact_path)]
            if bool(step.get("full_page", False)):
                args.insert(0, "--full")

        if not action:
            continue

        cmd = [action] + [str(v) for v in args]
        timeout_seconds = int(step.get("timeout_seconds") or options.per_step_timeout_seconds)
        started_at = _now_iso()
        result = _run_browser_command(project_name, options, cmd, timeout_seconds)
        ended_at = _now_iso()

        step_record = {
            "index": idx,
            "name": step.get("name", f"Step {idx}"),
            "action": action,
            "args": args,
            "started_at": started_at,
            "ended_at": ended_at,
            "result": result,
        }
        run_record["steps"].append(step_record)

        if not result["ok"]:
            failed = True
            break

    run_record["status"] = "failed" if failed else "passed"
    run_record["ended_at"] = _now_iso()

    # Always capture one final screenshot artifact if possible
    final_path = artifacts_dir / "final.png"
    final_shot = _run_browser_command(
        project_name,
        options,
        ["screenshot", str(final_path)],
        options.per_step_timeout_seconds,
    )
    run_record["final_screenshot"] = str(final_path) if final_shot.get("ok") else None
    run_record["final_screenshot_capture"] = final_shot

    run_json = run_dir / "run.json"
    run_json.write_text(json.dumps(run_record, indent=2) + "\n", encoding="utf-8")
    return run_record
