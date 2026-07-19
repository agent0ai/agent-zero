# Bootstrap Vendor DOX

## Purpose

- Own the vendored Bootstrap JavaScript bundle used for collapse and tooltip behavior.

## Ownership

- `bootstrap.bundle.min.js` owns Bootstrap runtime behavior.

## Local Contracts

- Do not hand-edit the minified vendor file for application behavior.
- Keep `webui/index.html` synchronized with the local bundle path.
- Bootstrap must be served locally and loaded with `defer` so startup does not wait on an external parser-blocking script.

## Work Guidance

- Replace from a clean upstream release when updating.

## Verification

- Smoke-test sidebar collapse controls and tooltips after changes.

## Child DOX Index

No child DOX files.
