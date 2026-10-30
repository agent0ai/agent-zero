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
- Greeting/composer and Quick Actions can be hidden independently; `welcome_hidden_intro` and `welcome_hidden_quick-actions` persist these choices in localStorage. Hide with `x-show` so the mounted composer draft survives dismissal.
- The single upper "Show all dismissed" control appears for hidden sections, notices, or discovery cards. `undismissAll()` restores all three through their owning stores, tolerating discovery not being mounted. Keep the control flush with the section's left edge.
- Place section close controls beside their headings without extra cards. Greeting and Quick Actions close controls appear when their section is hovered or contains keyboard focus, and remain visible on touch devices. Match section and System Resources controls to discovery cards' muted close-button style; use the text color for these controls in light mode to retain contrast.
- Keep the welcome container background transparent so the persistent right-panel background transition remains visible when entering and leaving Welcome.
- Reserve the welcome composer's final minimum height before its nested input components hydrate.
- On mobile, keep composer actions on one row and reduce only the placeholder font; editable text stays at least 16px. Quick-action buttons use a flex layout with native appearance disabled for stable initial and touch sizing.
- Render `system-resources` as the dedicated System Resources panel, not as a generic alert banner.
- Utility quick actions from welcome must keep the first screen intact; use modal/floating entry points instead of docking the right canvas beside welcome content.

## Work Guidance

- Coordinate visual card or CTA changes with plugin discovery and onboarding surfaces.
- Keep the lower welcome grid focused on Connect Channels, OAuth accounts, and System Resources unless the target design changes.

## Verification

- Smoke-test alert banners, feature cards, dismissal, priority ordering, and CTA actions after changes.
- Run `node --test tests/test_welcome_sections.mjs` and `pytest tests/test_welcome_composer_static.py -q` for section visibility, persistence, restoration, and composer contracts; check hover, keyboard focus, touch, and both themes in the browser.

## Child DOX Index

No child DOX files.
