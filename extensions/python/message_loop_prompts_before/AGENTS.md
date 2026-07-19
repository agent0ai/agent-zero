# Message Loop Prompts Before Extensions DOX

## Purpose

- Own preprocessing before message-loop prompt construction.

## Ownership

- Ordered Python files own history organization waits and related prompt-preparation gates.

## Local Contracts

- Preserve history consistency before prompts are assembled.
- Avoid blocking indefinitely on background organization tasks.

## Work Guidance

- Keep waiting behavior observable and bounded.

## Verification

- Smoke-test prompt construction after chats with pending history organization.

## Child DOX Index

No child DOX files.
