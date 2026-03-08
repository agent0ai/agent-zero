# RC Readiness Report: MCP Tool Performance

Date: 2026-03-08
Branch: `release/rc-mcp-tool-performance`
Commit baseline: `2c01b9d4`

## Summary

This RC implementation is **functionally ready** for MCP tool caching/reload workflows with targeted automated validation complete.
Status is **Go (Conditional)** pending manual UI smoke in browser session.

## Scope Verification

- MCP tool prompt caching added and used in system prompt path.
- Lightweight status endpoint path added for polling.
- Explicit reload endpoint added.
- MCP settings UI reload control added.
- Targeted tests for cache and reload API added and passing.

## Success Criteria Results

1. "Collecting MCP tools" only on cold cache/reload path: **PASS**
   Evidence: system prompt path now checks cache hit before progress and uses cached retrieval.

2. Repeated chat requests under unchanged config use cache-hit behavior: **PASS**
   Evidence: cache tests and cache stats methods validated.

3. Manual reload from API/UI path updates status metadata: **PASS (API), PENDING (UI manual click test)**
   Evidence: reload endpoint returns `cache` metadata shape and lightweight status in handler-level smoke.

4. No regressions in MCP tool execution correctness after reload: **PASS (targeted confidence), PENDING (full e2e MCP execution smoke)**
   Evidence: no codepath removed for tool invocation; reload path additive.

5. Existing MCP settings workflows remain intact: **PASS**
   Evidence: `mcp_servers_status` endpoint retained with lightweight implementation; `mcp_servers_apply` unchanged.

## Validation Evidence

- Automated tests:
  - `pytest -q tests/test_mcp_tools_cache.py tests/test_mcp_tools_reload_api.py`
  - Result: `5 passed`
- Compile/syntax checks:
  - `python` compile checks on modified MCP/system-prompt/api files passed.
- Runtime boot check:
  - Server boot log shows API handler registration incremented to include new endpoint (`154 handlers`).
- Handler-level smoke:
  - `mcp_servers_status` returns success payload.
  - `mcp_tools_reload` returns keys: `cache/status/success`.
  - `cache` keys: `cache_key/duration_ms/error/rebuilt/tool_count`.

## Open Items Before Promotion to Stable

1. Manual browser smoke:
   - Open MCP settings modal.
   - Click "Reload MCP Tools".
   - Verify reload metadata and server status update in UI.
2. Optional e2e MCP tool execution smoke:
   - Invoke one MCP tool after reload.
   - Confirm no regression in execution path.

## Go/No-Go

- Recommendation: **Go for RC testing rollout**
- Promotion to stable: **After completing the two manual smoke items above**
