# Local Socket Handlers DOX

## Purpose

- Own core handlers for the local Unix socket API, alongside HTTP handlers in `api/`.

## Ownership

- `helpers/socket_api.py` owns discovery, the handler base, JSON framing, socket permissions and lifecycle.
- `helpers/socket_cli.py` owns the standalone client and terminal entry point.
- Core handlers live here; plugin handlers live in `<plugin>/socket/`, next to `<plugin>/api/`.
- `ping.py` checks local socket readiness; startup/update readiness still uses HTTP `health`.
- Administration handlers explicitly reuse matching JSON API operations through `helpers/socket_handlers.py`: projects, chats/profile/control/queues, poll/history/export, plugins, notifications and profile catalog. Plugin-local handlers cover scheduler, installer, scan and Agent Editor.

## Local Contracts

- Do not add `__init__.py` here: a top-level `socket` package would shadow Python's standard library.
- Derive handlers from `helpers.socket_api.SocketHandler`; implement `async def process(self, input: dict) -> dict`.
- The dispatcher passes all entries of request `args` unchanged. Return JSON-safe dictionaries; the transport owns success/error envelopes.
- Raise `SocketError(code, message)` only for errors safe to expose to local callers. Other exceptions receive a generic error response.
- Keep operations asynchronous; offload blocking work, respect cancellation, and validate operation-specific inputs.
- Filesystem socket access authorizes invocation; it does not establish a trusted agent/chat identity. These administration handlers have instance-level authority, like an authenticated administrator. Chat controls require an existing explicit target, not an inferred current chat. Agent-tool handlers must separately establish trusted identity and apply action policy; caller-supplied IDs cannot do that. Do not proxy arbitrary tools/HTTP endpoints.
- Plugin route availability follows HTTP API discovery of installed plugins. Owning handlers enforce any activation or scoped-access requirements.

## Work Guidance

- Use shared feature helpers or explicit `JsonApiHandler` adapters for request-independent JSON operations. Adapters run in worker threads, normalize API errors and preserve structured failure details; do not synthesize Flask requests or sessions. Preserve existing HTTP and tool behavior.
- Read [the developer guide](../docs/developer/local-socket.md) for routes, limits, security and CLI examples.

## Verification

- Run `python -m pytest tests/test_socket_api.py` or `python3 -m unittest discover -s tests -p test_socket_api.py`.
- Keep real socket coverage for discovery, argument forwarding, framing, errors, permissions, startup, cleanup and CLI behavior.

## Child DOX Index

No child DOX files.
