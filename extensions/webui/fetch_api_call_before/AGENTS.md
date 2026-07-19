# Fetch API Call Before Extensions DOX

## Purpose

- Own frontend extension hooks that run before raw `fetchApi()` calls.

## Ownership

- Files in this folder own before-call behavior for CSRF-aware raw fetch flows.

## Local Contracts

- JavaScript modules must export a default function when present.
- Preserve CSRF, auth, and redirect behavior owned by `/js/api.js`.

## Work Guidance

- Avoid broad request mutation that surprises unrelated API callers.

## Verification

- Smoke-test affected frontend API calls after changes.

## Child DOX Index

No child DOX files.
