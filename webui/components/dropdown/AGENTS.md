# Dropdown Component DOX

## Purpose

- Own the shared dropdown component used by WebUI controls.

## Ownership

- `dropdown.html` owns dropdown markup, behavior hooks, and component-local styling.

## Local Contracts

- Keep keyboard, focus, and click-outside behavior compatible with existing callers.
- Avoid caller-specific assumptions in the shared dropdown.

## Work Guidance

- Prefer component attributes and slots over hardcoded option sets.

## Verification

- Smoke-test each caller that uses the dropdown after behavior changes.

## Child DOX Index

No child DOX files.
