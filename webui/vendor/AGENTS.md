# WebUI Vendor Assets DOX

## Purpose

- Own vendored third-party browser libraries served by the WebUI.
- Keep external library updates intentional, isolated, and reviewable.

## Ownership

- Each direct child directory owns one vendored library or library bundle.
- Vendored files should be treated as upstream artifacts, with local edits avoided unless clearly documented.

## Local Contracts

- Do not edit vendored files for application behavior when a wrapper or caller can own the change.
- Preserve license, version, and distribution assumptions for third-party assets.
- Do not add package-manager caches, build outputs, or unrelated downloaded artifacts.

## Work Guidance

- Prefer replacing a vendor bundle with a clean upstream build over hand-editing minified files.
- Coordinate library path changes with all HTML, CSS, and JS imports.

## Verification

- Manually smoke-test UI paths that load an updated vendor library.
- Run frontend checks when imports or wrappers are covered.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [_ace/AGENTS.md](_ace/AGENTS.md) | Minimal Ace editor subset used by core editor surfaces. |
| [ace-min/AGENTS.md](ace-min/AGENTS.md) | Full minified Ace distribution and supporting assets. |
| [alpine/AGENTS.md](alpine/AGENTS.md) | Vendored Alpine.js core and collapse plugin. |
| [bootstrap/AGENTS.md](bootstrap/AGENTS.md) | Vendored Bootstrap JavaScript bundle for collapse and tooltip behavior. |
| [dompurify/AGENTS.md](dompurify/AGENTS.md) | Vendored DOMPurify sanitizer module. |
| [flatpickr/AGENTS.md](flatpickr/AGENTS.md) | Vendored Flatpickr date/time picker assets. |
| [google/AGENTS.md](google/AGENTS.md) | Vendored Google Material Symbols font and stylesheet. |
| [katex/AGENTS.md](katex/AGENTS.md) | Vendored KaTeX rendering assets. |
| [marked/AGENTS.md](marked/AGENTS.md) | Vendored Marked markdown parser module. |
