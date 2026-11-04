# anysearch_parallel_search.py DOX

## Purpose

- Own the `anysearch_parallel_search.py` agent tool.
- This module fans several queries out against AnySearch concurrently.
  AnySearch exposes no batch endpoint, so parallel search issues one
  request per query from a thread pool and returns a mapping from query to
  results.
- Together with `anysearch_search.py`, `anysearch_vertical_search.py` and
  `anysearch_extract.py` this covers the supported AnySearch capability
  set: general search, vertical domain search, and extract.
- Keep this file-level DOX profile synchronized with
  `anysearch_parallel_search.py` because this directory is intentionally
  flat.

## Ownership

- `anysearch_parallel_search.py` owns the runtime implementation.
- `anysearch_parallel_search.py.dox.md` owns durable notes about
  responsibilities, contracts, side effects, and verification for that
  implementation.
- Classes:
- `AnySearchParallelSearch` (`Tool`)
  - `async execute(self, queries=..., max_results=..., max_workers=..., tag=..., zone=..., language=..., **kwargs)`
  - `_parallel_search(self, queries, max_results, max_workers, tag, zone, language)`
  - `_normalize_queries(self, queries)`
  - `format_result(self, batches, source=...)`
- The fan-out itself lives in `helpers/anysearch.py` (`search_parallel`),
  so the tool stays a thin adapter.

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return
  `helpers.tool.Response` from `execute(...)`.
- Network calls run through `asyncio.to_thread`, so the thread pool never
  blocks the agent loop.
- `queries` accepts a list, a tuple, a set, or a newline separated string;
  `_normalize_queries` trims blanks and drops duplicates. The model passes
  whichever shape it feels like, so accepting both avoids a wasted turn.
- Duplicate queries are collapsed and the mapping follows the input order.
- A query that fails maps to an empty list. One bad query must not destroy
  the results of the others: that is the point of fanning out.
- An empty query list returns
  `AnySearch parallel search failed: no query given`.
- Failures never raise out of `execute`; `handle_error` is called for
  logging.
- `break_loop` is always `False`.
- Update this file whenever tool arguments, output shape, `break_loop`
  behavior, intervention handling, prompt instructions, or side effects
  change.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`,
  `Tool`, `handle_error`, `search_parallel`, `asyncio.to_thread`,
  `self.agent.handle_intervention`, `self.format_result`.
- Output is one `Query: <query>` header per query, followed by its result
  blocks, or `(no results)` when that query came back empty.
- Authentication is optional. With no `ANYSEARCH_API_KEY` requests are sent
  anonymously and are rate limited per IP.
- Keep request/response, tool, or helper semantics documented here at the
  same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history
  persistence; `content` is already parsed, so a separate fetch is usually
  unnecessary.
- Keep the batch small. The written warnings apply per request, so fanning
  out twenty queries multiplies the cost by twenty.
- Respect intervention flow for long-running, external, or user-visible
  operations.

## Verification

- Tool level verification used a stubbed `helpers.tool` module: a newline
  separated string is normalized and deduplicated, results are labelled per
  query, an empty list is rejected, and the failure path returns the
  `... failed: ...` message instead of raising.
- No direct test reference was found by name search; choose the nearest
  behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
