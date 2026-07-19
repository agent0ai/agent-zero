# Message Loop Start Extensions DOX

## Purpose

- Own backend behavior that runs at the start of each message loop iteration.

## Ownership

- Ordered Python files own iteration counters and future loop-start state setup.

## Local Contracts

- Keep per-loop counters deterministic and scoped to the active context.
- Do not reset state owned by monologue-level hooks.

## Work Guidance

- Coordinate loop-start state changes with logging, streaming, and process-chain behavior.

## Verification

- Smoke-test multi-turn conversations after changes.

## Child DOX Index

No child DOX files.
