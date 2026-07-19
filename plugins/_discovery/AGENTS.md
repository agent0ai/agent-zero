# Plugin Discovery DOX

## Purpose

- Own contextual plugin discovery cards and welcome-screen promotions.

## Ownership

- `plugin.yaml` owns metadata and always-enabled status.
- `extensions/` owns backend or WebUI discovery contributions.
- `webui/discovery-store.js` owns discovery UI state and actions.

## Local Contracts

- Discovery cards must be accurate, dismissible where appropriate, and avoid advertising already-complete setup.
- CTA actions must match supported welcome-screen action contracts.
- Keep card IDs unique and plugin-prefixed.
- The Welcome screen `welcome-actions-end` surface renders feature channel cards plus the compact OAuth account-provider card; other hero discovery cards stay out of the lower welcome grid.
- Do not hide discovery cards solely because model setup is incomplete; model setup gating belongs to the chat thread.

## Work Guidance

- Prefer backend status checks before surfacing setup or integration prompts.

## Verification

- Smoke-test welcome-screen discovery cards, ordering, dismissal, and CTA behavior after changes.

## Child DOX Index

No child DOX files.
