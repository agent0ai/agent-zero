# mcp_server_scan.py DOX

## Purpose

- Own the `mcp_server_scan.py` API endpoint.
- Provide static and optional runtime inspection for a single MCP server draft before it is added to global or project MCP config.
- Keep this file-level DOX profile synchronized with `mcp_server_scan.py` because this directory is intentionally flat.

## Ownership

- `mcp_server_scan.py` owns the runtime implementation.
- `mcp_server_scan.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `McpServerScan` (`ApiHandler`)
  - `async process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- The request accepts a `server` draft object, `inspect_runtime`, `allow_remote_network`, and `allow_local_execution`.
- Remote runtime inspection may contact the configured MCP URL to list tools only when `allow_remote_network` is true and static checks have no errors.
- Local stdio runtime inspection must not execute unless `allow_local_execution` is true.
- Response data redacts `headers` and `env` values.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- Imported dependency areas include: `asyncio`, `helpers.api`, `helpers.mcp_handler`, `shutil`, `typing`, `urllib.parse`.

## Key Concepts

- Static checks report invalid URLs, non-HTTPS remote URLs, missing local commands, interpreter-style local commands, headers/env presence, and obvious prompt-injection markers in inspected tool descriptions.
- Static errors skip runtime inspection; remote network inspection and local command execution both require explicit trust flags.
- Runtime inspection creates a temporary `MCPConfig` in a worker thread so stdio/remote tool listing does not call `asyncio.run()` inside the request event loop.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Do not return secret values, raw environment values, or private files.
- Keep scanner warnings explicit about local command execution risk.

## Verification

- Run endpoint-specific or MCP helper tests for changed behavior; smoke-test remote URL and local-command scan paths when practical.

## Child DOX Index

No child DOX files.
