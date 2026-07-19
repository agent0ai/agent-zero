# DOMPurify Vendor DOX

## Purpose

- Own the vendored DOMPurify sanitizer module used for safe HTML rendering.

## Ownership

- `purify.es.mjs` owns the browser module imported by WebUI sanitization paths.

## Local Contracts

- Do not weaken sanitizer behavior through local edits.
- Keep import paths synchronized with markdown and message rendering code.

## Work Guidance

- Replace with a clean upstream module when updating.
- Coordinate sanitizer updates with security-sensitive rendering tests.

## Verification

- Run or manually exercise HTML/markdown rendering paths after changes.

## Child DOX Index

No child DOX files.
