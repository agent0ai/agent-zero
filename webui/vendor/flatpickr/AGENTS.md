# Flatpickr Vendor DOX

## Purpose

- Own vendored Flatpickr date and time picker assets.

## Ownership

- `flatpickr.min.js` owns picker runtime behavior.
- `flatpickr.min.css` owns picker vendor styling.

## Local Contracts

- Do not hand-edit minified vendor files for application behavior.
- Keep scheduler and date-input imports synchronized with file paths.

## Work Guidance

- Replace from a clean upstream release when updating.

## Verification

- Smoke-test scheduler or date/time inputs after changes.

## Child DOX Index

No child DOX files.
