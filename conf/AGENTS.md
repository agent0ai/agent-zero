# Configuration Defaults DOX

## Purpose

- Own repository-shipped configuration defaults and templates.
- Keep clean-checkout defaults safe, portable, and free of user-specific state.

## Ownership

- `model_providers.yaml` defines built-in provider metadata and LiteLLM wiring defaults.
- `*.default.gitignore` files define templates copied or used for generated user/project/workdir directories.
- Runtime user settings belong under ignored `usr/` local state and are not documented with local DOX files.

## Local Contracts

- Do not commit API keys, provider secrets, local account identifiers, or private endpoints.
- Keep provider IDs and settings keys stable unless all loaders, UI references, migrations, and tests are updated.
- Defaults must work in a clean checkout and in Docker.
- Templates must avoid accidentally unignoring private runtime content.

## Work Guidance

- Prefer adding provider metadata here only when it is broadly useful to shipped Agent Zero.
- Keep comments concise and operational.
- Coordinate provider changes with model settings UI, plugin model overrides, and docs.

## Verification

- Run targeted model/provider tests after changing `model_providers.yaml`.
- Check generated ignore templates manually when changing `*.default.gitignore`.

## Child DOX Index

No child DOX files.
