# Plugin Skill References DOX

## Purpose

- Keep detailed plugin workflows loaded only when the task needs them.

## Ownership

- `implementation.md` owns manifest, backend, configuration, hooks, agent-facing skills and tools, and runtime guidance.
- `channel-commands.md` owns channel command reuse: framework APIs, authorization/context binding, effect adaptation, native platform commands, and verification.
- `webui.md` owns frontend examples, shared `x-overflow` integration, and UI verification.
- `review.md` owns evidence-based review; `contribute.md` owns standalone publication and Index submission.

## Local Contracts

- Cite current source owners; keep API payloads and examples aligned with their handlers.
- Keep skill callable guidance aligned with shared `skill_tools` registration. A migration moves the declaration to the skill and removes the standalone tool file.
- Keep `a0_version` authoring/review guidance aligned with `docs/developer/plugins.md`; it is optional manifest compatibility metadata with advisory Hub warnings.
- Keep local-only work separate from community publication and catalog discovery separate from security scanning.
- Preserve authentication, scope, user authorization, and unrelated runtime state.

## Work Guidance

- Prefer existing framework APIs and references over duplicate helpers or manual lifecycle shortcuts.
- Verify external Index requirements at submission time.

## Verification

- Check local reference links, skill loading, example syntax and applicable runtime workflows.
- Use fixture data for catalog filtering checks and live read-only discovery for schema verification.

## Child DOX Index

No child DOX files.
