# JSON API Call After Extensions DOX

## Purpose

- Own frontend extension hooks that run after `callJsonApi()` calls.

## Ownership

- JavaScript files own after-call behavior such as cache reset handling.

## Local Contracts

- JavaScript modules must export a default function.
- Preserve JSON API response contracts and avoid hiding errors from callers.

## Work Guidance

- Keep global side effects narrow and tied to explicit API results or mutable contexts.

## Verification

- Smoke-test JSON API callers affected by extension changes.

## Child DOX Index

No child DOX files.
