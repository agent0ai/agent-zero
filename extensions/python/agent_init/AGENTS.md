# Agent Init Extensions DOX

## Purpose

- Own backend extensions that run when an agent context initializes.

## Ownership

- Ordered Python files own initial UI message setup and profile settings load behavior.

## Local Contracts

- Keep initialization idempotent for contexts that may be restored or reloaded.
- Preserve ordering between initial message creation and profile settings loading.

## Work Guidance

- Coordinate changes with profile loading, settings resolution, and startup smoke checks.

## Verification

- Smoke-test new chat/context initialization after changes.

## Child DOX Index

No child DOX files.
