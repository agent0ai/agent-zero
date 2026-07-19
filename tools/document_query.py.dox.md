# document_query.py DOX

## Purpose

- Own the `document_query.py` agent tool.
- This module loads and queries documents through the document query plugin compatibility path.
- Keep this file-level DOX profile synchronized with `document_query.py` because this directory is intentionally flat.

## Ownership

- `document_query.py` owns the runtime implementation.
- `document_query.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Update this file whenever tool arguments, output shape, `break_loop` behavior, intervention handling, prompt instructions, or side effects change.
- Observed side-effect areas: plugin state.
- Imported dependency areas include: `plugins._document_query.tools.document_query`.

## Key Concepts

- This module is primarily declarative or delegates behavior through classes/imported objects.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with prompt tool instructions and skill guidance.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run targeted tool and prompt-contract tests for changed behavior; smoke-test agent execution when no focused test exists.
- Related tests observed by source search:
  - `tests/test_document_query_fallback.py`
  - `tests/test_document_query_plugin.py`

## Child DOX Index

No child DOX files.
