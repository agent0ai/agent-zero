# Monologue Start Extensions DOX

## Purpose

- Own backend behavior that runs when a monologue starts.

## Ownership

- Ordered Python files own automatic chat renaming and future monologue-start setup.

## Local Contracts

- Keep automatic rename behavior bounded and non-destructive.
- Do not override explicit user chat names without the intended guard conditions.
- Surface Utility Model rename failures with one scoped error notification per chat.

## Work Guidance

- Coordinate rename behavior with chat persistence and WebUI refresh after successful saves.

## Verification

- Smoke-test new chat naming and existing named chat behavior after changes.

## Child DOX Index

No child DOX files.
