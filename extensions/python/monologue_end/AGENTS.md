# Monologue End Extensions DOX

## Purpose

- Own backend behavior that runs when a monologue ends.

## Ownership

- Ordered Python files own waiting-for-input UI message behavior and future monologue-end cleanup.

## Local Contracts

- Preserve clear UI state when the agent stops for user input.
- Do not leave loading/processing indicators stale.

## Work Guidance

- Coordinate changes with WebUI loading state and message-loop persistence.

## Verification

- Smoke-test an agent response that returns to waiting-for-input state.

## Child DOX Index

No child DOX files.
