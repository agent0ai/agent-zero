# History Tool Result Extensions DOX

## Purpose

- Own processing after tool results are added to history.

## Ownership

- Ordered Python files own tool-call file persistence and related history side effects.

## Local Contracts

- Preserve tool result traceability without leaking secrets.
- Keep file artifacts inside expected runtime/user-owned paths.
- Skip BACKGROUND contexts; background workers must remain ephemeral and must not create chat message files.

## Work Guidance

- Coordinate changes with tool output storage and chat persistence behavior.

## Verification

- Smoke-test a tool call that produces persisted output after changes.

## Child DOX Index

No child DOX files.
