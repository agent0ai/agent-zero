# RC: MCP Tool Performance and Reload Reliability

## Release Candidate Goal

Reduce MCP tool collection latency in chat loops by introducing cache-first tool prompt assembly and explicit operator-triggered reload flows.

## Scope

- MCP tool catalog caching and prompt-fragment caching
- Explicit MCP reload API and UI interaction
- Lightweight MCP status polling behavior
- Observability for cache hit/miss and reload outcomes

## Out of Scope

- MCP protocol changes
- New third-party MCP providers
- Major prompt template redesign unrelated to MCP tool list rendering

## Functional Requirements

1. MCP tool prompt assembly uses a process-wide cache keyed by normalized MCP configuration.
2. Cache invalidates on MCP config changes.
3. Operator can trigger explicit reload without editing settings (`mcp_tools_reload` API).
4. MCP settings UI exposes explicit "Reload MCP Tools" interaction.
5. MCP status endpoint used by polling does not trigger heavy tool re-discovery.

## Non-Functional Requirements

1. Cache hit path must avoid network/tool discovery work.
2. First-load collection should happen once per cache key.
3. Reload operation returns deterministic structured metadata:
   - `rebuilt`
   - `cache_key`
   - `tool_count`
   - `duration_ms`
   - `error` (optional)
4. Degraded mode: if reload fails, last known good cache remains available.

## API and Interface Additions

- New API endpoint: `mcp_tools_reload`
  - Input: `force_reconnect` (boolean, optional)
  - Output: `success`, `status`, `cache`
- MCP settings UI:
  - Add explicit reload action/button
  - Show last reload status and timestamp

## Test and Validation Matrix

1. Cache behavior
   - First prompt build after cold start is miss+rebuild.
   - Subsequent prompt builds with unchanged config are hits.
2. Invalidation
   - MCP config change produces new cache key and rebuild.
3. Reload API
   - Reload succeeds and returns status+cache metadata.
   - Reload failure keeps prior cached prompt available.
4. UI behavior
   - Reload action triggers API call and status update.
   - Polling view remains responsive and does not induce heavy re-init loops.

## RC Success Criteria

1. "Collecting MCP tools" appears only on cold cache/reload path, not every normal chat turn.
2. Repeated chat requests under unchanged MCP config exhibit cache-hit behavior.
3. Manual reload from UI completes and updates status metadata.
4. No regressions in MCP tool execution correctness after reload.
5. No blocking failures in existing MCP settings workflows (`mcp_servers_apply`, `mcp_servers_status`).

## Release Gate Checklist

- [ ] Backend cache implemented with invalidation and metrics
- [ ] Reload API implemented and registered
- [ ] UI explicit reload interaction implemented
- [ ] Status path lightweight behavior verified
- [ ] Targeted automated tests added and passing
- [ ] Manual smoke tests completed and documented
