# mcp_server_get_log.py DOX

## Purpose

- Own the `mcp_server_get_log.py` API endpoint.
- This module handles MCP server log requests for global or project scope.
- Keep this file-level DOX profile synchronized with `mcp_server_get_log.py` because this directory is intentionally flat.

## Ownership

- `mcp_server_get_log.py` owns the runtime implementation.
- `mcp_server_get_log.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `McpServerGetLog` (`ApiHandler`)
  - `async process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- The request accepts `server_name` and optional `project_name`; when `project_name` is present, logs resolve through the project-scoped MCP configuration.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `McpServerGetLog` is an `ApiHandler`.
- `McpServerGetLog` defines `process(...)`.
- Imported dependency areas include: `helpers.api`, `helpers.mcp_handler`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `MCPConfig.get_instance.get_server_log`, `MCPConfig.get_project_instance`, `MCPConfig.get_instance`.
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
