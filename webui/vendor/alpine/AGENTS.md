# Alpine Vendor DOX

## Purpose

- Own vendored Alpine.js browser runtime files used by the WebUI.

## Ownership

- `alpine.min.js` owns the Alpine core runtime.
- `alpine.collapse.min.js` owns the collapse plugin runtime.

## Local Contracts

- Do not modify vendored Alpine runtime files directly.
- Keep load order compatible with `webui/js/initFw.js` and component initialization.

## Work Guidance

- Update Alpine as a deliberate vendor bump and smoke-test component lifecycle directives.

## Verification

- Smoke-test WebUI startup, component loading, and store initialization after changes.

## Child DOX Index

No child DOX files.
