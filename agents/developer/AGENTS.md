# Developer Agent Profile DOX

## Purpose

- Own the bundled software development specialist profile.
- Keep development, debugging, refactoring, and architecture behavior separate from general agent defaults.

## Ownership

- `agent.yaml` owns title, description, and delegation context for software development work.
- `prompts/` owns developer-specific prompt overrides when present.
- `extensions/` owns developer-specific lifecycle hooks when present.

## Local Contracts

- Keep this profile focused on software engineering tasks.
- Do not hardcode repository-local credentials, paths, or project-specific conventions.
- Prompt overrides must preserve the framework tool-call and response contracts.

## Work Guidance

- Align developer behavior with the root engineering and tool contracts.
- Prefer profile prompt edits over core prompt edits when the behavior is specific to development tasks.

## Verification

- Manually inspect `agent.yaml` for valid YAML after edits.
- Run prompt/profile tests when changing profile loading or developer prompt behavior.

## Child DOX Index

No child DOX files.
