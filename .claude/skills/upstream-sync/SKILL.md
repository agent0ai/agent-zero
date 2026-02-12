---
name: upstream-sync
description: Merge upstream agent-zero changes into the fork. Fetches from agent0ai/agent-zero, merges upstream/main, resolves requirements.txt conflicts automatically, flags pyproject.toml conflicts for review, regenerates lockfile and requirements.txt, and runs CI validation.
disable-model-invocation: true
---

# Upstream Sync — Merge upstream agent-zero into fork

## Current State

Remotes:
```
! `git remote -v` !
```

Working tree:
```
! `git status --short` !
```

## Procedure

Follow these steps **in order**. Stop and report if any step fails unexpectedly.

### 1. Pre-flight checks

- Verify the current branch is `main`. If not, abort with a message telling the user to switch to main first.
- Verify the working tree is clean (no staged or unstaged changes). If dirty, abort and tell the user to commit or stash first.

### 2. Ensure upstream remote exists

Check if a remote named `upstream` exists (from the remotes shown above).

- If **missing**, add it:
  ```bash
  git remote add upstream https://github.com/agent0ai/agent-zero.git
  ```
- If it exists but points to the wrong URL, warn the user and abort.

### 3. Fetch upstream

```bash
git fetch upstream
```

### 4. Merge upstream/main

```bash
git merge upstream/main --no-edit
```

- If the merge completes cleanly, proceed to step 6.
- If there are conflicts, proceed to step 5.

### 5. Resolve conflicts

Handle conflicts according to these rules:

| File | Resolution |
|------|-----------|
| `requirements.txt` | Accept upstream's version (`git checkout upstream/main -- requirements.txt`). This file is auto-generated and will be regenerated in step 6. |
| `pyproject.toml` | **Do NOT auto-resolve.** Print the conflict markers and tell the user: "pyproject.toml has conflicts that require manual review — our fork may have different dependencies or version overrides (see `[tool.uv] override-dependencies`). Please resolve manually, then re-run `/upstream-sync`." Abort here. |
| `uv.lock` | Accept upstream's version (`git checkout upstream/main -- uv.lock`). It will be regenerated in step 6. |
| Any other file | Attempt to accept upstream's version. If unsure, list the conflicted files and ask the user for guidance. |

After resolving, stage all resolved files:
```bash
git add -A
```

### 6. Regenerate dependency files

Run these commands in sequence:

```bash
uv lock
uv export --no-hashes --no-dev --no-emit-project -o requirements.txt
```

If `uv lock` fails, it likely means `pyproject.toml` has incompatible dependencies. Report the error and suggest the user check `[tool.uv] override-dependencies` in `pyproject.toml`.

### 7. Stage regenerated files

```bash
git add uv.lock requirements.txt
```

### 8. Run CI validation

```bash
mise run ci
```

This runs lint + format check + tests. If CI fails:
- For **lint/format** failures: attempt auto-fix with `mise run format` and `mise run lint`, then re-run `mise run ci`.
- For **test** failures: report which tests failed and let the user decide how to proceed. Do NOT auto-commit if tests fail.

### 9. Commit the merge

If the merge was already committed by git (clean merge), amend to include regenerated files:
```bash
git add uv.lock requirements.txt
git commit --amend --no-edit
```

If the merge had conflicts that were resolved (so the merge is not yet committed):
```bash
git commit -m "chore: merge upstream agent-zero into fork

Merged upstream/main, regenerated uv.lock and requirements.txt.
CI validated: lint + format + tests pass."
```

### 10. Summary

Print a summary:
- Number of commits merged
- Any files that required manual conflict resolution
- CI pass/fail status
- Remind the user to `git push` when ready
