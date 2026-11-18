# Plugin Skill References DOX

## Purpose

- Keep detailed plugin workflows loaded only when the task needs them.

## Ownership

- `discovery.md` owns Index fetching, candidate filtering and recommendation evidence.
- `lifecycle.md` owns scan, install, update, configuration, activation and removal APIs.

## Local Contracts

- Cite current source owners; keep API payloads and examples aligned with their handlers.
- Hub install guidance includes the read-only `check_compatibility` action and advisory `a0_version` mismatch/unknown handling; preserve explicit user overrides and security confirmation.
- Keep local-only work separate from community publication and catalog discovery separate from security scanning.
- Use the local socket helper for supported operations; preserve filesystem access, scope, user authorization and unrelated runtime state. Remote HTTP retains authentication/CSRF.

## Work Guidance

- Prefer existing framework APIs and references over duplicate helpers or manual lifecycle shortcuts.
- Verify external Index requirements at submission time.

## Verification

- Check local reference links, skill loading, example syntax and applicable runtime workflows.
- Use fixture data for catalog filtering checks and live read-only discovery for schema verification.

## Child DOX Index

No child DOX files.
