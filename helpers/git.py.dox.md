# git.py DOX

## Purpose

- Own the `git.py` helper module.
- This module reads local and remote Git release/commit metadata safely.
- Keep this file-level DOX profile synchronized with `git.py` because this directory is intentionally flat.

## Ownership

- `git.py` owns the runtime implementation.
- `git.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `GitHeadInfo` (no explicit base class)
- `GitReleaseInfo` (no explicit base class)
- `GitRemoteReleaseInfo` (no explicit base class)
- `GitRemoteReleasesResult` (no explicit base class)
- `GitRemoteCommitsInfo` (no explicit base class)
- `GitRepoReleaseInfo` (no explicit base class)
- Top-level functions:
- `strip_auth_from_url(url: str) -> str`: Remove any authentication info from URL.
- `extract_author_repo(url: str) -> tuple[str, str]`
- `_format_git_timestamp(timestamp: int) -> str`
- `_split_describe_version(describe: str) -> tuple[str, int]`
- `_format_release_version(branch: str, short_tag: str, commits_since_tag: int, commit_hash: str) -> str`
- `get_remote_releases(author: str, repo: str) -> GitRemoteReleasesResult`
- `get_remote_commits_since_local(repo_path: str) -> GitRemoteCommitsInfo`
- `get_repo_release_info(repo_path: str) -> GitRepoReleaseInfo`
- `get_git_info()`
- `get_version()`
- `is_official_agent_zero_repo() -> bool`: Return True when origin points to agent0ai/agent-zero.
- `clone_repo(url: str, dest: str, token: str | None=...)`: Clone a git repository. Uses http.extraHeader for token auth (never stored in URL/config).
- `update_repo(repo_path: str) -> Repo`
- `get_repo_status(repo_path: str) -> dict`: Get Git repository status, ignoring A0 project metadata files.
- Notable constants/configuration names: `A0_IGNORE_PATTERNS`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, filesystem deletion, network calls, subprocess/runtime control, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `base64`, `dataclasses`, `datetime`, `git`, `giturlparse`, `helpers`, `helpers.localization`, `os`, `re`, `subprocess`, `urllib.parse`.

## Key Concepts

- Important called helpers/classes observed in the source: `urlparse`, `urlunparse`, `parse`, `strip`, `repo.endswith`, `datetime.fromtimestamp.strftime`, `describe.strip`, `re.fullmatch`, `files.get_base_dir`, `get_repo_release_info`, `os.environ.copy`, `subprocess.run`, `Repo`, `repo.active_branch.tracking_branch`, `strip_auth_from_url`, `ValueError`, `match.group`, `branch.upper`, `author.strip`, `repo.strip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_docker_release_plan.py`
  - `tests/test_git_version_label.py`
  - `tests/test_model_config_api_keys.py`
  - `tests/test_model_config_project_presets.py`
  - `tests/test_model_search.py`
  - `tests/test_oauth_github_copilot.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_onboarding_static.py`

## Child DOX Index

No child DOX files.
