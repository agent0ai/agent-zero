# Marked Vendor DOX

## Purpose

- Own the vendored Marked markdown parser module.

## Ownership

- `marked.esm.js` owns markdown parsing behavior imported by WebUI rendering code.

## Local Contracts

- Do not hand-edit the vendored parser for application behavior.
- Keep parser updates coordinated with sanitization and message rendering expectations.

## Work Guidance

- Replace with a clean upstream module when updating.

## Verification

- Smoke-test markdown rendering after changes.

## Child DOX Index

No child DOX files.
