# Error Format Extensions DOX

## Purpose

- Own backend error formatting and masking before errors are shown or logged.

## Ownership

- Ordered Python files own mutation of error-format data passed by the hook.

## Local Contracts

- Preserve secret masking and safe user-facing error messages.
- Do not expose raw tokens, credentials, hidden prompts, or private payloads.

## Work Guidance

- Keep masking rules conservative and synchronized with tool/model error surfaces.

## Verification

- Test or inspect representative masked and unmasked error paths after changes.

## Child DOX Index

No child DOX files.
