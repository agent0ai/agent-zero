---
name: build-skill
description: Build or improve Agent Zero skills following the official SKILL.md standard. Use when the user asks to create, rename, move, audit, test, or refactor a skill, or when a workflow should be packaged as reusable skill instructions.
---

# Build Skill

Skills are small folders that teach Agent Zero a repeatable workflow. Keep the always-visible metadata precise, keep `SKILL.md` lean, and move detailed material into scripts, references, or assets only when the task needs it.

## Standard Shape

Every skill folder must be named exactly like the skill and contain `SKILL.md`.

```text
skill-name/
├── SKILL.md
├── scripts/      # optional deterministic helpers
├── references/   # optional details loaded only when needed
└── assets/       # optional output resources or templates
```

The frontmatter should contain only `name` and `description`:

```yaml
---
name: skill-name
description: What the skill does and when to use it. Include trigger wording here because this is the part visible before the skill loads.
---
```

Use lowercase letters, digits, and hyphens. Prefer short verb-led names such as `build-skill`, `review-plugin`, or `host-file-editing`.

## Workflow

1. Identify two or three real user requests that should trigger the skill.
2. Decide whether the skill belongs in core `skills/` or inside a plugin's `plugins/<plugin>/skills/` directory.
3. Write the frontmatter description with all trigger conditions and key contexts.
4. Keep the body focused on procedure, contracts, failure handling, and the files/scripts to load next.
5. Move long examples, schemas, policies, or variant-specific detail to one-level-deep `references/` files.
6. Add scripts only for deterministic or repeatedly rewritten operations, and test representative scripts.
7. Validate by searching, loading, and using the skill on a median-user prompt.

## Placement

Use plugin-scoped skills when the skill exists to explain a plugin-owned tool or UI surface. Examples: Browser workflows belong under `_browser`; A0 CLI host tools belong under `_a0_connector`; Desktop canvas workflows belong under `_desktop`.

Use root `skills/` for Agent Zero framework workflows that are not owned by one plugin, such as building skills, developing core features, or managing community plugins.

## Writing Rules

- Put trigger language in `description`, not in a body section. The body is loaded only after the skill is already selected.
- Do not add README, changelog, quick reference, or install guide files inside the skill.
- Avoid compatibility aliases in prompts or skill bodies when renaming; update references to the new name.
- Prefer concise examples over long prose.
- Do not duplicate the same guidance in both `SKILL.md` and references.
- When multiple skills could apply, keep each skill's responsibility narrow and name the handoff clearly.

## Validation

Run targeted checks after edits:

```bash
conda run -n a0 pytest tests/test_skills_runtime.py tests/test_tool_action_contracts.py -q
```

Also exercise the live path when the skill changes agent-facing tool behavior:

```text
1. Ask a short ordinary prompt that should discover the skill.
2. Confirm the agent uses skills_tool search/load when appropriate.
3. Confirm it calls the intended tool only after the skill is loaded when the tool is skill-gated.
```
