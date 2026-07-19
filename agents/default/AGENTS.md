# Default Agent Profile DOX

## Purpose

- Own base profile metadata and default prompt specifics inherited by specialized profiles.
- Provide the shared behavior layer for bundled and custom profiles.

## Ownership

- `agent.yaml` owns default profile metadata.
- `agent.system.main.specifics.md` owns default profile-specific system prompt content.
- Additional prompt overrides under this directory become shared defaults unless a child profile overrides them.

## Local Contracts

- Keep default behavior broad, framework-compatible, and safe for inheritance.
- Avoid role-specific instructions that belong in specialist profiles.
- Prompt filenames must match the framework prompt override names they target.

## Work Guidance

- Prefer small, explicit prompt changes with clear inheritance impact.
- Check bundled specialist profiles after changing default behavior.

## Verification

- Manually inspect YAML and prompt rendering assumptions after edits.
- Run prompt/profile tests when changing inherited prompt behavior.

## Child DOX Index

No child DOX files.
