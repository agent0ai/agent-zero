# fasta2a_server.py DOX

## Purpose

- Own the `fasta2a_server.py` helper module.
- This module serves Agent Zero through a dynamic A2A proxy.
- Keep this file-level DOX profile synchronized with `fasta2a_server.py` because this directory is intentionally flat.

## Ownership

- `fasta2a_server.py` owns the runtime implementation.
- `fasta2a_server.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `AgentZeroFastA2A` (`FastA2A`)
  - `async _agent_card_endpoint(self, request: Request) -> StarletteResponse`
- `AgentZeroWorker` (`Worker`)
  - `async run_task(self, params: Any) -> None`
  - `async cancel_task(self, params: Any) -> None`
  - `build_message_history(self, history: List[Any]) -> List[Message]`
  - `build_artifacts(self, result: Any) -> List[Artifact]`
- `DynamicA2AProxy` (no explicit base class)
  - `get_instance()`
  - `reconfigure(self, token: str)`
- Top-level functions:
- `_enable_streaming_capability(agent_card_body: bytes) -> bytes`: Ensure the generated A2A agent card advertises streaming support.
- `is_available()`: Check if FastA2A is available and properly configured.
- `get_proxy()`: Get the FastA2A proxy instance.
- `_inject_project(body: bytes, project_name: str) -> bytes`: set `params.message.metadata.project` in a JSON-RPC body; returns the body unchanged when it is not JSON or has no `params.message`.
- `_project_injecting_receive(original_receive, project_name: str)`: wrap an ASGI `receive` so the downstream app gets the request body with the project injected.
- Notable constants/configuration names: `_PRINTER`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Agent Zero wraps `FastA2A` with `AgentZeroFastA2A` so the generated agent card sets `capabilities.streaming` to `true` by default.
- Auth contract (`DynamicA2AProxy.__call__`): a `/t-{token}/` path segment (after an optional `/a2a` prefix) is checked against the `mcp_server_token` setting; without it, an `Authorization: Bearer <token>` header or an `X-API-KEY` header / `api_key` query value is accepted. All comparisons use `server_auth.token_matches`; a failure is `401 Unauthorized`. The token is never logged.
- Project-routing contract: the project comes from a `/p-{project}/` segment after the token, or from the `X-A0-Project` header, via `server_auth.resolve_project`; an invalid value, or URL and header that differ, is answered with the `RequestRejected` status (`400`) and detail as plain text, before FastA2A sees the request.
- When a project is resolved, the proxy rewrites the JSON-RPC body so `params.message.metadata.project` names it (the standard A2A metadata pattern); `AgentZeroWorker.run_task` reads it from `message.metadata` and calls `projects.activate_project` on the new context. The rewrite buffers every `http.request` chunk until `more_body` is false and hands the app the whole rewritten body exactly once, as a single `http.request` event; later `receive` calls pass through. A non-JSON body is forwarded unchanged (joined into that single event). Without a project the body is not buffered or touched.
- Observed side-effect areas: filesystem writes, filesystem deletion, settings/state persistence, secret handling, scheduler state.
- Imported dependency areas include: `agent`, `asyncio`, `atexit`, `contextlib`, `helpers`, `helpers.persist_chat`, `helpers.print_style`, `helpers.server_auth`, `initialize`, `json`, `starlette.requests`, `starlette.responses`, `threading`, `typing`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `PrintStyle`, `DynamicA2AProxy.get_instance`, `json.loads`, `json.dumps`, `super.__init__`, `super._agent_card_endpoint`, `join`, `UserMessage`, `threading.Lock`, `atexit.register`, `self._configure`, `settings.get_settings`, `path.startswith`, `self._convert_message`, `initialize_agent`, `AgentContext`, `context.log.log`, `context.communicate`, `context.reset`, `AgentContext.remove`, `remove_chat`, `self.storage.update_task`, `self._register_shutdown`, `server_auth.token_matches`, `server_auth.get_bearer_token`, `server_auth.resolve_project`, `projects.activate_project`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests:
  - `tests/test_fasta2a_server.py`
  - `tests/test_mcp_a2a_header_auth.py`

## Child DOX Index

No child DOX files.
