# mcp_servers_apply.py DOX

## Purpose

- Own the `mcp_servers_apply.py` API endpoint.
- This module handles MCP servers apply requests for global or project scope.
- Keep this file-level DOX profile synchronized with `mcp_servers_apply.py` because this directory is intentionally flat.

## Ownership

- `mcp_servers_apply.py` owns the runtime implementation.
- `mcp_servers_apply.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `McpServersApply` (`ApiHandler`)
  - `async process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- The request accepts `config` and optional `project_name`.
- Without `project_name`, the endpoint persists global `mcp_servers_config` through settings and refreshes the global `MCPConfig`.
- With `project_name`, the endpoint saves `.a0proj/mcp_servers.json` through `helpers.projects.save_project_mcp_servers(...)` and refreshes that project's merged MCP config.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `McpServersApply` is an `ApiHandler`.
- `McpServersApply` defines `process(...)`.
- Observed side-effect areas: filesystem writes, settings/state persistence.
- Imported dependency areas include: `helpers.api`, `helpers.mcp_handler`, `helpers.projects`, `helpers.settings`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `set_settings_delta`, `projects.save_project_mcp_servers`, `MCPConfig.refresh_project`, `time.sleep`, `MCPConfig.get_instance.get_servers_status`, `MCPConfig.get_instance`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
