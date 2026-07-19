# Plugin Review Skill DOX

## Purpose

- Own the full audit workflow for Agent Zero plugins.
- Keep manifest, structure, code-pattern, security, and duplicate-detection checks current.

## Ownership

- `SKILL.md` owns the review workflow and phase order.
- `checklists.md` owns detailed review criteria loaded when needed.

## Local Contracts

- Keep review checks aligned with current plugin contracts, WebUI patterns, and Plugin Index expectations.
- Treat user plugins as `usr/plugins/` artifacts unless explicitly reviewing bundled core plugins.
- Do not expose secrets or private plugin data in review output.

## Work Guidance

- Update both `SKILL.md` and `checklists.md` when plugin conventions or security expectations change.
- Keep findings actionable and grouped by review phase.

## Verification

- Manually read changed skill files for stale paths, duplicated checks, and broken references.

## Child DOX Index

No child DOX files.
