# WebUI Public Assets DOX

## Purpose

- Own first-party static images, icons, splash art, and PWA assets served by the WebUI.
- Keep visual assets stable for core UI surfaces and settings sections.

## Ownership

- SVG files own first-party icons and settings/category symbols.
- Raster files own splash, thumbnail, and app-icon imagery.
- Asset filenames are part of the frontend reference contract when used by HTML, CSS, JS, or plugins.

## Local Contracts

- Do not add secrets, user uploads, generated runtime files, or private branding assets here.
- Keep asset paths stable or update every frontend reference in the same change.
- Prefer optimized web formats and reasonable file sizes for assets loaded during startup.

## Work Guidance

- Use this folder for shared first-party assets, not component-specific images that belong with a plugin or component.
- Check contrast and legibility for icon changes in both light and dark UI contexts when relevant.

## Verification

- Manually smoke-test pages that reference changed assets.
- Run frontend checks when asset references are covered by tests.

## Child DOX Index

No child DOX files.
