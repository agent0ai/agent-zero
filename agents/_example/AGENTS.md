# Example Agent Profile DOX

## Purpose

- Own the reference profile used to demonstrate bundled profile layout.
- Show how profile-local prompts, tools, and extensions fit beside `agent.yaml`.

## Ownership

- `agent.yaml` owns the example profile metadata.
- `prompts/` owns prompt override examples.
- `tools/` owns profile-local tool examples.
- `extensions/` owns profile-local lifecycle extension examples.

## Local Contracts

- Keep this profile generic, minimal, and safe to copy into user or plugin profile work.
- Do not add product behavior here that should live in a real bundled profile.
- Profile-local tools and extensions must follow the same contracts as root tools and extensions.

## Work Guidance

- Prefer simple examples that illustrate structure over complex behavior.
- Update related skill guidance when the example profile layout changes.

## Verification

- Manually inspect YAML and prompt filenames after edits.
- Run profile-loading tests when changing discovery or profile schema assumptions.

## Child DOX Index

No child DOX files.
