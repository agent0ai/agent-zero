# Fetch API Call After Extensions DOX

## Purpose

- Own frontend extension hooks that run after raw `fetchApi()` calls.

## Ownership

- Files in this folder own after-call behavior for CSRF-aware raw fetch flows.

## Local Contracts

- JavaScript modules must export a default function when present.
- Do not consume response bodies unless the hook contract explicitly passes a clone or mutable context for that purpose.

## Work Guidance

- Keep after-call extensions lightweight and safe for all fetch callers.

## Verification

- Smoke-test frontend API calls after adding behavior here.

## Child DOX Index

No child DOX files.
