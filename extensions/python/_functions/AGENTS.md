# Python Function Extensions DOX

## Purpose

- Own implicit `@extensible` backend hook implementations.
- Preserve nested module, class/function, method, and `start`/`end` extension layout.

## Ownership

- Each nested path mirrors a Python module and qualname segment.
- Leaf `start/` and `end/` directories own ordered extension files for that extensible function point.

## Local Contracts

- Do not flatten nested qualname paths into retired legacy folder names.
- Extension functions must match the implicit hook's supplied arguments.
- Preserve ordering prefixes where exception handling, watchdog registration, or cleanup depends on them.
- Hooks that mirror persisted AI responses into UI logs must reuse existing stream log items and avoid duplicating live response-tool logs.
- Recovery-loop circuit breakers must stop at the General Settings limit and render their user-visible cost warning from a core framework prompt.

## Work Guidance

- Keep implicit hook extensions narrow and colocated with the exact function point they extend.

## Verification

- Run targeted tests for the affected function point after changes.

## Child DOX Index

No child DOX files.
