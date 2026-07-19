# KaTeX Vendor DOX

## Purpose

- Own vendored KaTeX assets used for math rendering.

## Ownership

- `katex.min.js` owns core rendering behavior.
- `katex.auto-render.min.js` owns auto-render support.
- `katex.min.css` owns KaTeX styling.
- `fonts/` owns every font asset referenced by `katex.min.css`.

## Local Contracts

- Do not hand-edit minified vendor files.
- Keep markdown/message rendering imports synchronized with asset paths.
- Keep the CSS font references fully available under `fonts/`.

## Work Guidance

- Replace from a clean upstream release when updating KaTeX.

## Verification

- Smoke-test markdown or message content containing math after changes.

## Child DOX Index

No child DOX files.
