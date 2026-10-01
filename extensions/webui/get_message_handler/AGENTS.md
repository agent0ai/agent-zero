# Get Message Handler Extensions DOX

## Purpose

- Own frontend extensions that provide or modify message rendering handlers.

## Ownership

- Files in this folder own handler registration behavior for rendered chat messages.

## Local Contracts

- JavaScript modules must export a default function when present.
- Preserve mutable context contracts used by `/js/messages.js`.
- The default function receives `{ type, handler }` and may assign a handler returning `{ element, ... }`. Register custom process-step types through the sibling `get_process_step_types` hook; standalone types are omitted.
- Pass the original handler argument as `log` to `drawProcessStep`. Keep each type's process/standalone role consistent when replacing a handler.
- Do not render unsanitized model or user content.

## Work Guidance

- Coordinate handler changes with message components and plugin message extensions.

## Verification

- Smoke-test message rendering for affected message types after changes.

## Child DOX Index

No child DOX files.
