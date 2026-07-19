# Right Canvas Surface Extensions DOX

## Purpose

- Own frontend registration of built-in right-canvas surfaces.

## Ownership

- JavaScript files own registration of remote link, space agent, file browser, and future core canvas surfaces.

## Local Contracts

- JavaScript modules must export a default function.
- Surface IDs must be unique and stable.
- Registered surfaces must point to valid components or handlers.

## Work Guidance

- Coordinate surface registration changes with `webui/components/canvas/` and related plugin panels.

## Verification

- Smoke-test opening each registered right-canvas surface after changes.

## Child DOX Index

No child DOX files.
