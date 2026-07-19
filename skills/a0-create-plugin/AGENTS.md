# Plugin Creation Skill DOX

## Purpose

- Own the workflow for creating, extending, or modifying Agent Zero plugins.
- Keep full-stack plugin conventions accurate for API, tools, extensions, settings UI, and WebUI integration.

## Ownership

- `SKILL.md` owns trigger metadata, plugin scaffold guidance, manifest rules, and frontend/backend patterns.

## Local Contracts

- New custom plugins must default to `usr/plugins/`.
- Keep plugin manifest, settings, extension layout, Store Gating, and notification guidance synchronized with `plugins/AGENTS.md` and WebUI contracts.
- Do not recommend hardcoding secrets, bypassing auth, or persistent unmanaged side effects.

## Work Guidance

- Update this skill when plugin loader, Plugin Hub, settings modal, extension, or WebUI patterns change.
- Keep code examples short and aligned with current helper APIs.

## Verification

- Manually read `SKILL.md` for stale paths and broken handoffs to related plugin skills.

## Child DOX Index

No child DOX files.
