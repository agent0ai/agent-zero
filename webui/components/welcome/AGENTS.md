# Welcome Components DOX

## Purpose

- Own the WebUI welcome screen, discovery cards, banners, and related state.

## Ownership

- `welcome-screen.html` owns welcome screen markup and layout.
- `welcome-store.js` owns welcome state, banners, cards, and actions.

## Local Contracts

- Keep banner and discovery card behavior compatible with Python `banners` extensions.
- Supported banner/card CTA actions must stay synchronized with plugin discovery contracts.
- Banner body links may use `data-banner-action`; these actions route through the same welcome action dispatcher as CTA buttons.
- `open-modal:` banner actions may include a `#section-id` fragment, which updates the page hash before opening the modal so settings sections can deep-link correctly.
- Do not show setup prompts for already configured plugins when backend status can prevent it.
- Do not replace the welcome composer with blocking model setup UI; missing model setup is deferred to the chat thread on first send.
- The welcome screen mounts the shared chat composer to start a new chat; keep it mutually exclusive with the normal chat input DOM.
- Render `system-resources` as the dedicated System Resources panel, not as a generic alert banner.
- Utility quick actions from welcome must keep the first screen intact; use modal/floating entry points instead of docking the right canvas beside welcome content.

## Work Guidance

- Coordinate visual card or CTA changes with plugin discovery and onboarding surfaces.
- Keep the lower welcome grid focused on Connect Channels, OAuth accounts, and System Resources unless the target design changes.

## Verification

- Smoke-test alert banners, feature cards, dismissal, priority ordering, and CTA actions after changes.

## Child DOX Index

No child DOX files.
