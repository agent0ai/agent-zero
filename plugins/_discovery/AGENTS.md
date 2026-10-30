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
- The Welcome screen `welcome-actions-end` surface renders feature channel cards plus the compact OAuth account-provider card; other hero discovery cards stay out of the welcome board. The extension retains the discovery scope and teleports channels and the account-card list into `#welcome-channels` and `#welcome-accounts`; these slots must exist before the extension loads. The slots declare block IDs, labels and half-width sizing. Empty `data-welcome-handle` buttons are configured by the welcome layout controller.
- Welcome uses its single bottom "Show all dismissed" control for discovery cards too; do not render a second restore button there. `undismissCards()` clears discovery storage and returns its refresh promise. Onboarding retains its own discovery restore control.
- Do not hide discovery cards solely because model setup is incomplete; model setup gating belongs to the chat thread.

## Work Guidance

- Prefer backend status checks before surfacing setup or integration prompts.

## Verification

- Smoke-test welcome-screen discovery cards, ordering, dismissal, and CTA behavior after changes.

## Child DOX Index

No child DOX files.
