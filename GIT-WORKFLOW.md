# Multi-Agent Git Workflow

This repository uses disciplined multi-agent development.

## Source of truth

- The remote repository is the shared source of truth.
- `main` is the integration branch unless this repository's existing governance explicitly names another branch.
- Never use a shared network or cloud-synchronized checkout as a simultaneous workspace.
- Each computer uses its own local clone. Active tasks use separate branches and, when practical, Git worktrees.

## Before any work

1. Identify the repository root and confirm the `origin` remote.
2. Inspect branch, HEAD, upstream, ahead/behind, and working-tree status.
3. Never modify, reset, clean, stash, or switch another agent's dirty checkout.
4. Fetch remote references.
5. If starting from `main`, update it with fast-forward-only synchronization.
6. If `main` is dirty, stop and report it; do not overwrite local work.
7. Create a dedicated task branch from the current `origin/main`.

Windows example:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/<task-name>
```

Linux example:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c agent/<task-name>
```

Use the local repository root on each computer, such as `B:\AI Directory\Projects\<repo>`, `C:\dev\repos\<repo>`, or `~/dev/repos/<repo>`; do not hardcode one computer's path into project code.

## During work

- Keep one task per branch.
- Do not work directly on `main).
- Do not force-push, rewrite shared history, or use destructive cleanup.
- Do not commit secrets, credentials, private keys, secret `.env` files, caches, bytecode, OS metadata, or machine-only files.
- Coordinate before editing files another active agent is changing.
- Commit complete logical units with descriptive messages.

## Completion and integration

Before handoff, run the relevant tests and report:

- branch and commit SHA;
- changed files;
- tests and results;
- known risks or follow-up work.

Agents may commit, push their task branch, and open or update a pull request. Pull requests must target `main). Merging requires human approval and passing required checks. Do not enable unattended merging without explicit repository policy.

After a merge, every computer must fetch and fast-forward its local `main` before starting new work.

## Cross-platform expectations

Use repository-relative paths in documentation and scripts. Keep OS-specific behavior in explicit adapters or scripts. Prefer portable commands where possible, and document Windows PowerShell and Linux shell equivalents when setup differs.

Existing repository-specific `AGENTS.md`, security policy, governance, and contribution instructions remain authoritative when they add stricter requirements.

