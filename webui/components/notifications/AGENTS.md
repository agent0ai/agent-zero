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
- Keep the toast stack visible above normal and legacy modal overlays while staying below confirmation dialogs.
- Reload actions must persist their notification as read before refreshing the page.
- Avoid exposing secrets or raw auth payloads in notification text.

## Work Guidance

- Coordinate helper changes with plugin UI contracts and existing frontend imports.

## Verification

- Smoke-test toast display, dismiss, modal details, and notification severity styling.

## Child DOX Index

No child DOX files.
