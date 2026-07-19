# Chat Components DOX

## Purpose

- Own chat composer, attachments, message queue, navigation, and top-section component groups.

## Ownership

- `input/` owns composer input, progress, banners, and bottom action bars.
- `attachments/` owns drag/drop and attachment preview UI.
- `message-queue/` owns queued message display and store state.
- `navigation/` owns chat navigation state.
- `top-section/` owns chat header/top area.
- `model-gate-store.js` and `model-setup-gate.html` own the deferred in-thread model setup gate.

## Local Contracts

- Preserve Store Gating for all store-backed chat components.
- Use shared API, WebSocket, notification, and attachment helpers where available.
- Do not bypass CSRF or WebSocket state-sync expectations.
- The shared composer can be mounted on the Welcome screen with no selected chat; sending from that state must create and select a chat context before dispatch.
- Composer text uses the main UI font by default; typing a triple-backtick fence and pressing Enter turns that line into a visual code block that serializes back to fenced Markdown, while pasted fenced Markdown stays plain text.
- Missing model setup is gated at send intent: the first unconfigured send renders an in-thread setup card, keeps the pending prompt in browser session storage for refresh recovery, and must not call `/message_async` until a chat model is configured.
- While the setup gate is open, the composer remains typeable but send is blocked until setup succeeds.
- The setup gate must delegate Cloud/Local setup, account connections, and advanced model configuration to the existing onboarding and model-preset editor modals; do not duplicate provider/model/key forms inline.
- A connected OAuth account without Main/Utility model selection is its own gate state; route to model configuration and do not select models automatically.
- Model setup surfaces that change readiness must notify the gate with `model-setup-changed`, `model-configured`, or an existing modal/onboarding completion signal so the pending prompt can retry automatically.
- The top-section project selector, clock, and connection indicator must respect the instance-level mobile/desktop visibility preferences.

## Work Guidance

- Keep composer and attachment changes responsive across desktop and mobile.
- Coordinate payload changes with backend chat, upload, and WebSocket handlers.

## Verification

- Smoke-test sending, queued messages, attachments, drag/drop, and navigation after visible changes.
- Smoke-test the unconfigured first-send gate and automatic dispatch after model setup when touching model setup or send interception.

## Child DOX Index

No child DOX files.
