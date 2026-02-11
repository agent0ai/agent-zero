import base64
import os
import subprocess
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from git import Repo

from python.helpers import files


def strip_auth_from_url(url: str) -> str:
    """Remove any authentication info from URL."""
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.hostname:
        return url
    clean_netloc = parsed.hostname
    if parsed.port:
        clean_netloc += f":{parsed.port}"
    return urlunparse((parsed.scheme, clean_netloc, parsed.path, "", "", ""))


def get_git_info():
    # Get the current working directory (assuming the repo is in the same folder as the script)
    repo_path = files.get_base_dir()

    # Open the Git repository
    repo = Repo(repo_path)

    # Ensure the repository is not bare
    if repo.bare:
        raise ValueError(f"Repository at {repo_path} is bare and cannot be used.")

    # Get the current branch name
    branch = repo.active_branch.name if repo.head.is_detached is False else ""

    # Get the latest commit hash
    commit_hash = repo.head.commit.hexsha

    # Get the commit date (ISO 8601 format)
    commit_time = datetime.fromtimestamp(repo.head.commit.committed_date).strftime(
        "%y-%m-%d %H:%M"
    )

    # Get the latest tag description (if available)
    short_tag = ""
    try:
        tag = repo.git.describe(tags=True)
        tag_split = tag.split("-")
        if len(tag_split) >= 3:
            short_tag = "-".join(tag_split[:-1])
        else:
            short_tag = tag
    except:
        tag = ""

    version = branch[0].upper() + " " + (short_tag or commit_hash[:7])

    # Create the dictionary with collected information
    git_info = {
        "branch": branch,
        "commit_hash": commit_hash,
        "commit_time": commit_time,
        "tag": tag,
        "short_tag": short_tag,
        "version": version,
    }

    return git_info


def get_version():
    try:
        git_info = get_git_info()
        return str(git_info.get("short_tag", "")).strip() or "unknown"
    except Exception:
        return "unknown"


def clone_repo(url: str, dest: str, token: str | None = None):
    """Clone a git repository. Uses http.extraHeader for token auth (never stored in URL/config)."""
    cmd = ["git"]

    if token:
        # GitHub Git HTTP requires Basic Auth, not Bearer
        auth_string = f"x-access-token:{token}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()
        cmd.extend(["-c", f"http.extraHeader=Authorization: Basic {auth_base64}"])

    cmd.extend(["clone", "--progress", "--", url, dest])

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise Exception(f"Git clone failed: {error_msg}")

    return Repo(dest)


# Files to ignore when checking dirty status (A0 project metadata)
A0_IGNORE_PATTERNS = {".a0proj", ".a0proj/"}


def get_repo_status(repo_path: str) -> dict:
    """Get Git repository status, ignoring A0 project metadata files."""
    try:
        repo = Repo(repo_path)
        if repo.bare:
            return {"is_git_repo": False, "error": "Repository is bare"}

        # Remote URL (always strip auth info for security)
        remote_url = ""
        try:
            if repo.remotes:
                remote_url = strip_auth_from_url(repo.remotes.origin.url)
        except Exception:
            pass

        # Current branch
        try:
            current_branch = (
                repo.active_branch.name
                if not repo.head.is_detached
                else f"HEAD@{repo.head.commit.hexsha[:7]}"
            )
        except Exception:
            current_branch = "unknown"

        # Check dirty status, excluding A0 metadata
        def is_a0_file(path: str) -> bool:
            return path.startswith(".a0proj") or path == ".a0proj"

        # Filter out A0 files from diff and untracked
        changed_files = [d.a_path for d in repo.index.diff(None)] + [
            d.a_path for d in repo.index.diff("HEAD")
        ]
        untracked = repo.untracked_files

        real_changes = [f for f in changed_files if not is_a0_file(f)]
        real_untracked = [f for f in untracked if not is_a0_file(f)]

        is_dirty = len(real_changes) > 0 or len(real_untracked) > 0
        untracked_count = len(real_untracked)

        last_commit = None
        try:
            commit = repo.head.commit
            last_commit = {
                "hash": commit.hexsha[:7],
                "message": commit.message.split("\n")[0][:80],
                "author": str(commit.author),
                "date": datetime.fromtimestamp(commit.committed_date).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        except Exception:
            pass

        return {
            "is_git_repo": True,
            "remote_url": remote_url,
            "current_branch": current_branch,
            "is_dirty": is_dirty,
            "untracked_count": untracked_count,
            "last_commit": last_commit,
        }
    except Exception as e:
        return {"is_git_repo": False, "error": str(e)}
