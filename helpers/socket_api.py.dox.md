# socket_api.py DOX

## Purpose and Ownership

- Own the in-process Unix-domain JSON socket server and file-based dispatch. Handler ownership is in `socket/AGENTS.md` and plugin DOX.
- `SocketHandler(app, thread_lock).process(input)` receives all request arguments and returns a JSON-safe dictionary.
- `SocketError(code, message, details=...)` exposes deliberate, safe errors. Unexpected failures are logged locally and returned as `INTERNAL_ERROR` without exception text.
- `SocketServer` owns `start`, `close`, `dispatch` and active request tasks. `socket_lifespan` integrates it with the WebUI ASGI lifespan on POSIX systems.
- `get_socket_path`, `encode_message`, `decode_message`, limits and error envelopes are shared with the dependency-light CLI.

## Contracts and Side Effects

- One UTF-8 newline-delimited JSON request and response per connection. Request: `{"command":"ping","args":{}}`; success: `{"ok":true,"result":{...}}`; failure: `{"ok":false,"error":{"code":"...","message":"..."}}`.
- Messages, including the newline, default to 64 MiB (`A0_SOCKET_MAX_MESSAGE_BYTES`, minimum 1024). Receive/write deadlines default to 60 seconds each (`A0_SOCKET_IO_TIMEOUT`). Execution has no default deadline (`A0_SOCKET_REQUEST_TIMEOUT=0`); a positive value opts into a server deadline. Limits are read at process start and invalid values fail explicitly. Successful output is serialized once. NaN/Infinity, malformed input, non-object args and non-dictionary results are rejected.
- Resolve core `socket/<command>.py`, installed plugin `<plugin>/socket/<handler>.py` for `plugins/<name>/<handler>`, then `usr/socket/<command>.py`. Reuse `plugins.find_plugin_dir` and `modules.load_classes_from_file`; no route cache. Reject traversal and resolved paths outside each handler root before importing.
- Default path is framework-root `tmp/socket/a0.sock`; `A0_SOCKET_PATH` overrides it. The parent must be a real directory owned by the server user with no group/other permissions. The socket is mode 0600; no TCP listener or browser authentication is involved.
- A held advisory lock serializes starts. Refuse files, symlinks, another user's socket or an active listener. Only reclaim a same-owner, connection-refused socket. Cleanup removes only the inode created by this server; the lock file remains for safe reuse.
- Shutdown aborts client transports and cancels active request tasks before waiting for the listener. Write failures abort buffered output; graceful client closure has a five-second deadline. Handlers must cooperate with cancellation. Timeouts/disconnects do not roll back completed side effects; callers must not automatically retry mutations.
- Socket access is an instance-level local trust boundary, not an agent identity. Explicit JSON administration adapters live in `socket_handlers.py`; agent-tool handlers must separately establish identity and action policy. No caller-selected arbitrary tool/HTTP forwarding is provided.
- Keep imports needed for handler discovery lazy so the CLI needs only the standard library. `socket/` must remain a non-package to avoid shadowing the standard library.

## Verification

- `python -m pytest tests/test_socket_api.py tests/test_socket_handlers.py`; dependency-free alternative: `python3 -m unittest discover -s tests -p 'test_socket_*.py'`.
- Tests use real Unix sockets and subprocess clients, actual framework class loading against temporary roots, and isolated file/plugin resolver dependencies.
