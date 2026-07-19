# Get Message Handler Extensions DOX

## Purpose

- Own frontend extensions that provide or modify message rendering handlers.

## Ownership

- Files in this folder own handler registration behavior for rendered chat messages.

## Local Contracts

- JavaScript modules must export a default function when present.
- Preserve mutable context contracts used by `/js/messages.js`.
- Do not render unsanitized model or user content.

## Work Guidance

- Coordinate handler changes with message components and plugin message extensions.

## Verification

- Smoke-test message rendering for affected message types after changes.

## Child DOX Index

No child DOX files.
