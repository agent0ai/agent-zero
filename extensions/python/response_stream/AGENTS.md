# Response Stream Extensions DOX

## Purpose

- Own handling of full assistant response stream updates.

## Ownership

- Ordered Python files own response logging, include-alias replacement, and live response updates.

## Local Contracts

- Keep streaming output synchronized with UI log items.
- Preserve include-alias replacement semantics where prompts/tools rely on them.
- Do not expose unmasked secrets in live responses.

## Work Guidance

- Coordinate stream changes with chunk/end hooks and message rendering.

## Verification

- Smoke-test streamed responses, live updates, and include alias replacement after changes.

## Child DOX Index

No child DOX files.
