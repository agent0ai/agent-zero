# Composer More Menu Extensions DOX

## Purpose

- Own built-in HTML contributions to the chat composer's "+" More actions menu.

## Ownership

- `.html` files mount menu items into the `chat-input-more-menu` extension point rendered at the end of `webui/components/chat/input/bottom-actions.html`.

## Local Contracts

- Contributions render one or more `.chat-bottom-menu-item` buttons; the host menu owns item styling and the column layout.
- Click handlers close the menu via `$store.chatInput.closeChatMoreMenu()` and stay store-driven; do not inject or patch menu DOM from scripts.
- Prefill actions only set composer text and focus; fragments must never send messages.

## Work Guidance

- Keep fragments thin and delegate behavior to the owning plugin's store; guard fragments that read another plugin's store so a disabled dependency renders nothing.

## Verification

- Open the composer menu and confirm contributed items render with menu styling and act without sending.

## Child DOX Index

No child DOX files.
