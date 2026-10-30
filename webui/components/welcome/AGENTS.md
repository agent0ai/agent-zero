# Welcome Components DOX

## Purpose

- Own the WebUI welcome screen, discovery cards, banners, and related state.

## Ownership

- `welcome-screen.html` owns welcome screen markup and layout.
- `welcome-store.js` owns welcome state, banners, cards, and actions.
- `welcome-layout.js` owns block registration, browser-local order, drag/menu/keyboard interactions, and per-mount cleanup.

## Local Contracts

- Keep banner and discovery card behavior compatible with Python `banners` extensions.
- Supported banner/card CTA actions must stay synchronized with plugin discovery contracts.
- Banner body links may use `data-banner-action`; these actions route through the same welcome action dispatcher as CTA buttons.
- `open-modal:` banner actions may include a `#section-id` fragment, which updates the page hash before opening the modal so settings sections can deep-link correctly.
- Do not show setup prompts for already configured plugins when backend status can prevent it.
- Do not replace the welcome composer with blocking model setup UI; missing model setup is deferred to the chat thread on first send.
- The welcome screen mounts the shared chat composer to start a new chat; keep it mutually exclusive with the normal chat input DOM.
- Greeting/composer and Quick Actions can be hidden independently; `welcome_hidden_intro` and `welcome_hidden_quick-actions` persist these choices in localStorage. Hide with `x-show` so the mounted composer draft survives dismissal.
- The single "Show all dismissed" control appears below all blocks and extension content for hidden sections, notices, or discovery cards. `undismissAll()` restores all three through their owning stores, tolerating discovery not being mounted. Keep the control flush with the sections' left edge.
- Place section close controls beside their headings without extra cards. Greeting and Quick Actions close controls appear when their section is hovered or contains keyboard focus, and remain visible on touch devices. Match section and System Resources controls to discovery cards' muted close-button style; use the text color for these controls in light mode to retain contrast.
- Keep the welcome container background transparent so the persistent right-panel background transition remains visible when entering and leaving Welcome.
- Reserve the welcome composer's final minimum height before its nested input components hydrate.
- On mobile, keep composer actions on one row and reduce only the placeholder font; editable text stays at least 16px. Quick-action buttons use a flex layout with native appearance disabled for stable initial and touch sizing.
- Render `system-resources` as the dedicated System Resources panel, not as a generic alert banner.
- Utility quick actions from welcome must keep the first screen intact; use modal/floating entry points instead of docking the right canvas beside welcome content.

- The HTML is the block registry: direct children of `.welcome-board` opt in with a unique, nonempty `data-welcome-block` ID and `data-welcome-label`. IDs must not have surrounding whitespace. Use plugin-prefixed IDs for extensions. Missing metadata and duplicate IDs are excluded, with their move handles disabled.
- Put an empty `<button type="button" data-welcome-handle></button>` where the handle belongs. The controller supplies its icon, styling, accessible label, help and menu state. Blocks and handles may arrive asynchronously; a welcome-local observer registers additions, metadata changes, removal and replacement. Nested blocks do not register independently.
- `data-welcome-size="half"` opts into desktop pairing with the next visible half-width block. Any other value uses a full row. Lone half-width blocks expand; mobile remains one column.
- Preserve existing IDs (`intro`, `quick-actions`, `accounts`, `channels`, `system`) and the `welcome_block_order` localStorage array. Retain valid saved IDs while their plugins are absent, and append new IDs in discovery order. Reappearing blocks recover their position. Restoration changes visibility, not order.
- Drag only from dedicated handles. Preview with a label and insertion marker; commit real DOM order on drop so reading/tab order matches the layout. Ordinary loaders may rehydrate moved components; preserving an in-progress composer draft across reordering is not a requirement.
- Discovery keeps its Alpine ownership and teleports rendered cards into the two welcome slots. Notices stay above the board; restoration stays at the bottom, after `welcome-screen-end`. Other `welcome-actions-end` contributions stay below the board unless they opt into it through an Alpine teleport; their owning template controls cleanup.
- Handles support pointer capture, touch-only scroll prevention, edge scrolling, click/tap move options, arrow/Home/End keys, focus restoration, and live announcements. Cancel on Escape, pointer cancellation/lost capture, resize, blur, or unmount. Respect reduced motion and remove listeners/observers/drag overlays at unmount.

## Work Guidance

- Coordinate visual card or CTA changes with plugin discovery and onboarding surfaces.
- Keep reorder behavior local to welcome and its discovery contribution; shared component/extension loaders remain unchanged.
- A plugin's `welcome-actions-end` HTML extension can contribute a block with this pattern (put its content and styles in the same component):

  ```html
  <div x-data>
      <template x-teleport=".welcome-board">
          <section data-welcome-block="my-plugin.summary"
                   data-welcome-label="My summary" data-welcome-size="half">
              <header>
                  <h2>My summary</h2>
                  <button type="button" data-welcome-handle></button>
              </header>
              <p>Plugin content</p>
          </section>
      </template>
  </div>
  ```

- Keep the registered section as the teleport's single root; let Alpine remove it when the plugin scope is destroyed. Visibility/dismissal and card content remain the plugin's responsibility. No registration API, central ID list, or controller change is needed.

## Verification

- Smoke-test alert banners, feature cards, dismissal, priority ordering, and CTA actions after changes. Verify late plugin registration, removal/reappearance, duplicate IDs, hidden and orphan half-width blocks, metadata updates, and Home/End with more than five blocks.
- Run `node --test tests/test_welcome_sections.mjs tests/test_welcome_layout.mjs` and `pytest tests/test_welcome_composer_static.py -q` for section visibility, persistence, restoration, and composer contracts; check mouse/touch drag, ordinary touch scrolling, cancellation, reload persistence, hide/restore order, unmount/remount, keyboard focus, reduced motion, and both themes in the browser.

## Child DOX Index

No child DOX files.
