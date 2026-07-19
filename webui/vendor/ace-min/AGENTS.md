# Ace Min Vendor DOX

## Purpose

- Own the full minified Ace editor distribution and static assets.

## Ownership

- `ace.js`, extensions, modes, themes, workers, keybindings, and image assets are vendored Ace artifacts.

## Local Contracts

- Treat files as upstream-generated assets.
- Do not hand-edit minified or generated files for product behavior.
- Preserve referenced asset filenames unless all imports are updated.

## Work Guidance

- Replace this directory with a clean upstream distribution when updating Ace.
- Keep unrelated generated files and local caches out of this vendor bundle.

## Verification

- Smoke-test editor and code-input surfaces after vendor updates.

## Child DOX Index

No child DOX files.
