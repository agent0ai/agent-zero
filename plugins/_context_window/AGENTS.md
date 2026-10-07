# Context Window Plugin DOX

## Purpose

- Own context-window token accounting, the usage API, the composer indicator,
  its popover, and its Interface visibility row.

## Ownership

- `helpers/usage.py` owns per-prompt bucket measurement and reconciliation.
- `helpers/currency.py` owns optional USD exchange-rate lookup and validation.
- `extensions/python/` records prompt parts at their source extension points,
  preserves terminal streamed usage, and captures optional provider usage.
- `api/context_window.py` exposes the active chat's token usage and effective
  model limit plus display flags and price-currency metadata without returning
  prompt content or modifying stored provider usage.
- `webui/` and `extensions/webui/` own the Alpine store, indicator, popover,
  model-override refresh, plugin display settings, and Interface visibility row.

## Local Contracts

- The six used-token buckets are `messages`, `system_tools`, `skills`,
  `mcp_tools`, `system_prompt`, and `extras`.
- Tools, MCP tools, and the available-skills catalog are measured from their
  extensible prompt builders, never inferred from rendered headings.
- Loaded skill instructions are removed from Messages and added to Skills.
- Protocol and prompt extras are reported together as Extras.
- Messages reuse the history record token ledger; independently rendered
  fragments use a bounded, content-addressed, runtime-only cache.
- Bucket totals reconcile to the already-stored prompt token total; the
  unclaimed remainder belongs to System prompt.
- If the history ledger would consume the whole prompt estimate, recompute only
  the rendered message portion before reconciliation; ordinary prompt builds
  keep the fast ledger path.
- The prompt estimate never guesses provider-specific image token costs or
  counts embedded image bytes as text.
- Provider price, cache hit, and input/output tokens form a flat summary without
  diagnostic detail rows and share the same regular-weight typography.
- Provider rows are exposed only when the provider or transport reports their
  values; unavailable price and cache data render no row.
- Global `show_breakdown`, `show_price`, `show_cache_hit`, and `show_tokens`
  settings default to true and apply on each usage refresh or popover opening.
  Hiding the breakdown also hides its empty state; hiding all provider rows
  removes their container and divider. Accounting and the summary remain intact.
- `price_currency` defaults to USD; USD never invokes the rate helper or makes
  an external request. Fetch Frankfurter's daily reference rate only for a
  visible, nonzero provider cost in a selected non-USD currency. Cache valid
  rates for 24 hours and failed lookups for five minutes. Only currency codes
  leave the server. Validate pair, positive finite rate, and date; on failure,
  show the original USD amount with an explicit USD label and explanation.
- Streaming main turns request LiteLLM's terminal usage event for every
  provider through the transport's `stream_options.include_usage` injection,
  so provider input/output and cache tokens reach the summary. The response
  callback still runs normally; only an actual Chat Completions result
  restores the accepted response after the accounting tail is drained.
- Responses API turns keep their native result and callback behavior unchanged.
- Older chats without a stored breakdown show the explanatory empty state.
- The indicator refreshes once per new Agent 0 generation, after four root-agent
  tool calls without another refresh, when the final response completes the run,
  and when the active chat log GUID changes (including Clear Chat). Streamed
  updates to an existing generation or tool log do not refetch it.
- `_model_config` supplies the effective model limit and the
  `model-context-strip-end` WebUI slot; it does not own this feature's state.
- The `contextWindowUsage` Interface setting defaults to visible on mobile and
  desktop.

## Work Guidance

- Keep prompt accounting out of rendered-text heuristics.
- Keep provider-reported usage separate from the six estimated context buckets.
- Keep the API response limited to usage counts, whitelisted display flags,
  and effective price-currency metadata.
- Preserve the upward, right-aligned popover beside the model/profile selectors. Its minimum strip footprint is bounded by the available width; shared `x-overflow` positions the same popover when the indicator enters the overflow menu. `data-overflow-label` names the entry; `data-overflow-icon` retains its live percentage ring.

## Verification

- Run `conda run -n a0 pytest plugins/_context_window/tests`.
- Smoke-test the indicator, popover, chat switching, post-run refresh, and
  mobile/desktop visibility against the live WebUI.

## Child DOX Index

No child DOX files.
