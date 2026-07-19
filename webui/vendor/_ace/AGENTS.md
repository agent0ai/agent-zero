# Ace Minimal Vendor DOX

## Purpose

- Own the minimal Ace editor files used by focused WebUI editor flows.

## Ownership

- JavaScript mode, theme, worker, and loader files are vendored Ace artifacts.
- `ace.min.css` owns local Ace styling required by the bundled files.

## Local Contracts

- Avoid hand-editing Ace source files; replace from a known upstream build when updating.
- Keep filenames stable for existing WebUI imports.

## Work Guidance

- Prefer adding only the modes and themes actually needed by core UI surfaces.

## Verification

- Smoke-test editor surfaces that load this subset after changes.

## Child DOX Index

No child DOX files.
