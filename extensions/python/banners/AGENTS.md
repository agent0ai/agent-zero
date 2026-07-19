# Banner Extensions DOX

## Purpose

- Own backend banner and discovery-card contributions.

## Ownership

- Ordered Python files append alert banners or discovery cards to the mutable `banners` list.

## Local Contracts

- Banner IDs must be unique and stable.
- Use supported banner/card fields and types only.
- Banner HTML links that trigger WebUI behavior should use supported structured actions, such as `data-banner-action`, instead of inline JavaScript handlers.
- Do not expose secrets, local paths, or raw system diagnostics in banner text.

## Work Guidance

- Gate setup or warning banners on current configuration/status where possible.

## Verification

- Smoke-test welcome-screen banner rendering, ordering, dismissal, and CTA behavior after changes.

## Child DOX Index

No child DOX files.
