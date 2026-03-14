from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from python.helpers import project_lifecycle, projects


def _new_project_name() -> str:
    return f"pl_{uuid4().hex[:10]}"


def _create_project(name: str) -> None:
    projects.create_project(
        name,
        projects.BasicProjectData(
            title=f"PL {name}",
            description="project lifecycle test",
            instructions="",
            color="#0055aa",
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


def test_lifecycle_defaults_and_set_phase_round_trip():
    project_name = _new_project_name()
    _create_project(project_name)
    try:
        lifecycle = project_lifecycle.load_lifecycle(project_name)
        assert lifecycle["lifecycle_model"] == "hybrid"
        assert lifecycle["current_phase"] == "design"
        assert "development" in lifecycle["phase_bindings"]

        updated = project_lifecycle.set_phase(project_name, "testing")
        assert updated["current_phase"] == "testing"

        reloaded = project_lifecycle.load_lifecycle(project_name)
        assert reloaded["current_phase"] == "testing"
    finally:
        projects.delete_project(project_name)


def test_run_phase_creates_run_record(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)

    class FakeManager:
        def __init__(self):
            self._created = False

        def get_workflow(self, name=None, workflow_id=None):
            if self._created:
                return {"workflow_id": 7, "name": name}
            return {"error": "Workflow not found"}

        def create_from_template(self, template_path, name, customizations=None):
            self._created = True
            return {"workflow_id": 7, "name": name, "status": "created"}

        def start_workflow(self, workflow_id=None, workflow_name=None, execution_name=None, context=None):
            return {
                "execution_id": 99,
                "workflow_id": 7,
                "workflow_name": workflow_name,
                "status": "running",
            }

    monkeypatch.setattr(project_lifecycle, "_get_workflow_manager", lambda: FakeManager())
    monkeypatch.setattr(project_lifecycle, "_run_visual_validation_if_configured", lambda *args, **kwargs: None)

    try:
        run = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=False, actor="system"),
        )
        assert run["status"] == "started"
        assert run["workflow"]["execution"]["execution_id"] == 99

        run_file = Path(projects.get_project_lifecycle_folder(project_name, "runs", f"{run['run_id']}.json"))
        assert run_file.exists()

        rows = project_lifecycle.list_phase_runs(project_name, phase="design", limit=10)
        assert rows
        assert rows[0]["phase"] == "design"
    finally:
        projects.delete_project(project_name)


def test_run_phase_requires_visual_suite_when_enabled(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)

    class FakeManager:
        def __init__(self):
            self._created = False

        def get_workflow(self, name=None, workflow_id=None):
            if self._created:
                return {"workflow_id": 7, "name": name}
            return {"error": "Workflow not found"}

        def create_from_template(self, template_path, name, customizations=None):
            self._created = True
            return {"workflow_id": 7, "name": name, "status": "created"}

        def start_workflow(self, workflow_id=None, workflow_name=None, execution_name=None, context=None):
            return {
                "execution_id": 99,
                "workflow_id": 7,
                "workflow_name": workflow_name,
                "status": "running",
            }

    monkeypatch.setattr(project_lifecycle, "_get_workflow_manager", lambda: FakeManager())

    try:
        run = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=True, actor="alice"),
        )
        assert run["status"] == "failed"
        assert "no visual_suite is configured" in str(run.get("error", "")).lower()
    finally:
        projects.delete_project(project_name)


def test_run_phase_uses_actor_bound_browser_profile(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)

    class FakeManager:
        def __init__(self):
            self._created = False

        def get_workflow(self, name=None, workflow_id=None):
            if self._created:
                return {"workflow_id": 7, "name": name}
            return {"error": "Workflow not found"}

        def create_from_template(self, template_path, name, customizations=None):
            self._created = True
            return {"workflow_id": 7, "name": name, "status": "created"}

        def start_workflow(self, workflow_id=None, workflow_name=None, execution_name=None, context=None):
            return {
                "execution_id": 99,
                "workflow_id": 7,
                "workflow_name": workflow_name,
                "status": "running",
            }

    captured: dict[str, str] = {}

    def fake_run_suite(project_name: str, suite_name: str, options):
        captured["profile_name"] = options.profile_name or ""
        captured["suite_name"] = suite_name
        return {"status": "passed", "run_id": "vr_test"}

    monkeypatch.setattr(project_lifecycle, "_get_workflow_manager", lambda: FakeManager())
    monkeypatch.setattr(project_lifecycle.project_validation, "run_suite", fake_run_suite)

    try:
        project_lifecycle.upsert_lifecycle(
            project_name,
            {
                "phase_bindings": {
                    "design": {
                        "visual_suite": "google-auth-smoke",
                    }
                },
                "browser": {
                    "profile_name": "fallback-profile",
                    "profiles": {"alice": "alice-google-profile"},
                },
            },
        )
        run = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=True, actor="alice"),
        )
        assert run["status"] == "started"
        assert captured["suite_name"] == "google-auth-smoke"
        assert captured["profile_name"] == "alice-google-profile"
    finally:
        projects.delete_project(project_name)


def test_run_phase_records_failed_visual_validation(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)

    class FakeManager:
        def __init__(self):
            self._created = False

        def get_workflow(self, name=None, workflow_id=None):
            if self._created:
                return {"workflow_id": 7, "name": name}
            return {"error": "Workflow not found"}

        def create_from_template(self, template_path, name, customizations=None):
            self._created = True
            return {"workflow_id": 7, "name": name, "status": "created"}

        def start_workflow(self, workflow_id=None, workflow_name=None, execution_name=None, context=None):
            return {
                "execution_id": 99,
                "workflow_id": 7,
                "workflow_name": workflow_name,
                "status": "running",
            }

    def fake_run_suite(*args, **kwargs):
        raise Exception("mock visual failure")

    monkeypatch.setattr(project_lifecycle, "_get_workflow_manager", lambda: FakeManager())
    monkeypatch.setattr(project_lifecycle.project_validation, "run_suite", fake_run_suite)

    try:
        project_lifecycle.upsert_lifecycle(
            project_name,
            {
                "phase_bindings": {
                    "design": {
                        "visual_suite": "google-auth-smoke",
                    }
                },
                "browser": {
                    "profile_name": "fallback-profile",
                },
            },
        )
        run = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=True, actor="alice"),
        )

        assert run["status"] == "failed"
        assert "mock visual failure" in str(run.get("error", ""))

        rows = project_lifecycle.list_phase_runs(project_name, phase="design", limit=10)
        assert rows
        assert rows[0]["run_id"] == run["run_id"]
        assert rows[0]["status"] == "failed"
    finally:
        projects.delete_project(project_name)


def test_run_phase_rejects_when_lock_exists(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)
    try:
        lock_file = Path(projects.get_project_lifecycle_folder(project_name, "run.lock"))
        lock_file.write_text('{"pid":1,"started_at":"2099-01-01T00:00:00+00:00"}\n', encoding="utf-8")

        raised = False
        try:
            project_lifecycle.run_phase(
                project_name,
                phase="design",
                options=project_lifecycle.PhaseRunOptions(run_visual=False, actor="system"),
            )
        except Exception as exc:
            raised = True
            assert "already in progress" in str(exc).lower()
        assert raised is True
    finally:
        projects.delete_project(project_name)


def test_run_retention_keeps_newest_runs(monkeypatch):
    project_name = _new_project_name()
    _create_project(project_name)

    class FakeManager:
        def __init__(self):
            self._created = False

        def get_workflow(self, name=None, workflow_id=None):
            if self._created:
                return {"workflow_id": 7, "name": name}
            return {"error": "Workflow not found"}

        def create_from_template(self, template_path, name, customizations=None):
            self._created = True
            return {"workflow_id": 7, "name": name, "status": "created"}

        def start_workflow(self, workflow_id=None, workflow_name=None, execution_name=None, context=None):
            return {
                "execution_id": 99,
                "workflow_id": 7,
                "workflow_name": workflow_name,
                "status": "running",
            }

    monkeypatch.setattr(project_lifecycle, "_get_workflow_manager", lambda: FakeManager())
    monkeypatch.setattr(project_lifecycle, "_run_visual_validation_if_configured", lambda *args, **kwargs: None)

    try:
        project_lifecycle.upsert_lifecycle(project_name, {"retention": {"max_runs": 2}})
        first = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=False, actor="system"),
        )
        second = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=False, actor="system"),
        )
        third = project_lifecycle.run_phase(
            project_name,
            phase="design",
            options=project_lifecycle.PhaseRunOptions(run_visual=False, actor="system"),
        )

        rows = project_lifecycle.list_phase_runs(project_name, phase="design", limit=10)
        ids = {row["run_id"] for row in rows}
        assert len(rows) == 2
        assert first["run_id"] not in ids
        assert second["run_id"] in ids
        assert third["run_id"] in ids
        assert "duration_ms" in rows[0]
        assert "finished_at" in rows[0]
    finally:
        projects.delete_project(project_name)
