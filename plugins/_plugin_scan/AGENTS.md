# Plugin Scanner DOX

## Purpose

- Own LLM-guided security scanning for third-party Agent Zero plugins.

## Ownership

- `helpers/prompt.py` owns scan prompt construction from selectable checks.
- `api/` owns scan queue, start, and synchronous run endpoints.
- `webui/` owns scan checks, prompt template, store, UI, and thumbnail.
- `plugin.yaml` and `README.md` own metadata and behavior notes.

- `socket/plugin_scan_run.py` reuses the synchronous scan operation, including temporary-context cleanup, with no default socket execution deadline.

## Local Contracts

- Keep scan prompts explicit about source handling, security categories, and report expectations. Dependency isolation is a selectable check and rates clearly unnecessary shared environment installs as Fail. Allow minimal shared dependencies with a documented need.
- Temporary scan contexts must be isolated and cleaned up as intended.
- Do not install or execute scanned plugin code as part of scanning unless explicitly designed and documented.

## Work Guidance

- Coordinate check schema changes with prompt builder and frontend selection UI.

## Verification

- Smoke-test a synchronous scan and selected-check scan after prompt or API changes.

## Child DOX Index

No child DOX files.
