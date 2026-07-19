# Job Loop Extensions DOX

## Purpose

- Own periodic backend maintenance jobs.

## Ownership

- Ordered Python files own cleanup of expired API chats, cache trimming, and future job-loop tasks.

## Local Contracts

- Jobs must be idempotent and safe to run repeatedly.
- Keep cleanup scoped to owned caches, temporary contexts, or documented runtime state.

## Work Guidance

- Avoid expensive work on every loop; use timestamps or thresholds when practical.

## Verification

- Run targeted cleanup/cache tests or smoke-test job-loop startup after changes.

## Child DOX Index

No child DOX files.
