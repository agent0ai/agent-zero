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
    {"value": "ready", "label": "ready"},
    {"value": "testing", "label": "testing"},
    {"value": "development", "label": "development"},
]
SUPPORTED_BRANCHES = {option["value"] for option in BRANCH_OPTIONS}
BACKUP_CONFLICT_POLICIES = {"rename", "overwrite", "fail"}
MIN_SELECTOR_VERSION = (1, 0)
REMOTE_BRANCH_TAG_CACHE_TTL_SECONDS = 60.0
REMOTE_BRANCH_LIST_CACHE_TTL_SECONDS = 60.0

UPDATE_FILE_PATH = Path("/exe/a0-self-update.yaml")
STATUS_FILE_PATH = Path("/exe/a0-self-update-status.yaml")
LOG_FILE_PATH = Path("/exe/a0-self-update.log")
DURABLE_EXE_DIR = UPDATE_FILE_PATH.parent

_remote_branch_tag_cache: dict[str, tuple[float, set[str]]] = {}
_remote_branch_head_cache: dict[str, tuple[float, dict[str, str]]] = {}
_remote_branch_list_cache: tuple[float, list[str]] | None = None


class PendingUpdateConfig(TypedDict):
    branch: str
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


class SelectorTagOption(TypedDict):
    value: str
    label: str


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def get_update_file_path() -> Path:
    return UPDATE_FILE_PATH


def get_status_file_path() -> Path:
    return STATUS_FILE_PATH


def get_log_file_path() -> Path:
    return LOG_FILE_PATH


def get_durable_exe_dir() -> Path:
    return DURABLE_EXE_DIR


def get_durable_self_update_manager_path() -> Path:
    return get_durable_exe_dir() / "self_update_manager.py"


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
    return Path("/root/update-backups")


def get_repo_dir(repo_dir: str | Path | None = None) -> Path:
    if repo_dir is not None:
        return Path(repo_dir).resolve()
    return Path(__file__).resolve().parents[1]


def get_repo_self_update_manager_path(
    repo_dir: str | Path | None = None,
) -> Path:
    return get_repo_dir(repo_dir) / "docker" / "run" / "fs" / "exe" / "self_update_manager.py"


def _get_official_remote_url() -> str:
    return f"https://github.com/{OFFICIAL_REPO_AUTHOR}/{OFFICIAL_REPO_NAME}.git"


def _run_git_raw(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return completed.stdout.strip()


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


def _split_describe_version(describe: str) -> tuple[str, int]:
    normalized = describe.strip()
    match = re.fullmatch(r"(.+)-(\d+)-g[0-9a-f]+", normalized)
    if not match:
        return normalized, 0
    return match.group(1), int(match.group(2))


def _is_latest_selector_tag(tag: str) -> bool:
    return tag.strip().lower() == "latest"


def _get_tag_release_time_in_repo(
    repo_dir: str | Path,
    tag: str,
) -> str:
    normalized_tag = tag.strip()
    if not normalized_tag:
        return ""
    try:
        timestamp = _run_git(repo_dir, "log", "-1", "--format=%ct", normalized_tag)
        if not timestamp:
            return ""
        return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def get_repo_version_info(repo_dir: str | Path | None = None) -> dict[str, str]:
    repository = get_repo_dir(repo_dir)
    describe = _run_git(repository, "describe", "--tags", "--always")
    commit = _run_git(repository, "rev-parse", "HEAD")
    short_tag = _normalize_describe_to_version(describe)
    try:
        branch = _run_git(repository, "branch", "--show-current")
    except Exception:
        branch = ""
    return {
        "branch": branch,
        "describe": describe,
        "short_tag": short_tag,
        "display_version": _format_branch_head_version(branch, describe),
        "commit": commit,
        "short_commit": commit[:7],
        "released_at": _get_tag_release_time_in_repo(repository, short_tag),
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


def _is_excluded_self_update_branch(branch: str) -> bool:
    normalized = branch.strip().lower()
    return (
        not normalized
        or normalized == "head"
        or normalized.startswith("pr/")
        or normalized.startswith("pr-")
        or normalized.startswith("pull/")
    )


def _sort_branch_names(branches: list[str]) -> list[str]:
    unique_branches: list[str] = []
    seen: set[str] = set()
    for branch in branches:
        normalized = branch.strip().lower()
        if _is_excluded_self_update_branch(normalized) or normalized in seen:
            continue
        seen.add(normalized)
        unique_branches.append(normalized)
    return sorted(unique_branches, key=lambda branch: (branch != "main", branch))


def _get_remote_branch_names() -> list[str]:
    global _remote_branch_list_cache

    now = time.monotonic()
    if (
        _remote_branch_list_cache
        and now - _remote_branch_list_cache[0] <= REMOTE_BRANCH_LIST_CACHE_TTL_SECONDS
    ):
        return list(_remote_branch_list_cache[1])

    output = _run_git_raw("ls-remote", "--heads", _get_official_remote_url())
    branches: list[str] = []
    prefix = "refs/heads/"
    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        ref_name = parts[1]
        if not ref_name.startswith(prefix):
            continue
        branches.append(ref_name[len(prefix):])

    sorted_branches = _sort_branch_names(branches)
    _remote_branch_list_cache = (now, sorted_branches)
    return list(sorted_branches)


def _get_local_origin_branch_names(
    repo_dir: str | Path | None = None,
) -> list[str]:
    repository = get_repo_dir(repo_dir)
    try:
        output = _run_git(
            repository,
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/remotes/origin",
        )
    except Exception:
        return []

    branches: list[str] = []
    prefix = "origin/"
    for line in output.splitlines():
        ref_name = line.strip()
        if not ref_name.startswith(prefix):
            continue
        branches.append(ref_name[len(prefix):])
    return _sort_branch_names(branches)


def get_available_branch_values(
    repo_dir: str | Path | None = None,
) -> list[str]:
    try:
        remote_branches = _get_remote_branch_names()
        if remote_branches:
            return remote_branches
    except Exception:
        pass

    local_origin_branches = _get_local_origin_branch_names(repo_dir=repo_dir)
    if local_origin_branches:
        return local_origin_branches

    return _sort_branch_names([option["value"] for option in BRANCH_OPTIONS])


def get_available_branches(
    repo_dir: str | Path | None = None,
) -> list[dict[str, str]]:
    return [
        {"value": branch, "label": branch}
        for branch in get_available_branch_values(repo_dir=repo_dir)
    ]


def durable_self_update_supports_latest(
    repo_dir: str | Path | None = None,
) -> bool:
    candidate_paths = [
        get_durable_self_update_manager_path(),
        get_repo_self_update_manager_path(repo_dir=repo_dir),
    ]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        return (
            'LATEST_SELECTOR_TAG = "latest"' in content
            and "def resolve_requested_target(" in content
        )
    return False


def _get_branch_reference_names(branch: str) -> list[str]:
    normalized_branch = branch.strip().lower()
    if _is_excluded_self_update_branch(normalized_branch):
        return []
    return [f"origin/{normalized_branch}", normalized_branch]


def _get_remote_branch_merged_tags(branch: str) -> set[str]:
    normalized_branch = branch.strip().lower()
    if _is_excluded_self_update_branch(normalized_branch):
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


def _get_remote_branch_head_info(branch: str) -> dict[str, str]:
    normalized_branch = branch.strip().lower()
    if _is_excluded_self_update_branch(normalized_branch):
        return {"describe": "", "short_tag": "", "commit": "", "released_at": ""}

    cached = _remote_branch_head_cache.get(normalized_branch)
    now = time.monotonic()
    if cached and now - cached[0] <= REMOTE_BRANCH_TAG_CACHE_TTL_SECONDS:
        return dict(cached[1])

    with tempfile.TemporaryDirectory(prefix="a0-self-update-head-") as temp_dir:
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
        remote_ref = f"refs/remotes/origin/{normalized_branch}"
        describe = _run_git(repository, "describe", "--tags", "--always", remote_ref)
        commit = _run_git(repository, "rev-parse", remote_ref)
        short_tag = _normalize_describe_to_version(describe)
        released_at = _get_tag_release_time_in_repo(repository, short_tag)

    payload = {
        "describe": describe,
        "short_tag": short_tag,
        "commit": commit,
        "released_at": released_at,
    }
    _remote_branch_head_cache[normalized_branch] = (now, payload)
    return dict(payload)


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


def _get_local_branch_head_info(
    branch: str,
    repo_dir: str | Path | None = None,
) -> dict[str, str]:
    repository = get_repo_dir(repo_dir)
    for ref in _get_branch_reference_names(branch):
        try:
            _run_git(repository, "rev-parse", "--verify", ref)
            describe = _run_git(repository, "describe", "--tags", "--always", ref)
            commit = _run_git(repository, "rev-parse", ref)
            return {
                "describe": describe,
                "short_tag": _normalize_describe_to_version(describe),
                "commit": commit,
                "released_at": _get_tag_release_time_in_repo(
                    repository,
                    _normalize_describe_to_version(describe),
                ),
            }
        except Exception:
            continue
    return {"describe": "", "short_tag": "", "commit": "", "released_at": ""}


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


def _get_branch_head_info(
    branch: str,
    repo_dir: str | Path | None = None,
) -> dict[str, str]:
    try:
        remote_info = _get_remote_branch_head_info(branch)
        if remote_info.get("commit"):
            return remote_info
    except Exception:
        pass
    return _get_local_branch_head_info(branch, repo_dir=repo_dir)


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


def _parse_major_version(tag: str) -> int | None:
    match = re.fullmatch(r"v(\d+)(?:[.-].*)?", tag.strip())
    if not match:
        return None
    return int(match.group(1))


def _format_latest_selector_label(branch: str, describe: str) -> str:
    short_tag, commits_since_tag = _split_describe_version(describe)
    if not short_tag:
        return "latest"
    if branch.strip().lower() == "main" or commits_since_tag <= 0:
        return f"latest ({short_tag})"
    return f"latest ({short_tag}+{commits_since_tag})"


def _format_latest_release_label(tag: str) -> str:
    normalized = tag.strip()
    if not normalized:
        return "latest"
    return f"latest ({normalized})"


def _format_branch_head_version(branch: str, describe: str) -> str:
    short_tag, commits_since_tag = _split_describe_version(describe)
    if not short_tag:
        return ""
    if branch.strip().lower() == "main" or commits_since_tag <= 0:
        return short_tag
    return f"{short_tag}+{commits_since_tag}"


def _get_release_tag_info(
    branch: str,
    tag: str,
    *,
    repo_dir: str | Path | None = None,
) -> dict[str, Any]:
    repository = get_repo_dir(repo_dir)
    commit = ""
    try:
        commit = _run_git(repository, "rev-parse", f"refs/tags/{tag}^{{commit}}")
    except Exception:
        commit = ""
    return {
        "branch": branch.strip().lower(),
        "supported": True,
        "describe": tag,
        "short_tag": tag,
        "display_version": tag,
        "commit": commit,
        "short_commit": commit[:7] if commit else "",
        "released_at": _get_tag_release_time_in_repo(repository, tag),
    }


def get_current_major_main_latest_info(
    current_version: str,
    *,
    repo_dir: str | Path | None = None,
) -> dict[str, Any]:
    repository = get_repo_dir(repo_dir)
    available_branches = set(get_available_branch_values(repo_dir=repository))
    if "main" not in available_branches:
        return {
            "branch": "main",
            "supported": False,
            "describe": "",
            "short_tag": "",
            "display_version": "",
            "commit": "",
            "short_commit": "",
            "released_at": "",
        }

    current_major = _parse_major_version(current_version)
    if current_major is None:
        return get_current_branch_latest_info("main", repo_dir=repository)

    tags, error = get_available_tags("main", repo_dir=repository)
    if error:
        return get_current_branch_latest_info("main", repo_dir=repository)

    latest_same_major_tag = next(
        (tag for tag in tags if _parse_major_version(tag) == current_major),
        "",
    )
    if not latest_same_major_tag:
        return {
            "branch": "main",
            "supported": True,
            "describe": "",
            "short_tag": "",
            "display_version": "",
            "commit": "",
            "short_commit": "",
            "released_at": "",
        }

    branch_head_info = _get_branch_head_info("main", repo_dir=repository)
    head_describe = branch_head_info.get("describe", "")
    head_short_tag = branch_head_info.get("short_tag", "")
    _, commits_since_tag = _split_describe_version(head_describe)
    if head_short_tag == latest_same_major_tag and commits_since_tag <= 0:
        commit = branch_head_info.get("commit", "")
        return {
            "branch": "main",
            "supported": True,
            "describe": head_describe,
            "short_tag": head_short_tag,
            "display_version": _format_branch_head_version("main", head_describe),
            "commit": commit,
            "short_commit": commit[:7] if commit else "",
            "released_at": branch_head_info.get("released_at", ""),
        }

    return _get_release_tag_info("main", latest_same_major_tag, repo_dir=repository)


def get_current_branch_latest_info(
    current_branch: str,
    *,
    repo_dir: str | Path | None = None,
) -> dict[str, Any]:
    repository = get_repo_dir(repo_dir)
    normalized_branch = current_branch.strip().lower()
    available_branches = set(get_available_branch_values(repo_dir=repository))
    if normalized_branch not in available_branches:
        return {
            "branch": current_branch.strip(),
            "supported": False,
            "describe": "",
            "short_tag": "",
            "display_version": "",
            "commit": "",
            "short_commit": "",
            "released_at": "",
        }

    branch_head_info = _get_branch_head_info(normalized_branch, repo_dir=repository)
    commit = branch_head_info.get("commit", "")
    return {
        "branch": normalized_branch,
        "supported": True,
        "describe": branch_head_info.get("describe", ""),
        "short_tag": branch_head_info.get("short_tag", ""),
        "display_version": _format_branch_head_version(
            normalized_branch,
            branch_head_info.get("describe", ""),
        ),
        "commit": commit,
        "short_commit": commit[:7] if commit else "",
        "released_at": branch_head_info.get("released_at", ""),
    }


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


def get_selector_tag_options(
    branch: str | None = None,
    *,
    repo_dir: str | Path | None = None,
    current_version: str | None = None,
) -> tuple[list[SelectorTagOption], list[int], str]:
    repository = get_repo_dir(repo_dir)
    tags, error = get_available_tags(branch, repo_dir=repository)
    if error:
        return [], [], error
    supports_latest = durable_self_update_supports_latest(repo_dir=repository)

    current_major = _parse_major_version(
        current_version or get_repo_version_info(repository)["short_tag"]
    )
    if current_major is None:
        return [{"value": tag, "label": tag} for tag in tags], [], ""

    branch_head_info = _get_branch_head_info(branch or "", repo_dir=repository)
    branch_head_tag = branch_head_info.get("short_tag", "")
    branch_head_major = _parse_major_version(branch_head_tag)

    same_major_tags: list[SelectorTagOption] = []
    higher_major_versions: set[int] = set()
    for tag in tags:
        tag_major = _parse_major_version(tag)
        if tag_major is None:
            continue
        if tag_major == current_major:
            same_major_tags.append({"value": tag, "label": tag})
        elif tag_major > current_major:
            higher_major_versions.add(tag_major)

    if branch_head_major is not None and branch_head_major > current_major:
        higher_major_versions.add(branch_head_major)

    normalized_branch = (branch or "").strip().lower()

    if supports_latest and normalized_branch == "main" and same_major_tags:
        same_major_tags.insert(
            0,
            {
                "value": "latest",
                "label": _format_latest_release_label(same_major_tags[0]["value"]),
            },
        )
    elif (
        supports_latest
        and branch_head_major == current_major
        and _is_selector_supported_tag(branch_head_tag)
    ):
        same_major_tags.insert(
            0,
            {
                "value": "latest",
                "label": _format_latest_selector_label(
                    branch or "",
                    branch_head_info.get("describe", ""),
                ),
            },
        )

    return same_major_tags, sorted(higher_major_versions), ""


def get_update_info(repo_dir: str | Path | None = None) -> dict[str, Any]:
    repository = get_repo_dir(repo_dir)
    version_info = get_repo_version_info(repository)
    current_version = version_info["short_tag"]
    current_branch = version_info.get("branch", "").strip().lower()
    available_branches = get_available_branches(repo_dir=repository)
    available_branch_values = [branch["value"] for branch in available_branches]
    if current_branch in available_branch_values:
        default_branch = current_branch
    elif "main" in available_branch_values:
        default_branch = "main"
    elif available_branch_values:
        default_branch = available_branch_values[0]
    else:
        default_branch = "main"
    tag_options, higher_major_versions, tags_error = get_selector_tag_options(
        default_branch,
        repo_dir=repository,
        current_version=current_version,
    )
    if "main" in available_branch_values:
        _, major_upgrade_versions, _ = get_selector_tag_options(
            "main",
            repo_dir=repository,
            current_version=current_version,
        )
    else:
        major_upgrade_versions = []
    return {
        "repo_dir": str(repository),
        "current": version_info,
        "main_branch_latest": get_current_major_main_latest_info(
            current_version,
            repo_dir=repository,
        ),
        "current_branch_latest": get_current_branch_latest_info(
            current_branch,
            repo_dir=repository,
        ),
        "pending": load_pending_update(),
        "last_status": load_last_status(),
        "branches": available_branches,
        "available_tags": [option["value"] for option in tag_options],
        "available_tag_options": tag_options,
        "available_tags_error": tags_error,
        "available_higher_major_versions": higher_major_versions,
        "major_upgrade_versions": major_upgrade_versions,
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
    available_branch_values = set(get_available_branch_values(repo_dir=repository))
    if normalized_branch not in available_branch_values:
        raise ValueError("Branch must be one of the available remote branches.")

    normalized_tag = tag.strip()
    if not normalized_tag:
        raise ValueError("A release tag is required.")
    if _is_latest_selector_tag(normalized_tag):
        if not durable_self_update_supports_latest(repo_dir=repository):
            raise ValueError(
                "This Docker image's durable updater does not support the latest selector. "
                "Choose a concrete version or update the Docker image."
            )
        normalized_tag = "latest"
    elif not is_valid_selector_tag(normalized_tag):
        raise ValueError("Release tag must use the format vX.Y.")
    elif not _is_selector_supported_tag(normalized_tag):
        raise ValueError("Release tag must be v1.0 or newer.")

    selector_tag_options, _, tag_lookup_error = get_selector_tag_options(
        normalized_branch,
        repo_dir=repository,
        current_version=version_info["short_tag"],
    )
    if tag_lookup_error:
        raise RuntimeError(
            f"Failed to verify release tag {normalized_tag} on branch {normalized_branch}: {tag_lookup_error}"
        )
    if normalized_tag not in {option["value"] for option in selector_tag_options}:
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
