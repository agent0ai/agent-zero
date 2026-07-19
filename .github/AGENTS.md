# GitHub Automation DOX

## Purpose

- Own repository automation that runs on GitHub, including workflows and release-planning scripts.
- Keep CI, Docker publishing, stale issue handling, and release-note generation aligned with repository release rules.

## Ownership

- `workflows/` contains GitHub Actions workflow definitions.
- `scripts/` contains Python helpers called by workflows.
- This file owns release automation rules; user-facing release documentation belongs under `docs/`.

## Local Contracts

- Docker publishing lives in `workflows/docker-publish.yml` and delegates planning to `scripts/docker_release_plan.py`.
- Releasable tags are `vX.Y` tags at or above `v1.0`, matching the workflow environment.
- On `main`, the newest eligible tag publishes both the version tag and `latest`, then creates or updates its GitHub release after the image push succeeds; other allowed branches publish only their branch tag.
- Manual dispatch without a tag backfills missing Docker Hub tags. Manual dispatch with a tag rebuilds that target and refreshes `latest` and the GitHub release only when it remains the newest eligible tag on `main`.
- Release-note generation reads `scripts/openrouter_release_notes_system_prompt.md` from the repository root and requires OpenRouter credentials from workflow environment variables.
- Release notes compare against the previous published GitHub release tag and fall back to `No release notes.` when no meaningful summary is generated.
- Keep workflow secrets in GitHub Actions secrets or environment variables. Do not commit credentials, tokens, or generated release bodies containing private data.
- Workflow scripts must fail loudly with actionable messages when required environment variables or git refs are missing.

## Work Guidance

- Prefer deterministic, testable Python for workflow planning logic instead of complex inline shell in YAML.
- Preserve manual dispatch behavior when changing Docker publishing.
- Keep branch, tag, and release behavior synchronized between workflow YAML, release scripts, tests, and user-facing release documentation.

## Verification

- Run `pytest tests/test_docker_release_plan.py` after changing Docker publish planning or release workflow behavior.
- Run targeted tests for any changed script that already has coverage.

## Child DOX Index

No child DOX files.
