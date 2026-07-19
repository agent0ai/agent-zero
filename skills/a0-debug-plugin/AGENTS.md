# Plugin Debug Skill DOX

## Purpose

- Own the troubleshooting workflow for Agent Zero plugin loading, activation, API, frontend, extension, settings, and hook problems.

## Ownership

- `SKILL.md` owns diagnostic order, commands, and common failure cases.

## Local Contracts

- Keep route formats, import guidance, extension layouts, toggle files, and settings resolution aligned with runtime behavior.
- Do not recommend destructive cleanup unless the user explicitly asks and the target is clear.
- Keep diagnostics safe around secrets and local user data.

## Work Guidance

- Add checks when new plugin surfaces or loader failure modes are introduced.
- Prefer targeted commands that identify the first failing layer.

## Verification

- Manually read `SKILL.md` for stale commands and plugin path assumptions.

## Child DOX Index

No child DOX files.
