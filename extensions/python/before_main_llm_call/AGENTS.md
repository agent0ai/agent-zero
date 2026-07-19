# Before Main LLM Call Extensions DOX

## Purpose

- Own backend behavior that runs immediately before the main LLM call.

## Ownership

- Ordered Python files own pre-call logging or context preparation for streaming/model execution.

## Local Contracts

- Do not mutate prompt or history data unless the hook contract explicitly passes mutable state for that purpose.
- Avoid logging secrets, hidden prompt sections, or private user data.

## Work Guidance

- Keep this hook light because it sits on the main model hot path.

## Verification

- Run targeted model-call or streaming tests after behavior changes.

## Child DOX Index

No child DOX files.
