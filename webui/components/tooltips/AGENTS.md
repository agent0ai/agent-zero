# Tooltip Components DOX

## Purpose

- Own shared tooltip state and behavior for WebUI controls.

## Ownership

- `tooltip-store.js` owns tooltip state, positioning, and actions.

## Local Contracts

- Keep tooltip positioning compatible with desktop and mobile layouts.
- Do not make tooltips required for completing a workflow.

## Work Guidance

- Prefer concise tooltip text and stable positioning around icon-only controls.

## Verification

- Smoke-test hover/focus tooltip behavior after changes.

## Child DOX Index

No child DOX files.
