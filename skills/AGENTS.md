# Bundled Skills DOX

## Purpose

- Own bundled Agent Zero skills and their agent-facing instructions.
- Keep skill workflows accurate, composable, and safe for runtime loading.

## Ownership

- Each direct skill directory owns its `SKILL.md` and any local supporting files.
- Plugin-distributed skills belong under the relevant plugin directory.
- User-local skills belong under `usr/skills/`.

## Local Contracts

- Every skill directory must include a `SKILL.md`.
- Skill instructions must be operational and scoped to the skill's purpose.
- Do not include secrets, private user data, or environment-specific credentials.
- Supporting files referenced by a skill must exist relative to that skill directory.

## Work Guidance

- Keep skills focused on repeatable workflows that agents should actively follow.
- Prefer updating an existing skill over creating overlapping skill variants.
- When a skill refers to repository paths, commands, or plugin architecture, keep those references current with source and docs.

## Verification

- Run skill runtime/import tests after changing skill loading assumptions or skill format.
- Manually read changed `SKILL.md` files for broken relative references.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [a0-contribute-plugin/AGENTS.md](a0-contribute-plugin/AGENTS.md) | Publishing plugins to the community Plugin Index. |
| [a0-create-agent/AGENTS.md](a0-create-agent/AGENTS.md) | Creating Agent Zero agent profiles. |
| [a0-create-plugin/AGENTS.md](a0-create-plugin/AGENTS.md) | Creating or extending Agent Zero plugins. |
| [a0-debug-plugin/AGENTS.md](a0-debug-plugin/AGENTS.md) | Diagnosing plugin loading, API, frontend, and extension issues. |
| [a0-development/AGENTS.md](a0-development/AGENTS.md) | Broad Agent Zero framework development guidance. |
| [a0-manage-plugin/AGENTS.md](a0-manage-plugin/AGENTS.md) | Plugin install, update, scan, enable, disable, and removal workflows. |
| [a0-plugin-router/AGENTS.md](a0-plugin-router/AGENTS.md) | Routing plugin-related user requests to specialist skills. |
| [a0-review-plugin/AGENTS.md](a0-review-plugin/AGENTS.md) | Full plugin audit workflow and checklists. |
| [build-skill/AGENTS.md](build-skill/AGENTS.md) | Building and improving Agent Zero skills. |
| [scheduled-tasks/AGENTS.md](scheduled-tasks/AGENTS.md) | Managing scheduled, planned, and adhoc tasks. |
