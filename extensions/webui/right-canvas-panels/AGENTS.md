# Right Canvas Panel Extensions DOX

## Purpose

- Own built-in HTML panel contributions for the right-canvas surface area.

## Ownership

- `.html` files mount WebUI components into the `right-canvas-panels` extension point.
- Panel wrappers own `data-surface-id` anchors and active/mounted visibility bindings.

## Local Contracts

- Each panel must correspond to a registered right-canvas surface ID.
- Use `<x-component>` for reusable component content instead of duplicating panel implementations.
- Keep canvas panels compatible with `.right-canvas-surface-panel` layout semantics.

## Work Guidance

- Prefer thin wrappers that delegate lifecycle and state to the owning component store.

## Verification

- Smoke-test opening the matching surface from the right-canvas rail.

## Child DOX Index

No child DOX files.
