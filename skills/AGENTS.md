# Bundled Skills DOX

## Purpose

- Own bundled Agent Zero skills and their agent-facing instructions.
- Keep skill workflows accurate, composable, and safe for runtime loading.

## Ownership

- Each direct skill directory owns its `SKILL.md` and any local supporting files.
- Plugin-distributed skills belong under the relevant plugin directory.
- `setup-a0-cli/` owns primary host-connector setup guidance and remains discoverable without a connected CLI.
- User-local skills belong under `usr/skills/`.

## Local Contracts

- Every skill directory must include a `SKILL.md`.
- Skill instructions must be operational and scoped to the skill's purpose.
- Do not include secrets, private user data, or environment-specific credentials.
- Supporting files referenced by a skill must exist relative to that skill directory.
- Keep bundled catalog descriptions within the 100-character prompt preview, with distinct task and environment/format boundaries. Keep lexical triggers separate.

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
| [a0-create-agent/AGENTS.md](a0-create-agent/AGENTS.md) | Creating Agent Zero agent profiles. |
| [a0-create-plugin/AGENTS.md](a0-create-plugin/AGENTS.md) | Plugin authoring entrypoint with implementation, UI, review, and contribution references. |
| [a0-development/AGENTS.md](a0-development/AGENTS.md) | Broad Agent Zero framework development guidance. |
| [a0-manage-plugin/AGENTS.md](a0-manage-plugin/AGENTS.md) | Plugin Index discovery/recommendations and lifecycle operations. |
| [build-skill/AGENTS.md](build-skill/AGENTS.md) | Building and improving Agent Zero skills. |
| [scheduled-tasks/AGENTS.md](scheduled-tasks/AGENTS.md) | Managing scheduled, planned, and adhoc tasks. |
