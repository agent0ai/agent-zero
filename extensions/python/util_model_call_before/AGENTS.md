# Utility Model Call Before Extensions DOX

## Purpose

- Own preprocessing before utility model calls.

## Ownership

- Ordered Python files own secret masking and future utility-call preparation.

## Local Contracts

- Mask secrets before utility prompts leave the framework.
- Keep utility model inputs compatible with callers expecting structured outputs.

## Work Guidance

- Coordinate masking changes with main model call and error-format masking behavior.

## Verification

- Test utility model calls that include masked secret patterns after changes.

## Child DOX Index

No child DOX files.
