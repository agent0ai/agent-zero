# Init Framework End Extensions DOX

## Purpose

- Own frontend extensions that run after WebUI framework initialization.

## Ownership

- JavaScript files own post-bootstrap global setup such as self-update helpers and session-scoped UI restoration hooks.

## Local Contracts

- JavaScript modules must export a default function.
- Setup must be idempotent across reloads and cache resets.
- Do not register duplicate global listeners.

## Work Guidance

- Coordinate initialization changes with `/js/initFw.js` and component lifecycle directives.

## Verification

- Smoke-test WebUI startup and browser console after changes.

## Child DOX Index

No child DOX files.
