# socket_handlers.py DOX

## Purpose and Ownership

- `JsonApiHandler` adapts explicitly selected, request-independent JSON administration operations to `SocketHandler`. Each core/plugin socket file fixes `api_module` and `api_class`; callers cannot name an arbitrary HTTP endpoint.
- `require_context` validates a supplied existing chat ID. `context_field` enables this guard for chat controls; projects require a target for activation/deactivation. This is instance administration, not an authenticated agent identity or tool-policy dispatcher.
- `json_result` preserves dictionary results and converts HTTP error responses and body-level `error`, `ok: false`, or `success: false` into `SocketError`. An explicit success may include advisory error data (the compatibility check); it remains a successful operation unless another explicit flag is false. Body-level failures retain their original payload in `error.details`, including update conflict fields. Streaming responses require a dedicated handler.

## Contracts and Side Effects

- Reuse operation validation, hooks and persistence by invoking the fixed API handler's `process(input, None)`. Arguments are passed unchanged. No HTTP request, session or CSRF context is synthesized; browser HTTP protections remain in the HTTP dispatcher.
- `_in_worker` runs each operation coroutine on a worker thread with its own event loop, similar to Flask request execution. Blocking imports, Git/filesystem work and lifecycle hooks do not block the transport loop. The default asyncio executor bounds worker concurrency.
- Cancellation propagates to the worker coroutine, including cancellation before worker startup. Python cannot interrupt synchronous work already executing in a thread; it may finish a mutation after a timeout/disconnect. No retry or rollback is implied.
- Exceptions not deliberately converted by the operation or adapter remain sanitized by the socket transport. These privileged administration operations expose the same result/error data as the existing APIs; do not dump secrets from them into logs or chat.

## Verification

- `python -m unittest discover -s tests -p 'test_socket_*.py'` or the corresponding pytest files.
- Adapter tests load actual message/installer/pause implementations with isolated dependencies and state. Full WebUI/provider/lifecycle integration requires the installed framework runtime.
