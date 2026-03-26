#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


OFFICIAL_REPO_URL = os.environ.get(
    "A0_SELF_UPDATE_REMOTE_URL",
    "https://github.com/agent0ai/agent-zero.git",
)
REPO_DIR = Path("/a0")
TRIGGER_FILE = Path("/exe/a0-self-update.yaml")
STATUS_FILE = Path("/exe/a0-self-update-status.yaml")
LOG_FILE = Path("/exe/a0-self-update.log")
DEFAULT_HEALTH_URL = os.environ.get(
    "A0_SELF_UPDATE_HEALTH_URL",
    "http://127.0.0.1:80/api/health",
)
DEFAULT_HEALTH_TIMEOUT_SECONDS = int(
    os.environ.get("A0_SELF_UPDATE_HEALTH_TIMEOUT_SECONDS", "120")
)
DEFAULT_HEALTH_POLL_INTERVAL_SECONDS = float(
    os.environ.get("A0_SELF_UPDATE_HEALTH_POLL_INTERVAL_SECONDS", "2")
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class AttemptLogger:
    def __init__(self, path: Path):
        self.path = path

    def reset(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def log(self, message: str = "") -> None:
        line = f"[{now_iso()}] {message}".rstrip()
        print(f"[a0-self-update] {message}", flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def log_block(self, title: str, content: str) -> None:
        cleaned = content.rstrip()
        self.log(f"{title}:")
        if not cleaned:
            self.log("(empty)")
            return
        with self.path.open("a", encoding="utf-8") as handle:
            for line in cleaned.splitlines():
                handle.write(f"    {line}\n")


class NullLogger:
    def reset(self) -> None:
        return

    def log(self, message: str = "") -> None:
        return

    def log_block(self, title: str, content: str) -> None:
        return


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def write_status(payload: dict[str, Any]) -> None:
    write_yaml(STATUS_FILE, payload)


def git_output(repo_dir: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return completed.stdout.strip()


def normalize_describe_to_version(describe: str) -> str:
    match = re.fullmatch(r"(.+)-\d+-g[0-9a-f]+", describe)
    if match:
        return match.group(1)
    return describe


def get_repo_version_info(repo_dir: Path) -> dict[str, str]:
    describe = git_output(repo_dir, "describe", "--tags", "--always")
    commit = git_output(repo_dir, "rev-parse", "HEAD")
    branch = git_optional_output(repo_dir, "branch", "--show-current")
    return {
        "branch": branch,
        "describe": describe,
        "short_tag": normalize_describe_to_version(describe),
        "commit": commit,
        "short_commit": commit[:7],
    }


def git_optional_output(repo_dir: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.exists():
        shutil.rmtree(path)


def get_repo_relative_path(repo_dir: Path, path: Path) -> str | None:
    try:
        return path.resolve().relative_to(repo_dir.resolve()).as_posix()
    except ValueError:
        return None


def sanitize_filename(name: str, default_name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        raw = default_name
    raw = Path(raw).name
    raw = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-") or default_name
    if not raw.lower().endswith(".zip"):
        raw = f"{raw}.zip"
    return raw


def resolve_backup_destination(
    directory: Path,
    filename: str,
    conflict_policy: str,
) -> Path:
    normalized_policy = conflict_policy.strip().lower()
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / filename
    if not destination.exists():
        return destination

    if normalized_policy == "overwrite":
        remove_path(destination)
        return destination
    if normalized_policy == "fail":
        raise FileExistsError(f"Backup file already exists: {destination}")
    if normalized_policy != "rename":
        raise ValueError("backup_conflict_policy must be rename, overwrite, or fail.")

    stem = destination.stem
    suffix = destination.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def create_usr_backup(
    *,
    repo_dir: Path,
    backup_path: str,
    backup_name: str,
    conflict_policy: str,
    logger: AttemptLogger,
) -> Path:
    usr_dir = repo_dir / "usr"
    if not usr_dir.exists():
        raise FileNotFoundError(f"User directory not found: {usr_dir}")

    destination_dir = Path(backup_path)
    if not destination_dir.is_absolute():
        destination_dir = (repo_dir / destination_dir).resolve()
    else:
        destination_dir = destination_dir.resolve()
    destination_name = sanitize_filename(backup_name, "agent-zero-usr-backup.zip")
    destination = resolve_backup_destination(destination_dir, destination_name, conflict_policy)

    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)
    temporary_backup = Path(temp_path)

    try:
        with zipfile.ZipFile(
            temporary_backup,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            for root, _, files in os.walk(usr_dir):
                root_path = Path(root)
                for filename in files:
                    source_file = root_path / filename
                    archive_name = Path("usr") / source_file.relative_to(usr_dir)
                    archive.write(source_file, archive_name.as_posix())

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temporary_backup), str(destination))
        logger.log(f"Created usr backup at {destination}")
        return destination
    finally:
        if temporary_backup.exists():
            temporary_backup.unlink(missing_ok=True)


def run_command(
    command: list[str],
    *,
    cwd: Path | None,
    logger: AttemptLogger,
    error_message: str | None = None,
) -> subprocess.CompletedProcess[str]:
    logger.log(f"$ {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.stdout:
        logger.log_block("stdout", completed.stdout)
    if completed.stderr:
        logger.log_block("stderr", completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            error_message
            or f"Command failed with exit code {completed.returncode}: {' '.join(command)}"
        )
    return completed


def has_local_rollback_changes(repo_dir: Path) -> bool:
    status = git_output(repo_dir, "status", "--porcelain=v1", "--untracked-files=all")
    return bool(status.strip())


def get_top_stash_ref(repo_dir: Path) -> str:
    return git_optional_output(repo_dir, "stash", "list", "--format=%gd", "-n", "1")


def create_rollback_stash(repo_dir: Path, logger: AttemptLogger) -> str | None:
    if not has_local_rollback_changes(repo_dir):
        logger.log("No tracked or non-ignored untracked changes need rollback protection.")
        return None

    previous_top = get_top_stash_ref(repo_dir)
    message = f"a0-self-update rollback snapshot {now_iso()}"
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "stash",
            "push",
            "--include-untracked",
            "--message",
            message,
        ],
        cwd=None,
        logger=logger,
        error_message="Failed to save local tracked/untracked changes before updating.",
    )
    stash_ref = get_top_stash_ref(repo_dir)
    if not stash_ref or stash_ref == previous_top:
        raise RuntimeError("Failed to create the pre-update rollback stash.")
    logger.log(
        f"Saved local tracked/untracked changes into {stash_ref}. "
        "Ignored files stay in place and are not stashed."
    )
    return stash_ref


def drop_stash(repo_dir: Path, stash_ref: str, logger: AttemptLogger) -> None:
    if not stash_ref:
        return
    run_command(
        ["git", "-C", str(repo_dir), "stash", "drop", stash_ref],
        cwd=None,
        logger=logger,
        error_message=f"Failed to drop temporary rollback stash {stash_ref}.",
    )


def apply_stash(repo_dir: Path, stash_ref: str, logger: AttemptLogger) -> None:
    if not stash_ref:
        return
    run_command(
        ["git", "-C", str(repo_dir), "stash", "apply", "--index", stash_ref],
        cwd=None,
        logger=logger,
        error_message=(
            f"Failed to restore local tracked/untracked changes from {stash_ref}. "
            "The stash entry has been kept so it can be recovered manually."
        ),
    )
    try:
        drop_stash(repo_dir, stash_ref, logger)
    except Exception as exc:
        logger.log(
            f"Rollback stash {stash_ref} was restored but could not be dropped automatically: {exc}"
        )


def clean_repo_worktree(
    repo_dir: Path,
    logger: AttemptLogger,
    *,
    exclude_paths: list[Path] | None = None,
) -> None:
    command = ["git", "-C", str(repo_dir), "clean", "-ffd"]
    for path in exclude_paths or []:
        relative_path = get_repo_relative_path(repo_dir, path)
        if relative_path:
            command.extend(["-e", relative_path])
    run_command(
        command,
        cwd=None,
        logger=logger,
        error_message="Failed to remove leftover non-ignored files after checkout.",
    )


def fetch_release_refs(repo_dir: Path, branch: str, tag: str, logger: AttemptLogger) -> None:
    remote_branch_ref = f"refs/remotes/a0-self-update/{branch}"
    logger.log(f"Fetching branch {branch} and tag {tag} from {OFFICIAL_REPO_URL}")
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "fetch",
            "--force",
            OFFICIAL_REPO_URL,
            f"+refs/heads/{branch}:{remote_branch_ref}",
            f"+refs/tags/{tag}:refs/tags/{tag}",
        ],
        cwd=None,
        logger=logger,
        error_message=f"Failed to fetch branch {branch} and tag {tag} from the official repository.",
    )
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "merge-base",
            "--is-ancestor",
            f"refs/tags/{tag}",
            remote_branch_ref,
        ],
        cwd=None,
        logger=logger,
        error_message=f"Requested tag {tag} is not reachable from official branch {branch}.",
    )


def checkout_target_release(
    repo_dir: Path,
    branch: str,
    tag: str,
    logger: AttemptLogger,
    *,
    exclude_paths: list[Path] | None = None,
) -> None:
    logger.log(f"Checking out branch {branch} at tag {tag}")
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "checkout",
            "-B",
            branch,
            f"refs/tags/{tag}",
        ],
        cwd=None,
        logger=logger,
        error_message=f"Failed to check out requested tag {tag} on branch {branch}.",
    )
    clean_repo_worktree(repo_dir, logger, exclude_paths=exclude_paths)


def restore_git_state(
    repo_dir: Path,
    *,
    head: str,
    branch: str,
    logger: AttemptLogger,
    exclude_paths: list[Path] | None = None,
) -> None:
    logger.log(f"Restoring repository state to commit {head}")
    if branch:
        run_command(
            [
                "git",
                "-C",
                str(repo_dir),
                "checkout",
                "-B",
                branch,
                head,
            ],
            cwd=None,
            logger=logger,
            error_message=f"Failed to restore branch {branch} to commit {head}.",
        )
    else:
        run_command(
            [
                "git",
                "-C",
                str(repo_dir),
                "checkout",
                "--detach",
                head,
            ],
            cwd=None,
            logger=logger,
            error_message=f"Failed to restore detached HEAD at commit {head}.",
        )
    clean_repo_worktree(repo_dir, logger, exclude_paths=exclude_paths)


def launch_ui_process(repo_dir: Path, logger: AttemptLogger) -> subprocess.Popen[bytes]:
    prepare_script = repo_dir / "prepare.py"
    if prepare_script.exists():
        logger.log("Running prepare.py before UI start")
        run_command([sys.executable, str(prepare_script), "--dockerized=true"], cwd=repo_dir, logger=logger)
    else:
        logger.log("prepare.py not found, skipping prepare step")

    logger.log("Starting Agent Zero UI")
    return subprocess.Popen(
        [
            sys.executable,
            str(repo_dir / "run_ui.py"),
            "--dockerized=true",
            "--port=80",
            "--host=0.0.0.0",
        ],
        cwd=repo_dir,
    )


def wait_for_health(
    process: subprocess.Popen[bytes],
    *,
    health_url: str,
    timeout_seconds: int,
    poll_interval_seconds: float,
    expected_version: str | None = None,
    logger: AttemptLogger,
) -> tuple[bool, dict[str, Any] | str]:
    deadline = time.monotonic() + timeout_seconds
    last_error = "Health check did not return a successful response."

    while time.monotonic() < deadline:
        if process.poll() is not None:
            return (
                False,
                f"UI process exited with code {process.returncode} before passing the health check.",
            )
        try:
            request = urllib.request.Request(
                health_url,
                headers={"Cache-Control": "no-cache"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                body = response.read().decode("utf-8")
                payload = json.loads(body) if body else {}
                git_info = payload.get("gitinfo") or {}
                current_version = (git_info.get("short_tag") or "").strip()
                if expected_version and current_version and current_version != expected_version:
                    last_error = (
                        f"Health check responded, but version {current_version} does not match "
                        f"expected {expected_version}."
                    )
                elif response.status == 200:
                    logger.log(f"Health check passed at {health_url}")
                    return True, payload
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)

        time.sleep(poll_interval_seconds)

    return False, last_error


def terminate_process(process: subprocess.Popen[bytes], timeout_seconds: int = 20) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def wait_for_process(process: subprocess.Popen[bytes]) -> int:
    def forward_signal(signum, _frame) -> None:
        if process.poll() is None:
            process.send_signal(signum)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, forward_signal)
        except ValueError:
            pass

    return process.wait()


def record_result(
    *,
    status: str,
    message: str,
    request_data: dict[str, Any],
    source_info: dict[str, str],
    current_version: str,
    started_at: str,
    backup_zip_path: str = "",
    rollback_applied: bool = False,
    error: str = "",
) -> None:
    payload: dict[str, Any] = {
        "status": status,
        "message": message,
        "branch": str(request_data.get("branch", "")),
        "tag": str(request_data.get("tag", "")),
        "source_version": source_info["short_tag"],
        "source_commit": source_info["commit"],
        "current_version": current_version,
        "requested_at": str(request_data.get("requested_at", "")),
        "started_at": started_at,
        "finished_at": now_iso(),
        "log_file_path": str(LOG_FILE),
        "update_file_path": str(TRIGGER_FILE),
        "rollback_applied": rollback_applied,
    }
    if backup_zip_path:
        payload["backup_zip_path"] = backup_zip_path
    if error:
        payload["error"] = error
    write_status(payload)


def execute_pending_update(
    request_data: dict[str, Any],
    *,
    logger: AttemptLogger,
) -> subprocess.Popen[bytes]:
    source_info = get_repo_version_info(REPO_DIR)
    started_at = now_iso()
    backup_zip_path = ""
    stash_ref: str | None = None
    repository_changed = False
    branch = str(request_data.get("branch", "")).strip()
    tag = str(request_data.get("tag", "")).strip()
    backup_exclusions: list[Path] = []

    try:
        if not branch:
            raise ValueError("Update file is missing the branch field.")
        if not tag:
            raise ValueError("Update file is missing the tag field.")

        stash_ref = create_rollback_stash(REPO_DIR, logger)

        if bool(request_data.get("backup_usr", True)):
            backup_destination = create_usr_backup(
                repo_dir=REPO_DIR,
                backup_path=str(request_data.get("backup_path", "/a0/tmp/self-update-backups")),
                backup_name=str(request_data.get("backup_name", "agent-zero-usr-backup.zip")),
                conflict_policy=str(request_data.get("backup_conflict_policy", "rename")),
                logger=logger,
            )
            backup_zip_path = str(backup_destination)
            backup_exclusions.append(backup_destination)

        fetch_release_refs(REPO_DIR, branch, tag, logger)

        repository_changed = True
        logger.log(
            "Applying the requested release with native Git checkout. "
            "Ignored files remain untouched; tracked files and non-ignored leftovers are replaced."
        )
        checkout_target_release(
            REPO_DIR,
            branch,
            tag,
            logger,
            exclude_paths=backup_exclusions,
        )

        current_info = get_repo_version_info(REPO_DIR)
        if current_info["short_tag"] != tag:
            raise RuntimeError(
                "Git checkout completed but the repository version does not match the requested tag. "
                f"Expected {tag}, got {current_info['short_tag']}."
            )

        updated_process = launch_ui_process(REPO_DIR, logger)
        healthy, details = wait_for_health(
            updated_process,
            health_url=DEFAULT_HEALTH_URL,
            timeout_seconds=DEFAULT_HEALTH_TIMEOUT_SECONDS,
            poll_interval_seconds=DEFAULT_HEALTH_POLL_INTERVAL_SECONDS,
            expected_version=tag,
            logger=logger,
        )
        if healthy:
            record_result(
                status="success",
                message=f"Updated Agent Zero to branch {branch}, tag {tag}.",
                request_data=request_data,
                source_info=source_info,
                current_version=current_info["short_tag"],
                started_at=started_at,
                backup_zip_path=backup_zip_path,
                rollback_applied=False,
            )
            if stash_ref:
                logger.log(
                    f"Update succeeded, dropping temporary rollback stash {stash_ref}. "
                    "Tracked and non-ignored local changes were not reapplied."
                )
                try:
                    drop_stash(REPO_DIR, stash_ref, logger)
                except Exception as exc:
                    logger.log(
                        f"Temporary rollback stash {stash_ref} could not be dropped automatically: {exc}"
                    )
            return updated_process

        logger.log(f"Updated UI failed health check, rolling back: {details}")
        terminate_process(updated_process)
        restore_git_state(
            REPO_DIR,
            head=source_info["commit"],
            branch=source_info.get("branch", ""),
            logger=logger,
            exclude_paths=backup_exclusions,
        )
        apply_stash(REPO_DIR, stash_ref or "", logger)
        stash_ref = None

        rollback_process = launch_ui_process(REPO_DIR, logger)
        rollback_healthy, rollback_details = wait_for_health(
            rollback_process,
            health_url=DEFAULT_HEALTH_URL,
            timeout_seconds=DEFAULT_HEALTH_TIMEOUT_SECONDS,
            poll_interval_seconds=DEFAULT_HEALTH_POLL_INTERVAL_SECONDS,
            expected_version=source_info["short_tag"],
            logger=logger,
        )

        if rollback_healthy:
            record_result(
                status="rolled_back",
                message=(
                    "Updated version failed its health check and the previous version was restored. "
                    f"Reason: {details}"
                ),
                request_data=request_data,
                source_info=source_info,
                current_version=source_info["short_tag"],
                started_at=started_at,
                backup_zip_path=backup_zip_path,
                rollback_applied=True,
                error=str(details),
            )
            return rollback_process

        terminate_process(rollback_process)
        record_result(
            status="rollback_failed",
            message=(
                "Updated version failed its health check and rollback also failed to become healthy."
            ),
            request_data=request_data,
            source_info=source_info,
            current_version=source_info["short_tag"],
            started_at=started_at,
            backup_zip_path=backup_zip_path,
            rollback_applied=True,
            error=f"Update error: {details}. Rollback error: {rollback_details}",
        )
        raise RuntimeError(str(rollback_details))
    except Exception as exc:
        restore_error = ""
        if repository_changed or stash_ref:
            logger.log(f"Restoring pre-update repository state after error: {exc}")
            try:
                restore_git_state(
                    REPO_DIR,
                    head=source_info["commit"],
                    branch=source_info.get("branch", ""),
                    logger=logger,
                    exclude_paths=backup_exclusions,
                )
                if stash_ref:
                    apply_stash(REPO_DIR, stash_ref, logger)
                    stash_ref = None
            except Exception as restore_exc:
                restore_error = str(restore_exc)
                logger.log(f"Automatic restore failed: {restore_exc}")

        failure_message = str(exc)
        if restore_error:
            failure_message = f"{failure_message} | Restore error: {restore_error}"

        failure_status = "failed"
        if repository_changed:
            failure_status = "rollback_failed" if restore_error else "rolled_back"

        record_result(
            status=failure_status,
            message=failure_message,
            request_data=request_data,
            source_info=source_info,
            current_version=source_info["short_tag"],
            started_at=started_at,
            backup_zip_path=backup_zip_path,
            rollback_applied=repository_changed,
            error=failure_message,
        )
        logger.log(f"Update flow failed: {failure_message}")
        return launch_ui_process(REPO_DIR, logger)


def load_request_file() -> tuple[dict[str, Any] | None, str]:
    if not TRIGGER_FILE.exists():
        return None, ""
    raw_text = TRIGGER_FILE.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(raw_text)
        return (loaded if isinstance(loaded, dict) else None), raw_text
    finally:
        TRIGGER_FILE.unlink(missing_ok=True)


def docker_run_ui() -> int:
    request_data, raw_text = load_request_file()
    logger = AttemptLogger(LOG_FILE)
    quiet_logger = NullLogger()

    if request_data:
        logger.reset()
        logger.log(f"Consumed update file at {TRIGGER_FILE}")
        logger.log_block("Trigger file content", raw_text)

        try:
            current = get_repo_version_info(REPO_DIR)
            requested_branch = str(request_data.get("branch", "")).strip()
            requested_tag = str(request_data.get("tag", "")).strip()
            current_branch = current.get("branch", "").strip()
            if (
                requested_tag
                and current["short_tag"] == requested_tag
                and (not requested_branch or current_branch == requested_branch)
            ):
                logger.log(
                    "Requested tag already matches the installed version, skipping file replacement."
                )
                record_result(
                    status="skipped",
                    message="Requested tag already matches the installed version.",
                    request_data=request_data,
                    source_info=current,
                    current_version=current["short_tag"],
                    started_at=now_iso(),
                    rollback_applied=False,
                )
                process = launch_ui_process(REPO_DIR, logger)
            else:
                process = execute_pending_update(request_data, logger=logger)
        except Exception as exc:
            logger.log(f"Self-update bootstrap failed unexpectedly: {exc}")
            process = launch_ui_process(REPO_DIR, logger)
    elif raw_text:
        logger.reset()
        logger.log(f"Consumed invalid update file at {TRIGGER_FILE}")
        logger.log_block("Trigger file content", raw_text)
        source_info = get_repo_version_info(REPO_DIR)
        record_result(
            status="failed",
            message="Update file was not valid YAML.",
            request_data={},
            source_info=source_info,
            current_version=source_info["short_tag"],
            started_at=now_iso(),
            rollback_applied=False,
            error="Update file was not valid YAML.",
        )
        process = launch_ui_process(REPO_DIR, logger)
    else:
        process = launch_ui_process(REPO_DIR, quiet_logger)

    return wait_for_process(process)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if args and args[0] not in {"docker-run-ui"}:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        return 1
    return docker_run_ui()


if __name__ == "__main__":
    raise SystemExit(main())
