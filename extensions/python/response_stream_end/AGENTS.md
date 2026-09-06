# Response Stream End Extensions DOX

## Purpose

- Own finalization of assistant response stream content.

## Ownership

- Ordered Python files own final masking and stream-end log updates.

## Local Contracts

- Preserve final masking before response content is considered complete.
- Keep log state consistent with streamed chunks and final response text.
- Do not auto-promote native reasoning summaries into `thoughts` when explicit planning fields are absent; reasoning and `thoughts` are intentionally separate channels. Auto-population was removed (77e55152) as a maintainer UX call, not a bug fix — re-adding it requires an explicit maintainer decision.

## Work Guidance

- Coordinate finalization changes with live response and message rendering behavior.

## Verification

- Smoke-test response completion and persisted message display after changes.

## Child DOX Index

No child DOX files.
