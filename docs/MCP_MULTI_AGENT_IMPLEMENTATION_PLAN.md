# MCP Caching RC: Multi-Agent Implementation Plan

## Workstream A: Backend Cache Core

- Owner: Agent A (backend)
- Files:
  - `python/helpers/mcp_handler.py`
  - `python/extensions/system_prompt/_10_system_prompt.py`
- Deliverables:
  - Add cache key, cache payload, and cache stats for MCP tool prompts
  - Add cached prompt retrieval path used by system prompt extension
  - Add invalidation on config update
- Done when:
  - Cache hit avoids prompt rebuild and avoids repeated tool discovery
  - Existing behavior preserved for no-server and error paths

## Workstream B: API Reload and Status Semantics

- Owner: Agent B (backend API)
- Files:
  - `python/api/mcp_tools_reload.py` (new)
  - `python/api/mcp_servers_status.py`
  - `python/helpers/mcp_handler.py` (shared utility hooks only)
- Deliverables:
  - Implement explicit reload endpoint returning structured cache metadata
  - Ensure status polling path is lightweight and does not trigger heavy init loops
- Done when:
  - Reload endpoint is callable and returns deterministic payload
  - Status endpoint remains fast under repeated polling

## Workstream C: UI Operator Controls

- Owner: Agent C (frontend webui)
- Files:
  - `webui/components/settings/mcp/client/mcp-servers-store.js`
  - `webui/components/settings/mcp/client/mcp-servers.html`
- Deliverables:
  - Add "Reload MCP Tools" action
  - Display last reload outcome and timestamp
  - Preserve existing apply/status flows
- Done when:
  - Operator can reload without editing JSON config
  - UI reports result and does not block normal usage

## Workstream D: Tests and Validation

- Owner: Agent D (tests)
- Files:
  - `tests/` (targeted additions for mcp cache and reload API)
- Deliverables:
  - Unit coverage for cache hit/miss/invalidation
  - API test coverage for reload success/failure
  - Regression checks for existing MCP settings endpoints
- Done when:
  - Targeted test set passes locally in this branch

## Coordination Rules

- Keep write ownership disjoint where possible.
- Do not revert unrelated modified files in this branch.
- Shared file (`mcp_handler.py`) edits must be additive and merge-aware.
- Report changed files and acceptance evidence per workstream.
