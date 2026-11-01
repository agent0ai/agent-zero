import asyncio
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import threading
import types
import zipfile
from datetime import UTC
from pathlib import Path

import pytest
from flask import Flask, request

from helpers import backup, localization, login
from helpers.api import csrf_protect, requires_auth
from helpers.backup import BackupService
from helpers.backup_jobs import BackupJobs


@pytest.fixture
def backup_api(tmp_path, monkeypatch):
    """Use real HTTP handlers and ZIP creation with isolated source files/chats."""
    entered, release, finished = (threading.Event() for _ in range(3))
    loops = []
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    clock = types.SimpleNamespace(
        now_iso=lambda: "2026-01-01T00:00:00+00:00",
        get_timezone=lambda: "UTC",
        get_tzinfo=lambda: UTC,
    )
    monkeypatch.setattr(
        backup, "Localization", types.SimpleNamespace(get=lambda: clock)
    )

    def save_chats():
        loops.append(asyncio.get_running_loop())
        entered.set()
        assert release.wait(5), "test did not release backup worker"

    persist = types.ModuleType("helpers.persist_chat")
    persist.save_tmp_chats = save_chats
    with monkeypatch.context() as imports:
        imports.setitem(sys.modules, "helpers.persist_chat", persist)
        spec = importlib.util.spec_from_file_location(
            "backup_create_under_test",
            Path(__file__).parents[1] / "api/backup_create.py",
        )
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)

    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.txt").write_bytes(b"backup payload\n")
    service = BackupService()
    service.agent_zero_root = str(source)
    service.base_paths = {str(source): str(source)}
    monkeypatch.setattr(api, "BackupService", lambda: service)
    jobs = BackupJobs()
    run = jobs._run

    def run_and_signal(*args):
        try:
            run(*args)
        finally:
            finished.set()

    monkeypatch.setattr(jobs, "_run", run_and_signal)
    monkeypatch.setattr(api, "backup_jobs", jobs, raising=False)
    monkeypatch.setattr(login, "get_credentials_hash", lambda: "test-auth")
    app = Flask(__name__)
    app.secret_key = "test-only"
    handler = api.BackupCreate(app, threading.Lock())

    @app.route("/", endpoint="serve_index")
    def index():
        return "index"

    @app.route("/login", endpoint="login_handler")
    def login_page():
        return "login"

    @app.post("/api/backup_create")
    @requires_auth
    @csrf_protect
    async def create_backup():
        return await handler.handle_request(request)

    client = app.test_client()
    with client.session_transaction() as session:
        session["authentication"] = "test-auth"
        session["csrf_token"] = "test-csrf"

    responses = []

    def post(**data):
        response = client.post(
            "/api/backup_create", json=data, headers={"X-CSRF-Token": "test-csrf"}
        )
        responses.append(response)
        return response

    env = types.SimpleNamespace(
        post=post,
        client=client,
        app=app,
        jobs=jobs,
        api=api,
        service=service,
        entered=entered,
        loops=loops,
        release=release,
        finished=finished,
    )
    yield env
    release.set()
    if jobs._job and jobs._job.status == "running":
        assert finished.wait(5)
    for response in responses:
        response.close()
    if jobs._job:
        jobs._expire(jobs._job)


def start(env, **kwargs):
    response = env.post(
        action="start", include_patterns=["**"], backup_name="archive", **kwargs
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "running"
    assert env.entered.wait(5)
    return data["job_id"]


def complete(env):
    env.release.set()
    assert env.finished.wait(5)


def test_start_returns_during_blocked_work_and_downloads_real_archive(backup_api):
    env = backup_api
    job_id = start(env)
    assert not env.release.is_set()
    assert env.post(action="status", job_id=job_id).get_json()["status"] == "running"
    assert env.post(action="download", job_id=job_id).status_code == 409
    assert env.post(action="start").status_code == 409
    complete(env)
    assert env.loops[0].is_closed()

    status = env.post(action="status", job_id=job_id).get_json()
    assert status == {"success": True, "job_id": job_id, "status": "completed"}
    response = env.post(action="download", job_id=job_id)
    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    assert "archive.zip" in response.headers["Content-Disposition"]
    assert response.content_length == len(response.data)
    assert (
        response.headers["X-Content-SHA256"]
        == hashlib.sha256(response.data).hexdigest()
    )
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        payload = next(
            name for name in archive.namelist() if name.endswith("/payload.txt")
        )
        assert archive.read(payload) == b"backup payload\n"
        metadata = json.loads(archive.read("metadata.json"))
        assert metadata["backup_name"] == "archive"
        assert metadata["total_files"] == 1
    response.close()
    response.close()
    assert not env.jobs._job.downloads


def test_archive_creation_keeps_localization_state_isolated(backup_api, monkeypatch):
    def unexpected_localization(*args, **kwargs):
        raise AssertionError("backup fixture accessed process localization")

    monkeypatch.setattr(localization.Localization, "get", unexpected_localization)
    job_id = start(backup_api)
    complete(backup_api)
    response = backup_api.post(action="download", job_id=job_id)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        metadata = json.loads(archive.read("metadata.json"))
        assert metadata["timestamp"] == "2026-01-01T00:00:00+00:00"
        assert metadata["environment_info"]["timezone"] == "UTC"


def test_download_uses_digest_prepared_by_worker(backup_api, monkeypatch):
    job_id = start(backup_api)
    complete(backup_api)

    def unexpected_hash(*args, **kwargs):
        raise AssertionError("download recalculated archive digest")

    monkeypatch.setattr(hashlib, "file_digest", unexpected_hash)
    for _ in range(2):
        response = backup_api.post(action="download", job_id=job_id)
        assert response.status_code == 200
        assert (
            response.headers["X-Content-SHA256"]
            == hashlib.sha256(response.data).hexdigest()
        )
        response.close()


def test_archive_expires_after_an_active_download_closes(backup_api):
    env = backup_api
    job_id = start(env)
    complete(env)
    job = env.jobs._job
    response = env.post(action="download", job_id=job_id)
    env.jobs._expire(job)
    assert job.path.exists()
    assert env.post(action="status", job_id=job_id).status_code == 404
    assert env.post(action="start").status_code == 409
    assert zipfile.is_zipfile(io.BytesIO(response.data))
    response.close()
    assert not Path(job.directory.name).exists()
    assert env.jobs._job is None


def test_next_backup_replaces_completed_archive(backup_api):
    env = backup_api
    job_id = start(env)
    complete(env)
    old_job = env.jobs._job
    env.finished.clear()
    next_id = start(env)
    complete(env)
    assert next_id != job_id
    assert not Path(old_job.directory.name).exists()
    assert env.post(action="status", job_id=job_id).status_code == 404


def test_failed_backup_reports_error_and_cleans_partial_archive(
    backup_api, monkeypatch
):
    env = backup_api

    async def fail(**kwargs):
        Path(kwargs["output_path"]).write_bytes(b"partial zip")
        raise OSError("private filesystem diagnostic")

    monkeypatch.setattr(env.service, "create_backup", fail)
    job_id = start(env)
    complete(env)
    result = env.post(action="status", job_id=job_id).get_json()
    assert result["status"] == "failed"
    assert "server log" in result["error"]
    assert "private filesystem" not in result["error"]
    assert not Path(env.jobs._job.directory.name).exists()
    assert env.post(action="download", job_id=job_id).status_code == 409


@pytest.mark.parametrize("action", ["start", "status", "download"])
def test_job_actions_require_authentication_and_csrf(backup_api, action):
    env = backup_api
    assert env.api.BackupCreate.requires_auth()
    assert env.api.BackupCreate.requires_csrf()
    assert (
        env.client.post("/api/backup_create", json={"action": action}).status_code
        == 403
    )
    with env.client.session_transaction() as session:
        session.pop("authentication")
    assert env.post(action=action).status_code == 302
    assert not env.entered.is_set()


def test_unknown_job_and_action_return_json_errors(backup_api):
    env = backup_api
    for action in ("status", "download"):
        response = env.post(action=action, job_id="../../private.zip")
        assert response.status_code == 404
        assert response.get_json()["success"] is False
    assert env.post(action="other").status_code == 400
    assert env.post(action="start", backup_name="bad\r\nname").status_code == 400
    assert not env.entered.is_set()


def test_legacy_request_still_returns_zip(backup_api):
    env = backup_api
    env.release.set()
    response = env.post(patterns="**", backup_name="legacy")
    assert response.status_code == 200
    assert zipfile.is_zipfile(io.BytesIO(response.data))
    assert "legacy.zip" in response.headers["Content-Disposition"]
    response.close()
    assert env.jobs._job is None
