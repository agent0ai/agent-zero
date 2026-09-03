# Agent Init Extensions DOX

## Purpose

- Own backend extensions that run when an agent context initializes.

## Ownership

- Ordered Python files own initial UI message setup and profile settings load behavior.

## Local Contracts

- Keep initialization idempotent for contexts that may be restored or reloaded.
- Preserve ordering between initial message creation and profile settings loading.
- `_10_initial_message.py` adds a placeholder user turn (`fw.initial_user_message.md`) before the AI greeting (`fw.initial_message.md`) so `output_langchain` does not pop the greeting as a leading `AIMessage`. Do not remove either prompt without replacing the turn-order guarantee.
- `_10_initial_message.py` minifies the initial AI message JSON before storage; raw text is preserved as the displayed greeting when JSON parsing fails.

## Work Guidance

- Coordinate changes with profile loading, settings resolution, and startup smoke checks.

## Verification

- Smoke-test new chat/context initialization after changes.

## Child DOX Index

No child DOX files.
