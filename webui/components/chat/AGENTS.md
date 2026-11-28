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
- Gate dispatch (`dispatchPendingIfConfigured`) captures `pending` before awaiting and uses that object for the payload; re-check its identity and the send latch after readiness resolves. Keep pending state and session recovery until the send is accepted. Busy sends defer retry until `sendMessage` settles; readiness and preset-editor reads use the pending chat's context. A retry for another context must never enter the selected chat's queue.
- Chat reset clears only that context's pending/connected setup gate and session recovery. In-flight readiness checks must observe the discarded pending identity and never resend its old prompt.

## Local Contracts

- Preserve Store Gating for all store-backed chat components.
- The Stop Speech control listens to TTS state and stays available during first-use preparation and playback.
- Use shared API, WebSocket, notification, and attachment helpers where available.
- Do not bypass CSRF or WebSocket state-sync expectations.
- The shared composer can be mounted on the Welcome screen with no selected chat; sending from that state must create and select a chat context before dispatch.
- The Welcome placeholder invites model setup or Settings while the existing `missing-api-key` banner is present; reuse Welcome's refreshed banner state without adding a readiness request or changing chat placeholders.
- Text-only and attachment sends must render the first user turn immediately with the request message ID so the backend log merges into the same row.
- Unsent composer text is kept as a separate browser-session draft for each selected chat and restored when switching contexts; a Welcome-screen prompt must follow the chat created for its first send. Preset changes and setup-gate retries must preserve any new unsent composer draft.
- The composer is a native textarea: typing, paste, and undo are the browser's own, with no paste interception or DOM builders. Do not reintroduce contenteditable machinery (custom insert commands, caret walkers, code-block elements) — it detaches edits from the native undo stack and conflicts with the full-screen input editor.
- The composer "+" More actions menu ends with the `chat-input-more-menu` extension point; plugins contribute `.chat-bottom-menu-item` buttons declaratively instead of injecting menu DOM from scripts, and built-in Goal mode and Skills entries load through it.
- The textarea composer auto-grows through the reset-then-measure pattern in `adjustTextareaHeight`, capped by its CSS maximum height with internal scrolling; keep the reset-then-measure order so stale heights never stick.
- The backend rejects dispatches when no chat model is configured: a `user_message_ui` extension in `_model_config` flags the chat and `/message_async` returns a `model_not_configured` payload before logging or dispatching. The client opens the setup gate from that response and must not round-trip a per-send configuration pre-check.
- While the setup gate is open, the composer remains typeable but send is blocked until setup succeeds.
- The setup gate must delegate Cloud/Local setup, account connections, and advanced model configuration to the existing onboarding and model-preset editor modals; do not duplicate provider/model/key forms inline.
- Beneath the three setup choices, a neutral puzzle-icon text link with no underline opens Plugin Hub Browse with the exact `provider` tag filter and clears previous Hub searches. Opening the Hub must preserve the pending prompt and existing setup retry flow.
- A connected OAuth account without Main/Utility model selection is its own gate state; route to model configuration and do not select models automatically.
- Model setup surfaces that change readiness must notify the gate with `model-setup-changed`, `model-configured`, or an existing modal/onboarding completion signal so the pending prompt can retry automatically.
- Rapid sends (clicks or Enter presses) cannot dispatch duplicate `/message_async` calls: the composer latch covers Welcome chat creation through dispatch and makes further sends or primary-button actions no-ops until it settles. The global send latch also protects direct and setup-gate dispatches before backend `running` state flips.
- Composer pause state is optimistic: a click in flight suppresses poll-snapshot writes to the pause flag until its request settles.
- The top-section project selector, clock, and connection indicator must respect the instance-level mobile/desktop visibility preferences.
- While the selected context is running, an empty composer makes the primary button stop the active run; typed text still adds to the queue, and Enter with an empty composer still sends queued messages.
- Pending queue items render image thumbnails from local blob URLs until the upload confirms; confirmed attachments use server `image_get` URLs, and a failed queue add drops its pending entry.
- Chat navigation controls must cross virtual message-window boundaries; top and bottom target the full cached history rather than only the mounted DOM slice.
- The page-wide attachment drop overlay must activate only for external file drags so internal WebUI drag interactions keep their own targets; elements marked `data-internal-dropzone` own external file drops in their subtree, so the overlay hides over them and the document drop handler leaves their files to the owning dropzone. While a modal or a visible legacy `.modal-overlay` surface is open the overlay yields entirely, so drops over modal targets never attach to the chat input.
- Picker, folder, and drag/drop attachments share the store's size gate against the Files transfer limit (`/get_work_dir_files?limits=1`); oversized files are rejected with an error toast while the rest of the batch attaches, and unavailable limits fail open.

## Work Guidance

- Keep composer and attachment changes responsive across desktop and mobile.
- The selector strip injected into `input/progress.html` uses shared `x-overflow` behavior; controls that do not fit stay reachable through the ellipsis menu, including late plugin additions. Preserve the separate full-width goal strip and speech-stop action.
- Coordinate payload changes with backend chat, upload, and WebSocket handlers.

## Verification

- Smoke-test sending, queued messages, attachments, drag/drop, and navigation after visible changes.
- Smoke-test the unconfigured first-send gate and automatic dispatch after model setup when touching model setup or send interception.

## Child DOX Index

No child DOX files.
