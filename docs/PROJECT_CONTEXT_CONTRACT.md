# Project Context Contract

This project uses a unified context manifest so agents can execute with the right operational context at runtime.

## Manifest

- Path: `project_context/agent_jumbo.context.yaml`
- Scope:
  - skills
  - commands
  - workflows
  - runbooks
  - guardrails
  - success criteria

## Validation

Run:

```bash
python3 scripts/validate_project_context.py
```

The validator enforces:

1. Required top-level sections exist.
2. Referenced files/paths exist for skills, commands, workflows, and runbooks.
3. Guardrails are explicit (`id`, `rule`).
4. Success criteria are measurable (`metric`, `target`, `evidence`).

## Operating rule

Any high-level project change should update the manifest and pass validator checks before release.

## Secrets handling contract

- Personal Access Tokens (PATs), API tokens, and credentials must be entered only in the Settings `Secrets Store` UI.
- Never place PATs/tokens in source code, docs examples as real values, commit messages, or chat/user prompts.
- Use placeholders in examples and messages (for example `YOUR_TOKEN_HERE` or `§§secret(MY_TOKEN)`), not live secrets.
