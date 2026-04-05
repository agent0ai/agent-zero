#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
DEFAULT_BACKUP_DIR = "/root/update-backups"
DEFAULT_BACKUP_CONFLICT_POLICY = "rename"
BACKUP_CONFLICT_POLICIES = {"rename", "overwrite", "fail"}
MIN_SELECTOR_VERSION = (1, 0)
LATEST_SELECTOR_TAG = "latest"


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


def split_describe_version(describe: str) -> tuple[str, int]:
    normalized = describe.strip()
    match = re.fullmatch(r"(.+)-(\d+)-g[0-9a-f]+", normalized)
    if not match:
        return normalized, 0
    return match.group(1), int(match.group(2))


def parse_selector_version(tag: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"v(\d+)\.(\d+)", tag.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def is_valid_selector_tag(tag: str) -> bool:
    return parse_selector_version(tag) is not None


def is_supported_selector_tag(tag: str) -> bool:
    parsed = parse_selector_version(tag)
    return parsed is not None and parsed >= MIN_SELECTOR_VERSION


def sort_selector_supported_tags(tags: list[str]) -> list[str]:
    return sorted(
        tags,
        key=lambda tag: parse_selector_version(tag) or (-1, -1),
        reverse=True,
    )


def parse_major_version(tag: str) -> int | None:
    match = re.fullmatch(r"v(\d+)(?:[.-].*)?", tag.strip())
    if not match:
        return None
    return int(match.group(1))


def is_latest_selector_tag(tag: str) -> bool:
    return tag.strip().lower() == LATEST_SELECTOR_TAG


def get_tag_commit_ref(tag: str) -> str:
    return f"refs/tags/{tag}^{{commit}}"


def build_default_backup_name() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"usr-{timestamp}.zip"


def normalize_requested_tag(tag: str) -> str:
    normalized = (tag or "").strip()
    if not normalized:
        return LATEST_SELECTOR_TAG
    if is_latest_selector_tag(normalized):
        return LATEST_SELECTOR_TAG
    if not is_valid_selector_tag(normalized):
        raise ValueError("Release tag must use the format vX.Y.")
    if not is_supported_selector_tag(normalized):
        raise ValueError("Release tag must be v1.0 or newer.")
    return normalized


def normalize_backup_conflict_policy(conflict_policy: str) -> str:
    normalized = (conflict_policy or DEFAULT_BACKUP_CONFLICT_POLICY).strip().lower()
    if normalized not in BACKUP_CONFLICT_POLICIES:
        raise ValueError("Backup conflict policy must be one of: rename, overwrite, fail.")
    return normalized


def get_latest_same_major_tag(
    repo_dir: Path,
    *,
    branch_ref: str,
    current_version: str,
) -> str:
    current_major = parse_major_version(current_version)
    if current_major is None:
        raise RuntimeError(
            f"Could not determine the installed major version from {current_version}. "
            "Use an explicit tag instead of latest."
        )

    output = git_output(repo_dir, "tag", "--merged", branch_ref)
    same_major_tags = [
        tag
        for tag in (line.strip() for line in output.splitlines())
        if is_supported_selector_tag(tag) and parse_major_version(tag) == current_major
    ]
    if not same_major_tags:
        raise RuntimeError(
            f"No v{current_major}.x release tags are reachable from branch "
            f"{branch_ref.rsplit('/', 1)[-1]}."
        )
    return sort_selector_supported_tags(same_major_tags)[0]


def ensure_latest_target_matches_current_major(
    *,
    branch: str,
    current_version: str,
    target_version: str,
) -> None:
    current_major = parse_major_version(current_version)
    if current_major is None:
        raise RuntimeError(
            f"Could not determine the installed major version from {current_version}. "
            "Use an explicit tag instead of latest."
        )

    target_major = parse_major_version(target_version)
    if target_major is None or not is_supported_selector_tag(target_version):
        raise RuntimeError(
            f"Could not resolve latest on branch {branch} to a supported vX.Y release. "
            "Use an explicit tag instead."
        )

    if target_major != current_major:
        raise RuntimeError(
            f"Latest on branch {branch} resolves to {target_version}, but the installed "
            f"version is {current_version}. Use an explicit tag to change major versions."
        )


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
    tag_commit_ref = get_tag_commit_ref(tag)
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
            tag_commit_ref,
            remote_branch_ref,
        ],
        cwd=None,
        logger=logger,
        error_message=f"Requested tag {tag} is not reachable from official branch {branch}.",
    )


def fetch_branch_refs(repo_dir: Path, branch: str, logger: AttemptLogger) -> str:
    remote_branch_ref = f"refs/remotes/a0-self-update/{branch}"
    logger.log(f"Fetching branch {branch} and tags from {OFFICIAL_REPO_URL}")
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "fetch",
            "--force",
            "--tags",
            OFFICIAL_REPO_URL,
            f"+refs/heads/{branch}:{remote_branch_ref}",
        ],
        cwd=None,
        logger=logger,
        error_message=f"Failed to fetch branch {branch} from the official repository.",
    )
    return remote_branch_ref


def resolve_requested_target(
    repo_dir: Path,
    branch: str,
    tag: str,
    current_version: str,
    logger: AttemptLogger,
) -> dict[str, str]:
    normalized_tag = tag.strip()

    if not is_latest_selector_tag(normalized_tag):
        fetch_release_refs(repo_dir, branch, normalized_tag, logger)
        tag_commit_ref = get_tag_commit_ref(normalized_tag)
        return {
            "requested_tag": normalized_tag,
            "effective_tag": normalized_tag,
            "target_ref": f"refs/tags/{normalized_tag}",
            "expected_short_tag": normalized_tag,
            "expected_commit": git_output(repo_dir, "rev-parse", tag_commit_ref),
            "target_description": f"tag {normalized_tag}",
        }

    remote_branch_ref = fetch_branch_refs(repo_dir, branch, logger)
    if branch == "main":
        effective_tag = get_latest_same_major_tag(
            repo_dir,
            branch_ref=remote_branch_ref,
            current_version=current_version,
        )
        tag_commit_ref = get_tag_commit_ref(effective_tag)
        logger.log(f"Resolved latest on main to tag {effective_tag}")
        return {
            "requested_tag": LATEST_SELECTOR_TAG,
            "effective_tag": effective_tag,
            "target_ref": f"refs/tags/{effective_tag}",
            "expected_short_tag": effective_tag,
            "expected_commit": git_output(repo_dir, "rev-parse", tag_commit_ref),
            "target_description": f"latest tag {effective_tag}",
        }

    head_describe = git_output(repo_dir, "describe", "--tags", "--always", remote_branch_ref)
    head_short_tag = normalize_describe_to_version(head_describe)
    head_commit = git_output(repo_dir, "rev-parse", remote_branch_ref)
    ensure_latest_target_matches_current_major(
        branch=branch,
        current_version=current_version,
        target_version=head_short_tag,
    )
    logger.log(
        f"Resolved latest on branch {branch} to commit {head_commit[:7]} ({head_describe})"
    )
    return {
        "requested_tag": LATEST_SELECTOR_TAG,
        "effective_tag": head_short_tag,
        "target_ref": remote_branch_ref,
        "expected_short_tag": head_short_tag,
        "expected_commit": head_commit,
        "target_description": f"latest branch state {head_describe}",
    }


def checkout_target_release(
    repo_dir: Path,
    branch: str,
    target_ref: str,
    target_description: str,
    logger: AttemptLogger,
    *,
    exclude_paths: list[Path] | None = None,
) -> None:
    logger.log(f"Checking out branch {branch} at {target_description}")
    run_command(
        [
            "git",
            "-C",
            str(repo_dir),
            "checkout",
            "-B",
            branch,
            target_ref,
        ],
        cwd=None,
        logger=logger,
        error_message=f"Failed to check out requested {target_description} on branch {branch}.",
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
    expected_commit: str | None = None,
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
                current_commit = (git_info.get("commit_hash") or "").strip()
                if expected_commit and current_commit and current_commit != expected_commit:
                    last_error = (
                        f"Health check responded, but commit {current_commit} does not match "
                        f"expected {expected_commit}."
                    )
                elif expected_version and current_version and current_version != expected_version:
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
    resolved_target: dict[str, str] | None = None

    try:
        if not branch:
            raise ValueError("Update file is missing the branch field.")
        if not tag:
            raise ValueError("Update file is missing the tag field.")

        stash_ref = create_rollback_stash(REPO_DIR, logger)

        if bool(request_data.get("backup_usr", True)):
            backup_destination = create_usr_backup(
                repo_dir=REPO_DIR,
                backup_path=str(request_data.get("backup_path", "/root/update-backups")),
                backup_name=str(request_data.get("backup_name", "agent-zero-usr-backup.zip")),
                conflict_policy=str(request_data.get("backup_conflict_policy", "rename")),
                logger=logger,
            )
            backup_zip_path = str(backup_destination)
            backup_exclusions.append(backup_destination)

        resolved_target = resolve_requested_target(
            REPO_DIR,
            branch,
            tag,
            source_info["short_tag"],
            logger,
        )

        repository_changed = True
        logger.log(
            "Applying the requested release with native Git checkout. "
            "Ignored files remain untouched; tracked files and non-ignored leftovers are replaced."
        )
        checkout_target_release(
            REPO_DIR,
            branch,
            resolved_target["target_ref"],
            resolved_target["target_description"],
            logger,
            exclude_paths=backup_exclusions,
        )

        current_info = get_repo_version_info(REPO_DIR)
        if resolved_target.get("expected_commit") and current_info["commit"] != resolved_target["expected_commit"]:
            raise RuntimeError(
                "Git checkout completed but the repository commit does not match the requested target. "
                f"Expected {resolved_target['expected_commit']}, got {current_info['commit']}."
            )
        if resolved_target.get("expected_short_tag") and current_info["short_tag"] != resolved_target["expected_short_tag"]:
            raise RuntimeError(
                "Git checkout completed but the repository version does not match the requested tag. "
                f"Expected {resolved_target['expected_short_tag']}, got {current_info['short_tag']}."
            )

        updated_process = launch_ui_process(REPO_DIR, logger)
        healthy, details = wait_for_health(
            updated_process,
            health_url=DEFAULT_HEALTH_URL,
            timeout_seconds=DEFAULT_HEALTH_TIMEOUT_SECONDS,
            poll_interval_seconds=DEFAULT_HEALTH_POLL_INTERVAL_SECONDS,
            expected_version=resolved_target.get("expected_short_tag"),
            expected_commit=resolved_target.get("expected_commit"),
            logger=logger,
        )
        if healthy:
            record_result(
                status="success",
                message=f"Updated Agent Zero to branch {branch}, {resolved_target['target_description']}.",
                request_data=request_data,
                source_info=source_info,
                current_version=current_info["short_tag"],
                started_at=started_at,
                backup_zip_path=backup_zip_path,
                rollback_applied=False,
            )
            # Write breadcrumb to /a0/usr/ so initialize.sh can restore this
            # update after container recreation. /a0/usr/ is the directory
            # operators mount as a persistent volume.
            # See: https://github.com/MrTrenchTrucker/agent-zero-self-update-rollback
            try:
                breadcrumb_path = Path("/a0/usr/.a0_self_update_state")
                if breadcrumb_path.parent.exists():
                    import json as _json
                    breadcrumb_path.write_text(
                        _json.dumps({
                            "updated_at": now_iso(),
                            "target_tag": resolved_target.get("expected_short_tag", ""),
                            "target_hash": resolved_target.get("expected_commit", ""),
                            "branch": branch,
                        }, indent=2),
                        encoding="utf-8",
                    )
                    logger.log(f"Self-update breadcrumb written to {breadcrumb_path}")
            except Exception as exc:
                logger.log(f"Warning: Could not write self-update breadcrumb: {exc}")
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


def queue_update_request(
    *,
    branch: str = "main",
    tag: str = LATEST_SELECTOR_TAG,
    backup_usr: bool = True,
    backup_path: str = DEFAULT_BACKUP_DIR,
    backup_name: str = "",
    backup_conflict_policy: str = DEFAULT_BACKUP_CONFLICT_POLICY,
) -> dict[str, Any]:
    source_info = get_repo_version_info(REPO_DIR)
    normalized_branch = (branch or "").strip().lower() or "main"
    normalized_tag = normalize_requested_tag(tag)
    normalized_policy = normalize_backup_conflict_policy(backup_conflict_policy)
    normalized_backup_path = (backup_path or "").strip() or DEFAULT_BACKUP_DIR
    normalized_backup_name = sanitize_filename(
        backup_name,
        build_default_backup_name(),
    )

    payload = {
        "branch": normalized_branch,
        "tag": normalized_tag,
        "source_version": source_info["short_tag"],
        "source_describe": source_info["describe"],
        "source_commit": source_info["commit"],
        "requested_at": now_iso(),
        "backup_usr": bool(backup_usr),
        "backup_path": normalized_backup_path,
        "backup_name": normalized_backup_name,
        "backup_conflict_policy": normalized_policy,
    }
    write_yaml(TRIGGER_FILE, payload)
    return payload


def installed_target_matches_request(
    current_info: dict[str, str],
    *,
    requested_branch: str,
    requested_tag: str,
) -> bool:
    normalized_tag = requested_tag.strip()
    if not normalized_tag or is_latest_selector_tag(normalized_tag):
        return False

    current_branch = current_info.get("branch", "").strip()
    if requested_branch.strip() and current_branch != requested_branch.strip():
        return False

    return current_info.get("describe", "").strip() == normalized_tag


def trigger_update_command(args: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="trigger_self_update.sh",
        description="Queue an Agent Zero self-update for the next startup attempt.",
    )
    parser.add_argument(
        "branch",
        nargs="?",
        default="main",
        help="Target official branch. Default: main",
    )
    parser.add_argument(
        "tag",
        nargs="?",
        default=LATEST_SELECTOR_TAG,
        help='Target release tag such as v1.10 or "latest". Default: latest',
    )
    parser.add_argument(
        "--backup-dir",
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory for the usr backup zip. Default: {DEFAULT_BACKUP_DIR}",
    )
    parser.add_argument(
        "--backup-name",
        default="",
        help="Backup zip filename. Default: autogenerated usr-YYYYMMDD-HHMMSS.zip",
    )
    parser.add_argument(
        "--backup-conflict-policy",
        default=DEFAULT_BACKUP_CONFLICT_POLICY,
        choices=sorted(BACKUP_CONFLICT_POLICIES),
        help="How to handle an existing backup zip. Default: rename",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a usr backup before the update.",
    )
    parsed = parser.parse_args(args)

    try:
        payload = queue_update_request(
            branch=parsed.branch,
            tag=parsed.tag,
            backup_usr=not parsed.no_backup,
            backup_path=parsed.backup_dir,
            backup_name=parsed.backup_name,
            backup_conflict_policy=parsed.backup_conflict_policy,
        )
    except Exception as exc:
        print(f"Failed to queue self-update: {exc}", file=sys.stderr)
        return 1

    print("Queued Agent Zero self-update for the next startup attempt.")
    print(f"Branch: {payload['branch']}")
    print(f"Version: {payload['tag']}")
    if payload["backup_usr"]:
        print(f"Backup dir: {payload['backup_path']}")
        print(f"Backup name: {payload['backup_name']}")
        print(f"Backup conflict policy: {payload['backup_conflict_policy']}")
    else:
        print("Backup: disabled")
    print(f"Trigger file: {TRIGGER_FILE}")
    print(f"Log file: {LOG_FILE}")
    print("Restart the container or Agent Zero process to apply it.")
    return 0


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
            if installed_target_matches_request(
                current,
                requested_branch=requested_branch,
                requested_tag=requested_tag,
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
    if not args or args[0] == "docker-run-ui":
        return docker_run_ui()
    if args[0] == "trigger-update":
        return trigger_update_command(args[1:])
    if args[0] in {"-h", "--help"}:
        print("Usage: self_update_manager.py [docker-run-ui | trigger-update ...]")
        return 0
    print(f"Unknown command: {args[0]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
