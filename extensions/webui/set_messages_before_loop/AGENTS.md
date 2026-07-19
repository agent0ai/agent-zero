# Set Messages Before Loop Extensions DOX

## Purpose

- Own frontend extensions that run before message DOM updates.

## Ownership

- Files in this folder own pre-render message behavior.

## Local Contracts

- JavaScript modules must export a default function when present.
- Do not remove DOM state needed by message rendering unless the mutable context owns it.

## Work Guidance

- Coordinate pre-render behavior with `/js/messages.js` and message components.

## Verification

- Smoke-test message updates after changes.

## Child DOX Index

No child DOX files.
