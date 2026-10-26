# anysearch_vertical_search.py DOX

## Purpose

- Own the `anysearch_vertical_search.py` agent tool.
- This module searches a single vertical domain through AnySearch. A
  vertical domain is addressed with a `tag` such as `code.doc` or
  `finance.news`, which the SearxNG based `search_engine` tool cannot do.
- Unlike `anysearch_search.py`, which exposes `tag` as one optional
  argument among several, this tool exists so the vertical capability is
  discoverable on its own: the supported AnySearch capability set is
  general search, vertical domain search, and extract.
- Keep this file-level DOX profile synchronized with
  `anysearch_vertical_search.py` because this directory is intentionally
  flat.

## Ownership

- `anysearch_vertical_search.py` owns the runtime implementation.
- `anysearch_vertical_search.py.dox.md` owns durable notes about
  responsibilities, contracts, side effects, and verification for that
  implementation.
- Classes:
- `AnySearchVerticalSearch` (`Tool`)
  - `async execute(self, query=..., tag=..., params=..., max_results=..., zone=..., language=..., **kwargs)`
  - `_vertical_search(self, query, tag, params, max_results, zone, language)`
  - `format_result(self, results, source=...)`
- The HTTP client lives in `helpers/anysearch.py` (`search`,
  `AnySearchError`, `ANYSEARCH_BASE_URL`, `ANYSEARCH_TIMEOUT`).

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return
  `helpers.tool.Response` from `execute(...)`.
- Network calls run through `asyncio.to_thread`, so the synchronous
  `requests` client never blocks the agent loop.
- `tag` selects the vertical domain; some tags require `params` and answer
  with a business error when they are missing, which surfaces as
  `AnySearch vertical search failed: ...`.
- Failures never raise out of `execute`; `handle_error` is called for
  logging.
- `break_loop` is always `False`.
- Empty result sets return `AnySearch vertical search returned no results.`
- Update this file whenever tool arguments, output shape, `break_loop`
  behavior, intervention handling, prompt instructions, or side effects
  change.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`,
  `Tool`, `handle_error`, `search`, `asyncio.to_thread`,
  `self.agent.handle_intervention`, `self.format_result`.
- Output is one block per result: title, url, then the parsed page body
  (falling back to the snippet when no body is available).
- Authentication is optional. With no `ANYSEARCH_API_KEY` the request is
  sent anonymously and is rate limited per IP.
- Keep request/response, tool, or helper semantics documented here at the
  same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history
  persistence; `content` is already parsed, so a separate fetch is usually
  unnecessary.
- Prefer this tool over `anysearch_search.py` when the target domain is
  known, because a vertical request is narrower and cheaper than a general
  one.
- Respect intervention flow for long-running, external, or user-visible
  operations.

## Verification

- Tool level verification used a stubbed `helpers.tool` module: the success
  path forwards `tag` and `params` to `search(...)`, formats the results,
  and the failure path returns the `... failed: ...` message instead of
  raising.
- No direct test reference was found by name search; choose the nearest
  behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
