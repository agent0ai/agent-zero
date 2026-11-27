# Local socket API

Agent Zero starts a Unix-domain socket inside its WebUI process on Linux/POSIX.
It provides local JSON request/response calls without HTTP or a TCP port. The development and plugin-management skills use this transport for local
administration. Native agent tools remain unchanged. Startup and update health
checks continue to use HTTP `/api/health`; socket `ping` checks only this listener.

## Calling a handler

From the Agent Zero root, using its Python environment:

```bash
python -m helpers.socket_cli ping
# {"ok": true, "result": {"message": "pong"}}
```

The default socket is `tmp/socket/a0.sock` under the framework root. Set
`A0_SOCKET_PATH` to an absolute path before starting A0 to change it. The client
uses the same variable, or an explicit `--socket /path/to/a0.sock` argument.
The parent directory must be private to the server user (mode 0700); the server
creates it if missing and creates the socket with mode 0600.

Commands follow handler filenames, without `.py`:

| Command | Handler location |
| --- | --- |
| `ping` | `socket/ping.py` |
| `v1/example` | `socket/v1/example.py` |
| `plugins/example/do_work` | `plugins/example/socket/do_work.py` or the installed custom plugin equivalent |
| `custom_handler` | `usr/socket/custom_handler.py`, when no core handler matches |

Discovery follows HTTP API precedence: core, plugin, then user fallback. Plugin
directories resolve through the existing plugin finder, including custom
plugins under `usr/plugins/`. This is installed-handler discovery, not a new
activation policy; handlers enforce feature-specific access requirements.

## Available administration commands

| Commands | Operations |
| --- | --- |
| `projects`, `agents`, `agent_profile_set` | Project administration and profile selection |
| `chat_create`, `chat_reset`, `chat_remove`, `chat_export`, `history_get`, `poll` | Chat lifecycle and state |
| `message`, `message_async`, `pause`, `stop`, `message_queue_add`, `message_queue_remove`, `message_queue_send` | Start/control work and queued follow-ups |
| `plugins_list`, `plugins` | Installed plugins, configuration, activation and removal |
| `notification_create`, `notifications_history`, `notifications_mark_read` | Notifications |
| `plugins/_scheduler/scheduler_task_create`, `scheduler_task_update`, `scheduler_task_delete`, `scheduler_task_run`, `scheduler_tasks_list` | Saved tasks (each command uses the `plugins/_scheduler/` prefix) |
| `plugins/_agent_editor/agent_editor` | Profile editor planning/apply |
| `plugins/_plugin_installer/plugin_install` | Index fetch, compatibility check, Git install/update, local ZIP install |
| `plugins/_plugin_scan/plugin_scan_run` | Synchronous security scan |

These files select their corresponding API operations explicitly. Arguments
and successful results use the existing JSON shapes. Chat controls require an
existing `context` (profile selection uses `context_id`, export uses `ctxid`).
`poll` with no context lists instance state. Create a chat before sending work.

For local ZIP installation, use `{"action":"install_zip","zip_path":"/absolute/path/plugin.zip"}`.
The installer copies the file through the existing upload helper, retaining the
source archive and all archive validation/hooks. HTTP multipart uploads still
work. Files must be visible in the server's filesystem namespace.

See [the operation reference](../../skills/a0-development/references/operate-agent-zero.md)
and [plugin lifecycle reference](../../skills/a0-manage-plugin/references/lifecycle.md)
for payloads, scope and verification.

## Writing a handler

For example, place this in a plugin's `socket/do_work.py`, alongside its `api/`
directory:

```python
from helpers.socket_api import SocketError, SocketHandler


class DoWork(SocketHandler):
    async def process(self, input: dict) -> dict:
        text = input.get("text")
        if not isinstance(text, str) or not text:
            raise SocketError("INVALID_ARGUMENT", "text is required")
        return {"message": text, "length": len(text)}
```

The command would be:

```bash
python -m helpers.socket_cli plugins/example/do_work '{"text":"hello"}'
printf '%s' '{"text":"hello"}' | python -m helpers.socket_cli plugins/example/do_work -
```

All arguments arrive unchanged in `input`, including nested objects and arrays.
The handler receives the existing Flask app and shared lock as `self.app` and
`self.thread_lock`; no Flask request/session context is synthesized. Use shared
feature helpers for operations. Keep blocking work off the event loop and
cooperate with cancellation.

Do **not** add `socket/__init__.py` to the framework root: that would shadow
Python's standard-library `socket` module. Handlers are loaded by file path.

## Wire format and failures

Each connection carries one UTF-8 JSON line in each direction:

```json
{"command":"plugins/example/do_work","args":{"text":"hello"}}
{"ok":true,"result":{"message":"hello","length":5}}
```

Newlines inside strings are JSON-escaped. The server closes after its response.
Limits are configurable at process start:

| Setting | Default | Meaning |
| --- | --- | --- |
| `A0_SOCKET_MAX_MESSAGE_BYTES` | 67108864 (64 MiB) | Request/response ceiling including newline; minimum 1024 |
| `A0_SOCKET_IO_TIMEOUT` | 60 seconds | Request receive and response write deadlines; client connect/send deadline |
| `A0_SOCKET_REQUEST_TIMEOUT` | 0 | No operation deadline; positive seconds opt into a server deadline |

The client also accepts `--timeout SECONDS` or `call(..., timeout=seconds)` for a
response deadline; by default it waits for long operations to finish. Set the
same message ceiling in client and server environments. Invalid limits fail
explicitly. Requests run concurrently; the shared JSON administration adapters
use worker threads so blocking work does not block the transport event loop.

This protocol buffers JSON. It does not stream binary uploads or partial
results; HTTP's large streaming file transfers remain available. Increasing
the JSON ceiling increases peak memory per simultaneous request.

An expected failure looks like:

```json
{"ok":false,"error":{"code":"INVALID_ARGUMENT","message":"text is required"}}
```

Other transport codes include `INVALID_REQUEST`, `INVALID_COMMAND`, `NOT_FOUND`,
`REQUEST_TOO_LARGE`, `RESPONSE_TOO_LARGE`, `TIMEOUT` and `INTERNAL_ERROR`.
Shared API failures use `HTTP_<status>` or `OPERATION_FAILED`; the latter keeps
the original failure body in `error.details`, including plugin-update conflict
fields. Unexpected exception details remain in server logs. Handler results must be
JSON-safe dictionaries; NaN/Infinity and arbitrary Python objects are rejected.

The CLI prints JSON on stdout, diagnostics on stderr, and exits 0 for success
or 1 for a failed request. Invocation syntax errors exit 2. A timeout or lost
connection does not prove an operation had no effect; the client never retries
automatically.

## Access and lifecycle

Socket permissions authorize access to the instance. Processes running as the
same Linux user, and privileged root processes, share that access. This does
not authenticate a particular agent, chat or project. The supplied administration handlers require explicit existing chat targets
where needed and have instance-level authority. Agent-tool handlers would need
a separate trusted identity and action-policy boundary; caller-supplied chat
IDs do not provide that. There is no arbitrary tool or HTTP-endpoint dispatcher.

The listener starts and stops with the ASGI lifespan. Startup refuses an active
listener or a conflicting non-socket path, and reclaims only an owned stale
socket. A bind or permission failure fails server startup visibly. Graceful
shutdown cancels pending handlers and removes the owned socket. Synchronous
work already running in a worker thread cannot be forcibly interrupted; it
may complete after cancellation or a lost response. The small lock
file remains for the next start.

The client must run where the socket is accessible. Nothing is automatically
mounted into sandboxes or forwarded to connected hosts. Non-POSIX WebUI runtimes
skip this listener.

## Verification

```bash
python -m pytest tests/test_socket_api.py tests/test_socket_handlers.py
# Or, without pytest/application dependencies:
python3 -m unittest discover -s tests -p 'test_socket_*.py'
```

The focused suite uses temporary handlers, real sockets and CLI subprocesses;
adapter tests exercise shared operations with isolated dependencies. They do
not read private chats, call providers or install plugins.
