# Context Window Plugin DOX

## Purpose

- Own context-window token accounting, the usage API, the composer indicator,
  its popover, and its Interface visibility row.

## Ownership

- `helpers/usage.py` owns per-prompt bucket measurement and reconciliation.
- `extensions/python/` records prompt parts at their source extension points,
  preserves terminal streamed usage, and captures optional provider usage.
- `api/context_window.py` exposes the active chat's token usage and effective
  model limit without returning prompt content.
- `webui/` and `extensions/webui/` own the Alpine store, indicator, popover,
  model-override refresh, and Interface visibility row.

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
  diagnostic detail rows.
- Provider rows are exposed only when the provider or transport reports their
  values; unavailable price and cache data render no row.
- Streaming main turns request LiteLLM's terminal usage event for every
  provider through the transport's `stream_options.include_usage` injection,
  so provider input/output and cache tokens reach the summary. The response
  callback still runs normally; only an actual Chat Completions result
  restores the accepted response after the accounting tail is drained.
- Responses API turns keep their native result and callback behavior unchanged.
- Older chats without a stored breakdown show the explanatory empty state.
- The indicator refreshes once per new Agent 0 generation, when the run
  completes, and when the active chat log GUID changes (including Clear Chat);
  streamed updates to the same generation do not refetch it.
- `_model_config` supplies the effective model limit and the
  `model-context-strip-end` WebUI slot; it does not own this feature's state.
- The `contextWindowUsage` Interface setting defaults to visible on mobile and
  desktop.

## Work Guidance

- Keep prompt accounting out of rendered-text heuristics.
- Keep provider-reported usage separate from the six estimated context buckets.
- Keep the API response limited to counts needed by the UI.
- Preserve the upward, right-aligned popover geometry used beside the model and
  profile selectors, including its reserved footprint for short selector labels.

## Verification

- Run `conda run -n a0 pytest plugins/_context_window/tests`.
- Smoke-test the indicator, popover, chat switching, post-run refresh, and
  mobile/desktop visibility against the live WebUI.

## Child DOX Index

No child DOX files.
