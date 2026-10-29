# Notification Components DOX

## Purpose

- Own WebUI toast, modal, icon, and notification store behavior.

## Ownership

- `notification-store.js` owns notification state and public helper actions.
- `notification-toast-stack.html` owns toast rendering.
- `notification-modal.html` owns notification detail modal UI.
- `notification-icons.html` owns shared notification icon markup.

## Local Contracts

- Use the notification system for user-facing success, warning, info, and error feedback.
- Keep public helper names stable for core and plugin callers.
- `notification_received` JS extensions receive `{ notification, source }` for backend arrivals/updates and frontend-only toasts before dismissal. `notification` is a shallow copy, `source` is `backend` or `frontend`, and dispatch does not delay rendering; consumers must deduplicate replayed snapshots and handle their own persistence failures.
- `notification-header-actions-start` hosts plugin actions before Clear All, including when the notification list is empty.
- Keep the toast stack visible above normal and legacy modal overlays while staying below confirmation dialogs.
- Toasts keep the shared copy icon with a visible `Copy` label below the scrolling content, aligned with the text; Dismiss stays at the top right. Copy the full rendered title and message as plain text without opening the modal or dismissing the toast; pause dismissal while hovered or keyboard-focused.
- Hide the copy row whenever the rendered toast content contains a button; text-only toasts keep Copy. Nested actions and Dismiss remain available, including when message content changes.
- Reload actions must persist their notification as read before refreshing the page.
- Avoid exposing secrets or raw auth payloads in notification text.

## Work Guidance

- Coordinate helper changes with plugin UI contracts and existing frontend imports.

## Verification

- Smoke-test toast display, dismiss, modal details, and notification severity styling; check copy feedback and full text from long, scrolled toasts at desktop and mobile widths.

## Child DOX Index

No child DOX files.
