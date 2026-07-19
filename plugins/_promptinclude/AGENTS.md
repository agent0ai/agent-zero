# Prompt Include Plugin DOX

## Purpose

- Own automatic prompt injection of persistent behavioral rules and preferences from `*.promptinclude.md` files.

## Ownership

- `helpers/scanner.py` owns workspace scanning, ignore handling, token budgeting, and trimming.
- `prompts/` owns prompt-inclusion fragments.
- `extensions/` owns prompt injection hooks.
- `default_config.yaml`, `plugin.yaml`, `README.md`, and `webui/` own defaults, metadata, behavior notes, and settings UI.

## Local Contracts

- Respect gitignore-style filtering, per-file budgets, and total token budgets.
- Include only intended promptinclude files from configured workspaces.
- Keep scan result status fields accurate for skipped, cropped, and included files.

## Work Guidance

- Coordinate scanner changes with prompt fragments so included content is clearly attributed.

## Verification

- Smoke-test include, ignore, crop, and over-budget cases after scanner changes.

## Child DOX Index

No child DOX files.
