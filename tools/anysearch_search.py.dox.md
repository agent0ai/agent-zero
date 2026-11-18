# anysearch_search.py DOX

## Purpose

- Own the `anysearch_search.py` agent tool.
- This module runs web search through AnySearch, a search infrastructure
  built for AI agents. It also covers vertical domain search through a
  `tag` (for example `code.doc`), which the SearxNG based `search_engine`
  tool cannot do.
- Keep this file-level DOX profile synchronized with
  `anysearch_search.py` because this directory is intentionally flat.

## Ownership

- `anysearch_search.py` owns the runtime implementation.
- `anysearch_search.py.dox.md` owns durable notes about responsibilities,
  contracts, side effects, and verification for that implementation.
- Classes:
- `AnySearchSearch` (`Tool`)
  - `async execute(self, query=..., max_results=..., tag=..., zone=..., language=..., **kwargs)`
  - `_search(self, query, max_results, tag, zone, language)`
  - `format_result(self, results, source=...)`
- Notable constants/configuration names: `ANYSEARCH_MAX_RESULTS`.
- The HTTP client lives in `helpers/anysearch.py` (`search`, `extract`,
  `AnySearchError`, `ANYSEARCH_BASE_URL`, `ANYSEARCH_TIMEOUT`).

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return
  `helpers.tool.Response` from `execute(...)`.
- Network calls run through `asyncio.to_thread`, so the synchronous
  `requests` client never blocks the agent loop.
- Failures are converted to a `Response` message of the form
  `AnySearch search failed: <reason>` and never raise out of `execute`;
  `handle_error` is called for logging.
- `break_loop` is always `False`.
- Empty result sets return `AnySearch search returned no results.`
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
- Coordinate argument or behavior changes with prompt tool instructions
  and skill guidance.
- Respect intervention flow for long-running, external, or user-visible
  operations.

## Verification

- `helpers/anysearch.py` was verified against the live API anonymously:
  general search, `tag="code.doc"` vertical search with
  `params={"library": "golang"}`, a negative case where the required
  `params` are missing (the API answers with a business error and the
  client raises `AnySearchError`), and `extract` of
  `https://example.com` returning the title `Example Domain`.
- Tool level verification used a stubbed `helpers.tool` module: the
  success path formats results, and the failure path returns the
  `... failed: ...` message instead of raising.
- No direct test reference was found by name search; choose the nearest
  behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
