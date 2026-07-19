# response.py DOX

## Purpose

- Own the `response.py` agent tool.
- This module emits the final or intermediate agent response to the user.
- Keep this file-level DOX profile synchronized with `response.py` because this directory is intentionally flat.

## Ownership

- `response.py` owns the runtime implementation.
- `response.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ResponseTool` (`Tool`)
  - `async execute(self, **kwargs)`
  - `async before_execution(self, **kwargs)`
  - `async after_execution(self, response, **kwargs)`

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Update this file whenever tool arguments, output shape, `break_loop` behavior, intervention handling, prompt instructions, or side effects change.
- `ResponseTool` is a `Tool`.
- `ResponseTool` defines `execute(...)`.
- Imported dependency areas include: `helpers.tool`.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with prompt tool instructions and skill guidance.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run targeted tool and prompt-contract tests for changed behavior; smoke-test agent execution when no focused test exists.
- Related tests observed by source search:
  - `tests/chunk_parser_test.py`
  - `tests/rate_limiter_test.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_chat_compaction.py`
  - `tests/test_dirty_json.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_fasta2a_client.py`
  - `tests/test_fastmcp_openapi_security.py`

## Child DOX Index

No child DOX files.
