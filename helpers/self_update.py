from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict

from helpers import git, yaml


OFFICIAL_REPO_AUTHOR = "agent0ai"
OFFICIAL_REPO_NAME = "agent-zero"
BRANCH_OPTIONS = [
    {"value": "main", "label": "main"},
    {"value": "testing", "label": "testing"},
    {"value": "development", "label": "development"},
]
SUPPORTED_BRANCHES = {option["value"] for option in BRANCH_OPTIONS}
BACKUP_CONFLICT_POLICIES = {"rename", "overwrite", "fail"}
MIN_SELECTOR_VERSION = (1, 0)
REMOTE_BRANCH_TAG_CACHE_TTL_SECONDS = 60.0

UPDATE_FILE_PATH = Path("/exe/a0-self-update.yaml")
STATUS_FILE_PATH = Path("/exe/a0-self-update-status.yaml")
LOG_FILE_PATH = Path("/exe/a0-self-update.log")

_remote_branch_tag_cache: dict[str, tuple[float, set[str]]] = {}


class PendingUpdateConfig(TypedDict):
    branch: Literal["main", "testing", "development"]
    tag: str
    source_version: str
    source_describe: str
    source_commit: str
    requested_at: str
    backup_usr: bool
    backup_path: str
    backup_name: str
    backup_conflict_policy: Literal["rename", "overwrite", "fail"]


class UpdateStatus(TypedDict, total=False):
    status: str
    message: str
    branch: str
    tag: str
    source_version: str
    source_commit: str
    current_version: str
    requested_at: str
    started_at: str
    finished_at: str
    backup_zip_path: str
    log_file_path: str
    update_file_path: str
    rollback_applied: bool
    error: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def get_update_file_path() -> Path:
    return UPDATE_FILE_PATH


def get_status_file_path() -> Path:
    return STATUS_FILE_PATH


def get_log_file_path() -> Path:
    return LOG_FILE_PATH


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    loaded = yaml.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dumps(payload), encoding="utf-8")


def load_pending_update() -> PendingUpdateConfig | None:
    loaded = _load_yaml(get_update_file_path())
    return loaded if loaded is not None else None


def load_last_status() -> UpdateStatus | None:
    loaded = _load_yaml(get_status_file_path())
    return loaded if loaded is not None else None


def get_log_text() -> str:
    path = get_log_file_path()
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_default_backup_dir(repo_dir: str | Path | None = None) -> Path:
    repository = get_repo_dir(repo_dir)
    return repository / "tmp" / "self-update-backups"


def get_repo_dir(repo_dir: str | Path | None = None) -> Path:
    if repo_dir is not None:
        return Path(repo_dir).resolve()
    return Path(__file__).resolve().parents[1]


def _get_official_remote_url() -> str:
    return f"https://github.com/{OFFICIAL_REPO_AUTHOR}/{OFFICIAL_REPO_NAME}.git"


def _run_git(repo_dir: str | Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(get_repo_dir(repo_dir)), *args],
        check=True,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return completed.stdout.strip()


def _normalize_describe_to_version(describe: str) -> str:
    match = re.fullmatch(r"(.+)-\d+-g[0-9a-f]+", describe)
    if match:
        return match.group(1)
    return describe


def get_repo_version_info(repo_dir: str | Path | None = None) -> dict[str, str]:
    repository = get_repo_dir(repo_dir)
    describe = _run_git(repository, "describe", "--tags", "--always")
    commit = _run_git(repository, "rev-parse", "HEAD")
    try:
        branch = _run_git(repository, "branch", "--show-current")
    except Exception:
        branch = ""
    return {
        "branch": branch,
        "describe": describe,
        "short_tag": _normalize_describe_to_version(describe),
        "commit": commit,
        "short_commit": commit[:7],
    }


def _sanitize_filename(name: str, default_name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        raw = default_name
    raw = Path(raw).name
    raw = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-") or default_name
    if not raw.lower().endswith(".zip"):
        raw = f"{raw}.zip"
    return raw


def _slugify_version(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-")
    return cleaned or "unknown"


def build_default_backup_name(
    current_version: str,
    target_tag: str | None = None,
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"usr-{timestamp}.zip"


def _resolve_backup_path(
    backup_path: str,
    repo_dir: str | Path | None = None,
) -> Path:
    raw = (backup_path or "").strip()
    if not raw:
        return get_default_backup_dir(repo_dir)
    path = Path(raw)
    if not path.is_absolute():
        path = get_repo_dir(repo_dir) / path
    return path.resolve()


def _get_branch_reference_names(branch: str) -> list[str]:
    normalized_branch = branch.strip().lower()
    if normalized_branch not in SUPPORTED_BRANCHES:
        return []
    return [f"origin/{normalized_branch}", normalized_branch]


def _get_remote_branch_merged_tags(branch: str) -> set[str]:
    normalized_branch = branch.strip().lower()
    if normalized_branch not in SUPPORTED_BRANCHES:
        return set()

    cached = _remote_branch_tag_cache.get(normalized_branch)
    now = time.monotonic()
    if cached and now - cached[0] <= REMOTE_BRANCH_TAG_CACHE_TTL_SECONDS:
        return set(cached[1])

    with tempfile.TemporaryDirectory(prefix="a0-self-update-tags-") as temp_dir:
        repository = Path(temp_dir)
        _run_git(repository, "init", "--bare")
        _run_git(
            repository,
            "fetch",
            "--quiet",
            "--prune",
            "--filter=blob:none",
            "--tags",
            _get_official_remote_url(),
            f"refs/heads/{normalized_branch}:refs/remotes/origin/{normalized_branch}",
        )
        output = _run_git(repository, "tag", "--merged", f"refs/remotes/origin/{normalized_branch}")
        merged_tags = {line.strip() for line in output.splitlines() if line.strip()}

    _remote_branch_tag_cache[normalized_branch] = (now, merged_tags)
    return set(merged_tags)


def _get_local_branch_merged_tags(
    branch: str,
    repo_dir: str | Path | None = None,
) -> set[str]:
    repository = get_repo_dir(repo_dir)
    for ref in _get_branch_reference_names(branch):
        try:
            _run_git(repository, "rev-parse", "--verify", ref)
            output = _run_git(repository, "tag", "--merged", ref)
            return {line.strip() for line in output.splitlines() if line.strip()}
        except Exception:
            continue
    return set()


def _get_branch_merged_tags(
    branch: str,
    repo_dir: str | Path | None = None,
) -> set[str]:
    try:
        remote_tags = _get_remote_branch_merged_tags(branch)
        if remote_tags:
            return remote_tags
    except Exception:
        pass
    return _get_local_branch_merged_tags(branch, repo_dir=repo_dir)


def _parse_selector_version(tag: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"v(\d+)\.(\d+)", tag.strip())
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def _is_selector_supported_tag(tag: str) -> bool:
    parsed = _parse_selector_version(tag)
    return parsed is not None and parsed >= MIN_SELECTOR_VERSION


def _filter_selector_supported_tags(tags: list[str]) -> list[str]:
    return [tag for tag in tags if _is_selector_supported_tag(tag)]


def _sort_selector_supported_tags(tags: list[str]) -> list[str]:
    return sorted(tags, key=lambda tag: _parse_selector_version(tag) or (-1, -1), reverse=True)


def is_valid_selector_tag(tag: str) -> bool:
    return _parse_selector_version(tag) is not None


def get_available_tags(
    branch: str | None = None,
    *,
    repo_dir: str | Path | None = None,
    query: str = "",
) -> tuple[list[str], str]:
    result = git.get_remote_releases(OFFICIAL_REPO_AUTHOR, OFFICIAL_REPO_NAME)
    if result.error:
        return [], result.error
    tags = [release.tag for release in result.releases]

    if branch:
        merged_tags = _get_branch_merged_tags(branch, repo_dir=repo_dir)
        if merged_tags:
            tags = [tag for tag in tags if tag in merged_tags]

    tags = _sort_selector_supported_tags(_filter_selector_supported_tags(tags))

    normalized_query = query.strip().lower()
    if normalized_query:
        tags = [tag for tag in tags if normalized_query in tag.lower()]

    return tags, ""


def get_update_info(repo_dir: str | Path | None = None) -> dict[str, Any]:
    repository = get_repo_dir(repo_dir)
    version_info = get_repo_version_info(repository)
    current_version = version_info["short_tag"]
    current_branch = version_info.get("branch", "").strip().lower()
    default_branch = current_branch if current_branch in SUPPORTED_BRANCHES else "main"
    tags, tags_error = get_available_tags(default_branch, repo_dir=repository)
    return {
        "repo_dir": str(repository),
        "current": version_info,
        "pending": load_pending_update(),
        "last_status": load_last_status(),
        "branches": BRANCH_OPTIONS,
        "available_tags": tags,
        "available_tags_error": tags_error,
        "paths": {
            "update_file": str(get_update_file_path()),
            "status_file": str(get_status_file_path()),
            "log_file": str(get_log_file_path()),
        },
        "defaults": {
            "branch": default_branch,
            "tag": current_version if _is_selector_supported_tag(current_version) else "",
            "backup_usr": True,
            "backup_path": str(get_default_backup_dir(repository)),
            "backup_name": build_default_backup_name(current_version, current_version),
            "backup_conflict_policy": "rename",
        },
    }


def schedule_update(
    *,
    branch: str,
    tag: str,
    backup_usr: bool,
    backup_path: str,
    backup_name: str,
    backup_conflict_policy: str,
    repo_dir: str | Path | None = None,
) -> PendingUpdateConfig:
    repository = get_repo_dir(repo_dir)
    version_info = get_repo_version_info(repository)

    normalized_branch = branch.strip().lower()
    if normalized_branch not in SUPPORTED_BRANCHES:
        raise ValueError("Branch must be one of: main, testing, development.")

    normalized_tag = tag.strip()
    if not normalized_tag:
        raise ValueError("A release tag is required.")
    if not is_valid_selector_tag(normalized_tag):
        raise ValueError("Release tag must use the format vX.Y.")
    if not _is_selector_supported_tag(normalized_tag):
        raise ValueError("Release tag must be v1.0 or newer.")

    available_tags, tag_lookup_error = get_available_tags(
        normalized_branch,
        repo_dir=repository,
        query=normalized_tag,
    )
    if tag_lookup_error:
        raise RuntimeError(
            f"Failed to verify release tag {normalized_tag} on branch {normalized_branch}: {tag_lookup_error}"
        )
    if normalized_tag not in available_tags:
        raise ValueError(
            f"Version {normalized_tag} does not exist on branch {normalized_branch}."
        )

    normalized_policy = backup_conflict_policy.strip().lower()
    if normalized_policy not in BACKUP_CONFLICT_POLICIES:
        raise ValueError(
            "Backup conflict policy must be one of: rename, overwrite, fail."
        )

    resolved_backup_path = _resolve_backup_path(backup_path, repository)
    resolved_backup_name = _sanitize_filename(
        backup_name,
        build_default_backup_name(version_info["short_tag"], normalized_tag),
    )

    payload: PendingUpdateConfig = {
        "branch": normalized_branch,  # type: ignore[assignment]
        "tag": normalized_tag,
        "source_version": version_info["short_tag"],
        "source_describe": version_info["describe"],
        "source_commit": version_info["commit"],
        "requested_at": _now_iso(),
        "backup_usr": bool(backup_usr),
        "backup_path": str(resolved_backup_path),
        "backup_name": resolved_backup_name,
        "backup_conflict_policy": normalized_policy,  # type: ignore[assignment]
    }

    _write_yaml(get_update_file_path(), payload)
    return payload
