# Agent 0 Profile DOX

## Purpose

- Own the main user-facing Agent Zero profile metadata.
- Keep the primary assistant profile discoverable and distinct from subordinate specialist profiles.

## Ownership

- `agent.yaml` owns the profile title, description, and delegation context.
- Prompt behavior is inherited from the default profile unless a local prompt override is added.

## Local Contracts

- Keep `Agent 0` suitable as the direct conversation agent for the system.
- Do not add narrow specialist behavior that belongs in `developer/`, `researcher/`, `hacker/`, or a custom user profile.
- Do not store user-specific preferences, provider settings, or secrets in this profile.

## Work Guidance

- Keep metadata concise because it appears in profile selection and delegation contexts.
- Coordinate substantial behavior changes with default prompts and WebUI profile selection.

## Verification

- Manually inspect `agent.yaml` for valid YAML after edits.
- Run profile-loading tests when changing schema or discovery behavior.

## Child DOX Index

No child DOX files.
