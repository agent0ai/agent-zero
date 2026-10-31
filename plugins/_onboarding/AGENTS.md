# Onboarding Plugin DOX

## Purpose

- Own the built-in first-time onboarding wizard for model configuration.

## Ownership

- `plugin.yaml` owns metadata and always-enabled status.
- `webui/` owns onboarding providers, wizard store, modal/page markup, and thumbnail.

## Local Contracts

- Keep onboarding provider choices synchronized with model configuration and provider metadata.
- Do not ask for or expose API keys outside approved settings/API flows.
- Avoid blocking already-configured users with unnecessary onboarding prompts.
- Completion updates the selected global model preset (normally immutable-name `Default`); advanced setup opens that preset in the shared editor.
- Completing setup dispatches `onboarding-configured` so the model gate can resume its held message in the original chat. The Ready action is `Continue`: it closes the wizard without creating or selecting a chat, including when opened outside a chat.
- Cloud, Account, and Local share a left-aligned, neutral puzzle-icon text button below their provider grids. It replaces the Account/Local pane notes and closes onboarding without saving before opening Plugin Hub Browse with the exact `provider` tag filter and no previous search.

## Work Guidance

- Coordinate provider changes with `_model_config` and `_oauth` when account-backed providers are involved.

## Verification

- Smoke-test first-run onboarding, provider selection, completion, and skip/close behavior after changes.
- Run `node --test tests/test_onboarding.mjs` for preferred model selection, held-message continuation and the Ready action; run `pytest tests/test_onboarding_static.py` for markup/provider contracts.

## Child DOX Index

No child DOX files.
