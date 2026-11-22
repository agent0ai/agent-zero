# anysearch_extract.py DOX

## Purpose

- Own the `anysearch_extract.py` agent tool.
- This module parses an arbitrary web page into readable content through
  the AnySearch `/v1/extract` endpoint. It complements
  `anysearch_search.py`, whose results already carry a parsed body.
- Keep this file-level DOX profile synchronized with
  `anysearch_extract.py` because this directory is intentionally flat.

## Ownership

- `anysearch_extract.py` owns the runtime implementation.
- `anysearch_extract.py.dox.md` owns durable notes about
  responsibilities, contracts, side effects, and verification for that
  implementation.
- Classes:
- `AnySearchExtract` (`Tool`)
  - `async execute(self, url=..., **kwargs)`
  - `_extract(self, url)`
  - `format_result(self, page, source=...)`
- Notable constants/configuration names: `ANYSEARCH_EXTRACT_LIMIT`.
- The HTTP client lives in `helpers/anysearch.py` (`extract`).

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return
  `helpers.tool.Response` from `execute(...)`.
- Network calls run through `asyncio.to_thread`, so the synchronous
  `requests` client never blocks the agent loop.
- Failures are converted to a `Response` message of the form
  `AnySearch extract failed: <reason>` and never raise out of `execute`;
  `handle_error` is called for logging.
- `break_loop` is always `False`.
- Page content is truncated to `ANYSEARCH_EXTRACT_LIMIT` characters with a
  `...(truncated)` marker, so a large page cannot flood the history.
- Update this file whenever tool arguments, output shape, `break_loop`
  behavior, intervention handling, prompt instructions, or side effects
  change.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`,
  `Tool`, `handle_error`, `extract`, `asyncio.to_thread`,
  `self.agent.handle_intervention`, `self.format_result`.
- Output is the page title, the url, and the parsed content.
- Authentication is optional; without `ANYSEARCH_API_KEY` requests are
  anonymous and rate limited per IP.
- Keep request/response, tool, or helper semantics documented here at the
  same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history
  persistence.
- Coordinate argument or behavior changes with prompt tool instructions
  and skill guidance.
- Respect intervention flow for long-running, external, or user-visible
  operations.

## Verification

- `helpers/anysearch.py` was verified against the live API anonymously:
  `extract("https://example.com")` returns the title `Example Domain`
  and a non-empty body; a non-URL string raises `ValueError` before any
  request is made.
- Tool level verification used a stubbed `helpers.tool` module: the
  success path formats title, url and content, and long content is
  truncated at `ANYSEARCH_EXTRACT_LIMIT`.
- No direct test reference was found by name search; choose the nearest
  behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
