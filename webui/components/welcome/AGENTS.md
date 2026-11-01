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
- The adjacent puzzle button reads "Find welcome screen plugins", always remains visible, and opens Plugin Hub Browse with the `welcome` tag selected and any old search cleared. Both footer actions use muted text and icons, brighten smoothly on hover without a background, and wrap on narrow screens. Preserve a visible keyboard focus outline and respect reduced motion.
- `openWelcomePlugins(tag = "welcome")` also opens the channel shortcut with `channels`; use `welcome-panel-text-button` alongside `welcome-panel-icon-button` to share the footer's text-button styling.
- Place section close controls beside their headings without extra cards. The greeting close control and all Quick Actions header controls appear when their section is hovered or contains keyboard focus, and remain visible on touch devices. Match section and System Resources controls to discovery cards' muted close-button style; use the text color for these controls in light mode to retain contrast.
- Keep the welcome container background transparent so the persistent right-panel background transition remains visible when entering and leaving Welcome.
- Clip the decorative background with `overflow: clip`; do not create a nested hidden scroll container that can move when a block's handle receives focus.
- Reserve the welcome composer's final minimum height before its nested input components hydrate.
- Keep the greeting and decorative wave together on one line. Size the heading to the space left by its two 28px move/hide controls and their gaps using the header's inline-size container; preserve the normal desktop font size when it fits.
- On mobile, keep composer actions on one row and reduce only the placeholder font; editable text stays at least 16px. Quick-action buttons use a flex layout with native appearance disabled for stable initial and touch sizing.
- Render `system-resources` as the dedicated System Resources panel, not as a generic alert banner.
- System Resources defaults to a full row; its width control persists the half/full preference in `welcome_system_wide`. Honor half width on desktop even without a neighboring half-width block; mobile stays full width. Keep its meters and footer responsive to the panel width.
- Quick Actions defaults to a full row; its width control persists in `welcome_quick_actions_wide` and honors half width on desktop even when unpaired. Cards show only icons and titles, including plugin contributions. The `welcome-quick` container switches narrow panels to square tiles with titles below icons and keeps the website's external-link indicator.
- Utility quick actions from welcome must keep the first screen intact; use modal/floating entry points instead of docking the right canvas beside welcome content.

- The HTML is the block registry: direct children of `.welcome-board` opt in with a unique, nonempty `data-welcome-block` ID and `data-welcome-label`. IDs must not have surrounding whitespace. Use plugin-prefixed IDs for extensions. Missing metadata and duplicate IDs are excluded, with their move handles disabled.
- Put an empty `<button type="button" data-welcome-handle></button>` immediately before the dismiss control when present, after width/refresh controls. Card handles stay visible with the muted panel-button style and hover/focus feedback. Greeting/composer and Quick Actions handles appear with their close buttons on hover or keyboard focus; keep an open menu's handle visible and preserve touch visibility. The controller supplies its icon, styling, accessible label, help and menu state. Blocks and handles may arrive asynchronously; a welcome-local observer registers additions, metadata changes, removal and replacement. Nested blocks do not register independently.
- `data-welcome-size="half"` opts into desktop pairing with the next visible half-width block. Any other value uses a full row. Lone half-width blocks expand by default; Quick Actions and System Resources honor their explicit width choices. Mobile remains one column.
- Discovery slots and their rendered cards stretch to match their row, with content aligned at the top, and provide the `welcome-discovery` inline-size container for card-local responsive layouts.
- Preserve existing IDs (`intro`, `quick-actions`, `accounts`, `channels`, `system`) and the `welcome_block_order` localStorage array. Retain valid saved IDs while their plugins are absent, and append new IDs in discovery order. Reappearing blocks recover their position. Restoration changes visibility, not order.
- Drag only from dedicated handles. Preview with a label and insertion marker; commit real DOM order on drop so reading/tab order matches the layout. Ordinary loaders may rehydrate moved components; preserving an in-progress composer draft across reordering is not a requirement.
- Discovery keeps its Alpine ownership and teleports rendered cards into the two welcome slots. Notices stay above the board; restoration stays at the bottom, after `welcome-screen-end`. Other `welcome-actions-end` contributions stay below the board unless they opt into it through an Alpine teleport; their owning template controls cleanup.
- Handles support pointer capture, touch-only scroll prevention, edge scrolling, click/tap move options, arrow/Home/End keys, focus restoration, and live announcements. Cancel on Escape, pointer cancellation/lost capture, resize, blur, or unmount. Respect reduced motion and remove listeners/observers/drag overlays at unmount.
- Keep move options open when focus passes between their buttons; use the focus event's destination rather than the temporarily unfocused document state.

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
