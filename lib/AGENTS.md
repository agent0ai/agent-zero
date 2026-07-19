# Library Assets DOX

## Purpose

- Own small browser-side helper scripts outside the main WebUI module tree.
- Keep injected browser automation assets stable and narrowly scoped.

## Ownership

- `browser/` contains scripts used by browser automation and DOM extraction flows.
- Main WebUI code belongs under `webui/`.

## Local Contracts

- Browser helper scripts must not depend on unavailable bundlers or Node build steps.
- Keep scripts safe to inject into arbitrary pages by minimizing global side effects.
- Do not collect secrets or page data beyond what the calling tool explicitly needs.

## Work Guidance

- Prefer plain JavaScript with clear inputs and outputs.
- Coordinate DOM extraction changes with browser tools, browser plugins, and tests.
- Avoid adding large third-party libraries here.

## Verification

- Run browser-agent or browser-tool regression tests after changing browser helper scripts.
- Manually smoke-test browser flows when tests do not cover the changed path.

## Child DOX Index

No child DOX files.
