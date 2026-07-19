# JSON API Call Before Extensions DOX

## Purpose

- Own frontend extension hooks that run before `callJsonApi()` calls.

## Ownership

- Files in this folder own before-call behavior for JSON API requests.

## Local Contracts

- JavaScript modules must export a default function when present.
- Preserve CSRF/auth behavior and JSON payload shape expected by `/js/api.js`.

## Work Guidance

- Avoid broad request mutation that affects unrelated plugin or core API calls.

## Verification

- Smoke-test affected JSON API calls after changes.

## Child DOX Index

No child DOX files.
