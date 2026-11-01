# Response Stream End Extensions DOX

## Purpose

- Own finalization of assistant response stream content.

## Ownership

- Ordered Python files own final masking and stream-end log updates.

## Local Contracts

- Preserve final masking before response content is considered complete.
- Keep log state consistent with streamed chunks and final response text.
- Do not auto-promote native reasoning summaries into `thoughts` during normal response finalization; reasoning and `thoughts` remain separate channels. The explicit exception is reasoning-only recovery in `message_loop_result`, which preserves the emitted reasoning as thoughts before silently retrying.

## Work Guidance

- Coordinate finalization changes with live response and message rendering behavior.

## Verification

- Smoke-test response completion and persisted message display after changes.

## Child DOX Index

No child DOX files.
