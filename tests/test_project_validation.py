from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from python.helpers import project_validation, projects


def _new_project_name() -> str:
    return f"pv_{uuid4().hex[:10]}"


def _create_project(name: str) -> None:
    projects.create_project(
        name,
        projects.BasicProjectData(
            title=f"PV {name}",
            description="project validation test",
            instructions="",
            color="#123456",
            memory="own",
            file_structure={
                "enabled": True,
                "max_depth": 2,
                "max_files": 10,
                "max_folders": 10,
                "max_lines": 100,
                "gitignore": "",
            },
        ),
    )


def test_suite_crud_round_trip():
    project_name = _new_project_name()
    _create_project(project_name)
    try:
        saved = project_validation.save_suite(
            project_name,
            "smoke-auth",
            {
                "name": "Smoke Auth",
                "description": "basic auth flow",
                "base_url": "https://example.test",
                "steps": [
                    {"name": "Open login", "action": "open", "args": ["/login"]},
                    {"name": "Snapshot", "action": "snapshot", "args": ["-i"]},
                ],
            },
        )
        assert saved["name"] == "Smoke Auth"

        suites = project_validation.list_suites(project_name)
        assert any(s["slug"] == "smoke-auth" for s in suites)

        loaded = project_validation.load_suite(project_name, "smoke-auth")
        assert loaded["base_url"] == "https://example.test"
        assert len(loaded["steps"]) == 2
    finally:
        projects.delete_project(project_name)


def test_run_suite_persists_run_json(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)
    try:
        project_validation.save_suite(
            project_name,
            "smoke",
            {
                "name": "Smoke",
                "base_url": "https://example.test",
                "steps": [
                    {"name": "Open", "action": "open", "args": ["/"]},
                    {"name": "Shot", "action": "screenshot"},
                ],
            },
        )

        def fake_run_browser_command(project_name: str, options, command: list[str], timeout_seconds: int):
            return {
                "command": ["agent-browser", *command],
                "exit_code": 0,
                "stdout": "ok",
                "stderr": "",
                "ok": True,
            }

        monkeypatch.setattr(project_validation, "_run_browser_command", fake_run_browser_command)
        run = project_validation.run_suite(
            project_name,
            "smoke",
            project_validation.RunOptions(headed=False, profile_name="qa"),
        )

        assert run["status"] == "passed"
        assert run["run_id"].startswith("vr_")
        run_json = Path(projects.get_project_validation_folder(project_name, "runs", run["run_id"], "run.json"))
        assert run_json.exists()
    finally:
        projects.delete_project(project_name)
