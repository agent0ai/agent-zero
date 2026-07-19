# Plugin Validator DOX

## Purpose

- Own structured validation of Agent Zero plugins against manifest, structure, code-pattern, and security conventions.

## Ownership

- `helpers/prompt.py` owns validation prompt construction.
- `api/` owns ZIP preparation, queue, start, and synchronous run endpoints.
- `webui/` owns validation checks, guidance, prompt template, store, UI, and thumbnail.
- `plugin.yaml` and `README.md` own metadata and behavior notes.

## Local Contracts

- Keep validation criteria aligned with `plugins/AGENTS.md`, WebUI contracts, and Plugin Index requirements.
- Temporary validation source directories and contexts must be cleaned up as intended.
- Do not confuse runtime `plugin.yaml` with Plugin Index `index.yaml`.

## Work Guidance

- Coordinate checklist changes with prompt builder and frontend check selection.

## Verification

- Smoke-test local, Git, and ZIP validation paths when API or prompt behavior changes.

## Child DOX Index

No child DOX files.
