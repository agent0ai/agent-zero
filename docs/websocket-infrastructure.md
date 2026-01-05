# WebSocket Infrastructure Guide

**Audience**: Backend and frontend developers building real-time features on Agent Zero
**Updated**: 2026-01-02
**Related Specs**: `specs/003-websocket-event-handlers/*`

This guide consolidates everything you need to design, implement, and troubleshoot Agent Zero WebSocket flows. It complements the feature specification by describing day-to-day developer tasks, showing how backend handlers and frontend clients cooperate, and documenting practical patterns for producers and consumers on both sides of the connection.

---

## Table of Contents

1. [Architecture at a Glance](#architecture-at-a-glance)
2. [Terminology & Metadata](#terminology--metadata)
3. [Connection Lifecycle](#connection-lifecycle)
4. [Backend Cookbook (Handlers & Manager)](#backend-cookbook-handlers--manager)
5. [Frontend Cookbook (websocket.js)](#frontend-cookbook-websocketjs)
6. [Producer & Consumer Patterns](#producer--consumer-patterns)
7. [Metadata Flow & Envelopes](#metadata-flow--envelopes)
8. [Diagnostics, Harness & Logging](#diagnostics-harness--logging)
9. [Best Practices Checklist](#best-practices-checklist)
10. [Quick Reference Tables](#quick-reference-tables)
11. [Further Reading](#further-reading)

---

## Architecture at a Glance

- **Runtime (`run_ui.py`)** – boots `python-socketio.AsyncServer` inside an ASGI stack served by Uvicorn. Flask routes are mounted via `uvicorn.middleware.wsgi.WSGIMiddleware`, and Flask + Socket.IO share the same process so session cookies and CSRF semantics stay aligned.
- **Singleton handlers** – every `WebSocketHandler` subclass exposes `get_instance()` and is registered exactly once. Direct instantiation raises `SingletonInstantiationError`, keeping shared state and lifecycle hooks deterministic.
- **Dispatcher offload** – handler entrypoints (`process_event`, `on_connect`, `on_disconnect`) run in a background worker loop (via `DeferredTask`) so blocking handlers cannot stall the Socket.IO transport. Socket.IO emits/disconnects are marshalled back to the dispatcher loop. Diagnostic timing and payload summaries are only built when Event Console watchers are subscribed (development mode).
- **`python/helpers/websocket_manager.py`** – orchestrates routing, buffering, aggregation, metadata envelopes, and session tracking. Think of it as the “switchboard” for every WebSocket event.
- **`python/helpers/websocket.py`** – base class for application handlers. Provides lifecycle hooks, helper methods (`emit_to`, `broadcast`, `request`, `request_all`) and identifier metadata.
- **`webui/js/websocket.js`** – frontend singleton exposing a minimal client API (`emit`, `request`, `on`, `off`) with lazy connection management and development-only logging (no client-side `broadcast()` or `requestAll()` helpers).
- **Developer Harness (`webui/components/settings/developer/websocket-test-store.js`)** – manual and automatic validation suite for emit/request flows, timeout behaviour (including the default unlimited wait), correlation ID propagation, envelope metadata, subscription persistence across reconnect, and development-mode diagnostics.
- **Specs & Contracts** – canonical definitions live under `specs/003-websocket-event-handlers/`. This guide references those documents but focuses on applied usage.

---

## Terminology & Metadata

| Term | Where it Appears | Meaning |
|------|------------------|---------|
| `sid` | Socket.IO | Connection identifier for a Socket.IO namespace connection. With only the root namespace (`/`), each tab has one `sid`. When connecting to multiple namespaces, a tab has one `sid` per namespace. Treat connection identity as `(namespace, sid)`. |
| `handlerId` | Manager Envelope | Fully-qualified Python class name (e.g., `python.websocket_handlers.notifications.NotificationHandler`). Used for result aggregation and logging. |
| `eventId` | Manager Envelope | UUIDv4 generated for every server→client delivery. Unique per emission. Useful when correlating broadcast fan-out or diagnosing duplicates. |
| `correlationId` | Bidirectional flows | Thread that ties together request, response, and any follow-up events. Client may supply one; otherwise the manager generates and echoes it everywhere. |
| `data` | Envelope payload | Application payload you define. Always a JSON-serialisable object. |
| `user_to_sids` / `sid_to_user` | Manager session tracking | Single-user map today (`allUsers` bucket). Future-proof for multi-tenant routing but already handy when you need all active SIDs. |
| Buffer | Manager | Up to 100 fire-and-forget events stored per temporarily disconnected SID (expires after 1 hour). Request/response events never buffer—clients receive standardised errors instead. |

Useful mental model: **client ↔ manager ↔ handler**. The manager normalises metadata and enforces routing; handlers focus on business logic; the frontend uses the same identifiers, so logs are easy to stitch.

---

## Connection Lifecycle

1. **Lazy Connect** – `/js/websocket.js` connects only when a consumer uses the client API (e.g., `emit`, `request`, `on`). Consumers may still explicitly `await websocket.connect()` to block UI until the socket is ready.
2. **Handshake** – Socket.IO connects using the existing Flask session cookie and a CSRF token provided via the Socket.IO `auth` payload (`csrf_token`). The token is obtained from `GET /csrf_token` (see `/js/api.js#getCsrfToken()`), which also sets the runtime-scoped cookie `csrf_token_{runtime_id}`. The server validates an **Origin allowlist** (RFC 6455 / OWASP CSWSH baseline) and then checks handler requirements (`requires_auth`, `requires_csrf`) before accepting.
3. **Lifecycle Hooks** – After acceptance, `WebSocketHandler.on_connect(sid)` fires for every registered handler. Use it for initial emits, state bookkeeping, or session tracking.
4. **Normal Operation** – Client emits events. Manager routes them to the appropriate handlers, gathers results, and wraps outbound deliveries in the mandatory envelope.
5. **Disconnection & Buffering** – If a tab goes away without a graceful disconnect, fire-and-forget events accumulate (max 100). On reconnect, the manager flushes the buffer via `emit_to`. Request flows respond with explicit `CONNECTION_NOT_FOUND` errors.
6. **Reconnection Attempts** – Socket.IO handles reconnect attempts; the manager continues to buffer fire-and-forget events (up to 1 hour) for temporarily disconnected SIDs and flushes them on reconnect.

### State Sync (Replacing `/poll`)

Agent Zero can also push poll-shaped state snapshots over the WebSocket bus, replacing the legacy 4Hz `/poll` loop while preserving the existing UI update contract.

- **Handshake**: the frontend sync store (`/components/sync/sync-store.js`) calls `websocket.request("state_request", { context, log_from, notifications_from, timezone })` to establish per-tab cursors and a `seq_base`.
- **Push**: the server emits `state_push` events containing `{ runtime_epoch, seq, snapshot }`, where `snapshot` is exactly the `/poll` payload shape built by `python/helpers/snapshot.py`.
- **Coalescing**: the backend `StateMonitor` coalesces dirties per SID (25ms window) so streaming updates stay smooth without unbounded trailing-edge debounce.
- **Degraded fallback**: if the WebSocket handshake/push path is unhealthy, the UI enters `DEGRADED` and uses `/poll` as a fallback; while degraded, push snapshots are ignored to avoid racey double-writes.

### Thinking in Roles

- **Client** (frontend) is the page that imports `/js/websocket.js`. It acts as both a **producer** (calling `emit`, `request`) and a **consumer** (subscribing with `on`).
- **Manager** (`WebSocketManager`) sits server-side and routes everything. It resolves correlation IDs, wraps envelopes, and fans out results.
- **Handler** (`WebSocketHandler`) executes the application logic. Each handler may emit additional events back to the client or initiate its own requests to connected SIDs.

### Flow Overview (by Operation)

```
Client emit() ───▶ Manager route_event() ───▶ Handler.process_event()
   │                │                           └──(fire-and-forget, no ack)
   └── throws if    └── validates payload + routes by namespace/event type
       not connected    updates last_activity

Client request() ─▶ Manager route_event() ─▶ Handlers (async gather)
   │                │                        └── per-handler dict/None
   │                │
   │                └── builds {correlationId, results[]}
   └── Promise resolves with aggregated results (timeouts become error items)

Server emit_to() ──▶ Manager.emit_to() ──▶ Socket.IO delivery/buffer
   │                 │                         └── envelope {handlerId,…}
   └── raises ConnectionNotFoundError for unknown sid (never seen)

Server broadcast() ─▶ Manager.broadcast()
   │                     └── iterates active sids (respecting exclude_sids)
   │                           └── delegates to `Manager.emit_to()` → `socketio.emit(..., to=sid)`
   └── fire-and-forget (no ack)

Server request() ─▶ Manager.request_for_sid() ─▶ route_event()
   │                  │                            └── per-handler responses
   └── Await aggregated {correlationId, results[]}

Server request_all() ─▶ Manager.route_event_all() ─▶ route_event per sid
        │                     │                         └── per-handler results
        └── Await list[{sid, correlationId, results[]}]
```

These diagrams highlight the “who calls what” surface while the detailed semantics (envelopes, buffering, timeouts) remain consistent with the tables later in this guide.

### End-to-End Examples

1. **Client request ➜ multiple handlers**

   1. Frontend calls `websocket.request("refresh_metrics", payload)`.
   2. Manager routes to each handler registered for that event type and awaits `asyncio.gather`.
   3. Each handler returns a dict (or raises); the manager wraps them in `results[]` and resolves the Promise with `{ correlationId, results }`.
   4. The caller inspects per-handler data or errors, filtering by `handlerId` as needed.

2. **Server broadcast with buffered replay**

   1. Handler invokes `self.broadcast("notification_broadcast", data, exclude_sids=sid)`.
   2. Manager iterates active connections. For connected SIDs it emits immediately with the mandatory envelope. For temporarily disconnected SIDs it enqueues into the per-SID buffer (up to 100 events).
   3. When a buffered SID reconnects, `_flush_buffer()` replays the queued envelopes preserving `handlerId`, `eventId`, `correlationId`, and `ts`.

3. **Server request_all ➜ client-side confirmations**

   1. Handler issues `await self.request_all("confirm_close", { contextId }, timeout_ms=5000)`.
   2. Manager fans out to every active SID, allowing `exclude_handlers` when provided.
   3. Each subscribed client runs its `websocket.on("confirm_close", …)` callback and returns data through the Socket.IO acknowledgement.
   4. The handler receives `[{ sid, correlationId, results[] }]`, inspects each response, and proceeds accordingly.

These expanded flows complement the operation matrix later in the guide, ensuring every combination (client/server × emit/request and server request_all) is covered explicitly.

---

## Backend Cookbook (Handlers & Manager)

### 1. Handler Discovery & Setup

Handlers are discovered deterministically from `python/websocket_handlers/`:

- **File entry**: `python/websocket_handlers/state_sync_handler.py` → namespace `/state_sync`
- **Folder entry**: `python/websocket_handlers/orders/` or `python/websocket_handlers/orders_handler/` → namespace `/orders` (loads `*.py` one level deep; ignores `__init__.py` and deeper nesting)
- **Reserved root**: `python/websocket_handlers/_default.py` → namespace `/` (diagnostics-only by default)

Create handler modules under the appropriate namespace entry and inherit from `WebSocketHandler`.

```python
from python.helpers.websocket import WebSocketHandler

class DashboardHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["dashboard_refresh", "dashboard_push"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str) -> dict | None:
        if event_type == "dashboard_refresh":
            stats = await self._load_stats(data.get("scope", "all"))
            return {"ok": True, "stats": stats}

        if event_type == "dashboard_push":
            await self.broadcast(
                "dashboard_update",
                {"stats": data.get("stats", {}), "source": sid},
                exclude_sids=sid,
            )
        return None
```

Handlers are auto-loaded on startup; duplicate event declarations produce warnings but are supported. Use `validate_event_types` to ensure names follow lowercase snake_case and avoid Socket.IO reserved events.

### 2. Consuming Client Events (Server as Consumer)

- Implement `process_event` and return either `None` (fire-and-forget) or a dict that becomes the handler’s contribution in `results[]`.
- Use dependency injection (async functions, database calls, etc.) but keep event loop friendly—no blocking calls.
- Validate input vigorously and return structured errors as needed.

```python
async def process_event(self, event_type: str, data: dict, sid: str) -> dict | None:
    if "query" not in data:
        return {"ok": False, "error": {"code": "VALIDATION", "error": "Missing query"}}

    rows = await self.search_backend(data["query"], limit=data.get("limit", 25))
    return {"ok": True, "data": rows, "count": len(rows)}
```

### 3. Producing Server Events (Server as Producer)

Four helper methods mirror the frontend API. The table below summarises them (full table in [Quick Reference](#quick-reference-tables)).

| Method | Target | Ack | Filters | Typical Use |
|--------|--------|-----|---------|--------------|
| `emit_to(sid, event, data, correlation_id=None)` | Single SID | No | None | Push job progress, reply to a request without using Socket.IO ack (already produced). |
| `broadcast(event, data, exclude_sids=None, correlation_id=None)` | All SIDs | No | `exclude_sids` only | Fan-out notifications, multi-tab sync while skipping the caller. |
| `request(sid, event, data, timeout_ms=0)` | Single SID | Yes (`results[]`) | None | Ask the client to run local logic (e.g., UI confirmation) and gather per-handler results. |
| `request_all(event, data, timeout_ms=0)` | All SIDs | Yes (`[{sid, results[]}]`) | None | Fan-out to every tab, e.g., “refresh your panel” or “confirm unsaved changes”. |

Each helper automatically injects `handlerId`, obeys metadata envelopes, enforces routing rules, and handles timeouts:

```python
aggregated = await self.request_all(
    "workspace_ping",
    {"payload": {"reason": "health_check"}},
    timeout_ms=2_000,
)

for entry in aggregated:
    self.log.info("sid %s replied: %s", entry["sid"], entry["results"])
```

Timeouts convert into `{ "ok": False, "error": {"code": "TIMEOUT", ...} }`; they do **not** raise.

### 4. Multi-Handler Aggregation

- When multiple handlers subscribe to the same event, the manager invokes them concurrently with `asyncio.gather`. Aggregated results preserve registration order. Use correlation IDs to map responses to original triggers.
- Client-side handler include/exclude filters are intentionally not supported. Consumers filter `results[]` by `handlerId` when needed.

```python
if not results:
    return {
        "handlerId": self.identifier,
        "ok": False,
        "error": {"code": "NO_HANDLERS", "error": "No handler registered for this event type"},
    }
```

### 5. Session Tracking Helpers

`WebSocketManager` maintains lightweight mappings that you can use from handlers:

```python
all_sids = self.manager.get_sids_for_user()      # today: every active sid
maybe_user = self.manager.get_user_for_sid(sid)  # currently None or "single_user"

if updated_payload:
    await asyncio.gather(
        *[
            self.emit_to(other_sid, "dashboard_update", updated_payload)
            for other_sid in all_sids if other_sid != sid
        ]
    )
```

These helpers are future-proof for multi-tenant evolution and already handy to broadcast to every tab except the caller.

**Future Multitenancy Mechanics**
- **Registration**: When multi-user support ships, `handle_connect` will resolve the authenticated user identifier (e.g., from Flask session). `register()` will stash that identifier alongside the SID and place it into `user_to_sids[user_id]` while still populating the `allUsers` bucket for backward compatibility.
- **Lookups**: `get_sids_for_user(user_id)` will return the tenant-specific SID set. Omitting the argument (or passing `None`) keeps today’s behaviour and yields the full `allUsers` list. `get_user_for_sid(sid)` will expose whichever identifier was recorded at registration.
- **Utility**: These primitives unlock future features such as sending workspace notifications to every tab owned by the same account, ejecting all sessions for a suspended user, or correlating request/response traffic per tenant without rewriting handlers.
- **Migration Story**: Existing handler code that loops over `get_sids_for_user()` automatically gains tenant-scoped behaviour once callers pass a `user_id`. Tests will exercise both single-user (default) and multi-tenant branches to guarantee compatibility.

---

## Frontend Cookbook (`websocket.js`)

### 1. Connecting

```javascript
import { getNamespacedClient } from "/js/websocket.js";

const websocket = getNamespacedClient("/"); // reserved root (diagnostics-only by default)

// Optional: await the handshake if you need to block UI until the socket is ready
await websocket.connect();

// Runtime metadata is exposed globally for Alpine stores / harness
console.log(window.runtimeInfo.id, window.runtimeInfo.isDevelopment);
```

- The module connects lazily when a consumer uses the client API (e.g., `emit`, `request`, `on`). Components may still explicitly `await websocket.connect()` to block rendering on readiness or re-run diagnostics.
- The server enforces an Origin allowlist during the Socket.IO connect handshake (baseline CSWSH mitigation). The browser session cookie remains the authentication mechanism, and CSRF is validated via the Socket.IO `auth` payload (`csrf_token`) plus the runtime-scoped CSRF cookie and session value.
- Socket.IO handles reconnection attempts automatically.

### Namespaces (end-state)

- The root namespace (`/`) is reserved and intentionally unhandled by default for application events. Feature code should connect to an explicit namespace (for example `/state_sync`).
- The frontend exposes `createNamespacedClient(namespace)` and `getNamespacedClient(namespace)` (one client instance per namespace per tab). Namespaced clients expose the same minimal API: `emit`, `request`, `on`, `off`.
- Unknown namespaces are rejected deterministically during the Socket.IO connect handshake with a `connect_error` payload:
  - `err.message === "UNKNOWN_NAMESPACE"`
  - `err.data === { code: "UNKNOWN_NAMESPACE", namespace: "/requested" }`

### 2. Client Operations

- **Producers (client → server)** use `emit` and `request`. Payloads must be objects; primitive payloads throw.
- **Consumers (server → client)** register callbacks with `on(eventType, callback)` and remove them with `off()`.

Example (producer):

```javascript
await websocket.request("hello_request", { name: this.name }, {
  timeoutMs: 1500,
  correlationId: `greet-${crypto.randomUUID()}`,
});
```

Example (consumer):

```javascript
websocket.on("dashboard_update", (envelope) => {
  const { handlerId, correlationId, ts, data } = envelope;
  this.debugLog({ handlerId, correlationId, ts });
  this.rows = data.rows;
});

// Later, during cleanup
websocket.off("dashboard_update");
```

### 3. Envelope Awareness

Subscribers always receive:

```javascript
interface ServerDeliveryEnvelope {
  handlerId: string;
  eventId: string;
  correlationId: string;
  ts: string;       // ISO8601 UTC with millisecond precision
  data: object;
}
```

Even if existing components only look at `data`, you should record `handlerId` and `correlationId` when building new features—doing so simplifies debugging multi-tab flows.

### 4. Development-Only Logging

`websocket.debugLog()` writes to the console only when `runtimeInfo.isDevelopment` is true. Use it liberally when diagnosing event flows without polluting production logs.

```javascript
websocket.debugLog("request", { correlationId: payload.correlationId, timeoutMs });
```

### 5. Helper Utilities

`webui/js/websocket.js` exports helper utilities alongside the `websocket` singleton so correlation metadata and envelopes stay consistent:

- `createCorrelationId(prefix?: string)` returns a UUID-based identifier, optionally prefixed (e.g. `createCorrelationId('hello') → hello-1234…`). Use it when chaining UI actions to backend logs.
- `validateServerEnvelope(envelope)` guarantees subscribers receive the canonical `{ handlerId, eventId, correlationId, ts, data }` shape; throw if the payload is malformed.

Example:

```javascript
import { getNamespacedClient, createCorrelationId, validateServerEnvelope } from '/js/websocket.js';

const websocket = getNamespacedClient('/state_sync');

const { results } = await websocket.request(
  'hello_request',
  { name: this.name },
  { correlationId: createCorrelationId('hello') },
);

websocket.on('dashboard_update', (envelope) => {
  const validated = validateServerEnvelope(envelope);
  this.rows = validated.data.rows;
});
```

### 6. Error Handling

- Producer methods call `websocket.connect()` internally, so they wait for the handshake automatically. They only surface `Error("Not connected")` if the handshake ultimately fails (for example, the user is logged out or the server is down).
- `request()` acknowledgement timeouts reject with `Error("Request timeout")`. Server-side fan-out timeouts (for example `request_all`) are represented as `results[]` entries with `error.code = "TIMEOUT"` (no Promise rejection).
- For large payloads, the client throws before sending and the server rejects frames above the 50 MiB cap (`max_http_buffer_size` on the Socket.IO engine).

### 7. Startup Broadcast

- When **Broadcast server restart event** is enabled in Developer settings (on by default) the backend emits a fire-and-forget `server_restart` envelope the first time each connection is established after a process restart. The payload includes `runtimeId` and an ISO8601 timestamp so clients can reconcile cached state.
- Disable the toggle if your deployment pipeline already publishes restart notifications.

---

## Frontend Error Handling (Using the Registry)

Client code should treat `RequestResultItem.error.code` as one of the documented values and branch behavior accordingly. Keep UI decisions localized and reusable.

Recommended patterns
- Centralize mapping from `WsErrorCode` → user-facing message and remediation hint.
- Always surface hard errors (timeouts); gate debug details by dev flag.

Example – request()
```javascript
import { getNamespacedClient } from '/js/websocket.js'

const websocket = getNamespacedClient('/state_sync')

function renderError(code, message) {
  // Map codes to UI copy; keep messages concise
  switch (code) {
    case 'NO_HANDLERS': return `No handler for this action (${message})`
    case 'TIMEOUT': return `Request timed out; try again or increase timeout`
    case 'CONNECTION_NOT_FOUND': return `Target connection unavailable; retry after reconnect`
    default: return message || 'Unexpected error'
  }
}

const res = await websocket.request('example_event', { foo: 'bar' }, { timeoutMs: 1500 })
for (const item of res.results) {
  if (item.ok) {
    // use item.data
  } else {
    const msg = renderError(item.error?.code, item.error?.error)
    // show toast/log based on dev flag
    console.error('[ws]', msg)
  }
}
```

Subscriptions – envelope handler
```javascript
import { getNamespacedClient } from '/js/websocket.js'

const websocket = getNamespacedClient('/state_sync')

websocket.on('example_broadcast', ({ data, handlerId, eventId, correlationId }) => {
  // handle data; errors should not typically arrive via broadcast
  // correlationId can link UI actions to backend logs
})
```

See also
- Error Codes Registry (above) for the authoritative code list
- Contracts: `frontend-api.md` for method signatures and response shapes

---

## Producer & Consumer Patterns

### Pattern A – Fire-and-Forget Notification (Server Producer → Client Consumers)

Backend:

```python
await self.broadcast(
    "notification_broadcast",
    {
        "message": data["message"],
        "level": data.get("level", "info"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    },
    exclude_sids=sid,
    correlation_id=data.get("correlationId"),
)
```

Frontend:

```javascript
websocket.on("notification_broadcast", ({ data, correlationId, ts }) => {
  notifications.unshift({ ...data, correlationId, ts });
});
```

### Pattern B – Request/Response With Multi-Handler Aggregation (Client Producer → Server Consumers)

Client:

```javascript
const { correlationId, results } = await websocket.request(
  "refresh_metrics",
  { duration: "1h" },
  { timeoutMs: 2_000 }
);

results.forEach(({ handlerId, ok, data, error }) => {
  if (ok) renderMetrics(handlerId, data);
  else console.warn(handlerId, error);
});
```

Server (two handlers listening to the same event):

```python
class TaskMetrics(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["refresh_metrics"]

    async def process_event(self, event_type: str, data: dict, sid: str) -> dict | None:
        stats = await self._load_task_metrics(data["duration"])
        return {"metrics": stats}

class HostMetrics(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["refresh_metrics"]

    async def process_event(self, event_type: str, data: dict, sid: str) -> dict | None:
        return {"metrics": await self._load_host_metrics(data["duration"])}
```

### Pattern C – Fan-Out `request_all` (Server Producer → Many Client Consumers)

Backend (server producer asking every tab to confirm a destructive operation):

```python
confirmations = await self.request_all(
    "confirm_close_tab",
    {"contextId": context_id},
    timeout_ms=5_000,
)

for entry in confirmations:
    self.log.info("%s responded: %s", entry["sid"], entry["results"])
```

Frontend consumer matching the envelope:

```javascript
websocket.on("confirm_close_tab", async ({ data, correlationId }) => {
  const accepted = await showModalAndAwaitUser(data.contextId);
  return { ok: accepted, correlationId, decision: accepted ? "close" : "stay" };
});
```

### Pattern D – Server Reply Without Using `ack`

Sometimes you want to acknowledge work immediately but stream additional updates later. Combine `request()` for the initial confirmation and `emit_to()` for follow-up events using the same correlation ID.

```python
async def process_event(self, event_type: str, data: dict, sid: str) -> dict | None:
    if event_type != "start_long_task":
        return None

    correlation_id = data.get("correlationId")
    asyncio.create_task(self._run_workflow(sid, correlation_id))
    return {"accepted": True, "correlationId": correlation_id}

async def _run_workflow(self, sid: str, correlation_id: str | None):
    for step in range(10):
        await asyncio.sleep(1)
        await self.emit_to(
            sid,
            "task_progress",
            {"step": step, "total": 10},
            correlation_id=correlation_id,
        )
```

---

## Metadata Flow & Envelopes

### Client → Server Payload

Producers send an object payload as `data` (never primitives). Request metadata like `timeoutMs` and `correlationId` are passed as method options, not embedded into `data`.

The manager validates the payload, resolves/creates `correlationId`, and passes a clean copy of `data` to handlers.

### Server → Client Envelope (mandatory)

```json
{
  "handlerId": "python.websocket_handlers.notifications.NotificationHandler",
  "eventId": "b7e2a9cd-2857-4f7a-8bf4-12a736cb6720",
  "correlationId": "caller-supplied-or-generated",
  "ts": "2025-10-31T13:13:37.123Z",
  "data": { "message": "Hello!" }
}
```

**Guidance:**

- Use `eventId` alongside frontend logging to spot duplicate deliveries or buffered flushes.
- `correlationId` ties together the user action that triggered the event, even if multiple handlers participate.
- `handlerId` helps you distinguish which handler produced the payload, especially when multiple handlers share the same event type.

---

## Diagnostics, Harness & Logging

### Developer Harness

- Location: `Settings → Developer → WebSocket Test Harness`.
- Automatic mode drives emit, request, delayed request (default unlimited timeout), subscription persistence, and envelope validation. It asserts envelope metadata (handlerId, eventId, correlationId, ISO8601 timestamps) and correlation carryover.
- Manual buttons let you trigger individual flows and inspect recent payloads.
- Harness hides itself when `runtime.isDevelopment` is false so production builds incur zero overhead.
- Helper APIs (`createCorrelationId`, `validateServerEnvelope`) are exercised end to end; subscription logs record the `server_restart` broadcast emitted on first connection after a runtime restart.

### WebSocket Event Console

- Location: `Settings → Developer → WebSocket Event Console`.
- Enabling capture calls `websocket.request("ws_event_console_subscribe", { requestedAt })`. The handler (`DevWebsocketTestHandler`) refuses the subscription outside development mode and registers the SID as a **diagnostic watcher** by calling `WebSocketManager.register_diagnostic_watcher`. Only connected SIDs can subscribe.
- Disabling capture calls `websocket.request("ws_event_console_unsubscribe", {})`. Disconnecting also triggers `WebSocketManager.unregister_diagnostic_watcher`, so stranded watchers never accumulate.
- While at least one watcher exists, the manager streams `ws_dev_console_event` envelopes (documented in `contracts/event-schemas.md`). Each payload contains:
  - `kind`: `"inbound" | "outbound" | "lifecycle"`
  - `eventType`, `sid`, `targets[]`, delivery/buffer flags
  - `resultSummary` (handler counts, per-handler status, durationMs)
  - `payloadSummary` (first few keys + byte size)
- Lifecycle broadcasts (`ws_lifecycle_connect` / `ws_lifecycle_disconnect`) are emitted asynchronously via `broadcast(..., diagnostic=True)` so long-running handlers can’t block dispatch.
- The modal UI exposes:
  - Start/stop capture (explicitly controls subscription state).
  - Resubscribe button (detach + resubscribe) to recover gracefully after Socket.IO reconnects.
  - Clear button (resets the in-memory ring buffer).
  - “Handled-only” toggle that filters inbound entries to ones that resolved to registered handlers or produced errors.
- When the watcher set becomes empty the manager immediately stops streaming diagnostics, guaranteeing zero steady-state overhead outside development.

### Instrumentation & Logging

- `WebSocketManager` offloads handler execution via `DeferredTask` and may record `durationMs` when development diagnostics are active (Event Console watchers subscribed). These metrics flow into the Event Console stream (and may also appear in `request()` / `request_all()` results), keeping steady-state overhead near zero when diagnostics are closed.
- Lifecycle events capture `connectionCount`, ISO8601 timestamps, and SID so dashboards can correlate UI behaviour with connection churn.
- Backend logging: use `PrintStyle.debug/info/warning` and always include `handlerId`, `eventType`, `sid`, and `correlationId`. The manager already logs connection events, missing handlers, and buffer overflows.
- Frontend logging: `websocket.debugLog()` mirrors backend debug messages but only when `window.runtimeInfo.isDevelopment` is true.

### Access Logs & Transport Troubleshooting

- Settings → Developer includes a persisted `uvicorn_access_logs_enabled` switch. When enabled, `run_ui.py` enables Uvicorn access logs so transport issues (CORS, handshake failures) can be traced.
- The long-standing `websocket_server_restart_enabled` switch (same section) controls whether newly connected clients receive the `server_restart` broadcast that carries `runtimeId` metadata.

### Common Issues

1. **`CONNECTION_NOT_FOUND`** – `emit_to` called with an SID that never existed or expired long ago. Use `get_sids_for_user` before emitting or guard on connection presence.
2. **Timeout Rejections** – `request()` and `request_all()` reject only when the transport times out, not when a handler takes too long. Inspect the returned result arrays for `TIMEOUT` entries and consider increasing `timeoutMs`.
3. **Origin Rejected** – the Socket.IO handshake was rejected because the `Origin` header did not match the expected UI origin. Ensure you access the UI and the WebSocket endpoint on the same scheme/host/port, and verify any reverse proxy preserves the `Origin` header.
4. **Diagnostics Subscriptions Failing** – only available in development mode and for connected SIDs. Verify the browser tab still holds an active session and that `window.runtimeInfo.isDevelopment` is true before opening the modal.

---

## Best Practices Checklist

- [ ] Always validate inbound payloads in `process_event` (required fields, type constraints, length limits).
- [ ] Propagate `correlationId` through multi-step workflows so logs and envelopes align.
- [ ] Respect the 50 MB payload cap; prefer HTTP + polling for bulk data transfers.
- [ ] Ensure long-running operations emit progress via `emit_to` or switch to an async task with periodic updates.
- [ ] Buffer-sensitive actions (`emit_to`) should handle `ConnectionNotFoundError` from unknown SIDs gracefully.
- [ ] When adding new handlers, update the developer harness if new scenarios need coverage.
- [ ] Keep `PrintStyle` logs meaningful—include `handlerId`, `eventType`, `sid`, and `correlationId`.
- [ ] In Alpine components, call `websocket.off()` during teardown to avoid duplicate subscriptions.

---

## Quick Reference Tables

### Operation Matrix

| Direction | API | Ack? | Filters | Notes |
|-----------|-----|------|---------|-------|
| Client → Server | `emit(event, data, { correlationId? })` | No | None | Fire-and-forget. |
| Client → Server | `request(event, data, { timeoutMs?, correlationId? })` | Yes (`{ correlationId, results[] }`) | None | Aggregates per handler. Timeout entries appear inside `results`. |
| Server → Client | `emit_to(sid, ...)` | No | None | Raises `ConnectionNotFoundError` for unknown `sid`. Buffers if disconnected. |
| Server → Client | `broadcast(...)` | No | `exclude_sids` only | Iterates over current connections; uses the same envelope as `emit_to`. |
| Server → Client | `request(...)` | Yes (`{ correlationId, results[] }`) | None | Equivalent of client `request` but targeted at one SID from the server. |
| Server → Client | `request_all(...)` | Yes (`[{ sid, correlationId, results[] }]`) | None | Server-initiated fan-out. |

### Metadata Cheat Sheet

| Field | Produced By | Guarantees |
|-------|-------------|------------|
| `correlationId` | Manager | Present on every response/envelope. Caller-supplied ID is preserved; otherwise manager generates UUIDv4 hex. |
| `eventId` | Manager | Unique UUIDv4 per server→client delivery. Helpful for dedup / auditing. |
| `handlerId` | Handler / Manager | Deterministic value `module.Class`. Used for results. |
| `ts` | Manager | ISO8601 UTC with millisecond precision. Replaces `+00:00` with `Z`. |
| `results[]` | Manager | Array of `{ handlerId, ok, data?, error? }`. Errors include `code`, `error`, and optional `details`. |

---

## Further Reading

- **QuickStart** – [`specs/003-websocket-event-handlers/quickstart.md`](../specs/003-websocket-event-handlers/quickstart.md) for a step-by-step introduction.
- **Contracts** – Backend, frontend, schema, and security contracts define the canonical API surface:
  - [`websocket-handler-interface.md`](../specs/003-websocket-event-handlers/contracts/websocket-handler-interface.md)
  - [`frontend-api.md`](../specs/003-websocket-event-handlers/contracts/frontend-api.md)
  - [`event-schemas.md`](../specs/003-websocket-event-handlers/contracts/event-schemas.md)
  - [`security-contract.md`](../specs/003-websocket-event-handlers/contracts/security-contract.md)
- **Implementation Reference** – Inspect `python/helpers/websocket_manager.py`, `python/helpers/websocket.py`, `webui/js/websocket.js`, and the developer harness in `webui/components/settings/developer/websocket-test-store.js` for concrete examples.

> **Tip:** When extending the infrastructure (new metadata) start by updating the contracts, sync the manager/frontend helpers, and then document the change here so producers and consumers stay in lockstep.

## Error Codes Registry (Draft for Phase 6)

The WebSocket stack standardizes backend error codes returned in `RequestResultItem.error.code`. This registry documents the currently used codes and their intended meaning. Client and server implementations should reference these values verbatim (UPPER_SNAKE_CASE).

| Code | Scope | Meaning | Typical Remediation | Example Payload |
|------|-------|---------|---------------------|-----------------|
| `NO_HANDLERS` | Manager routing | No handler is registered for the requested `eventType`. | Register a handler for the event or correct the event name. | `{ "handlerId": "WebSocketManager", "ok": false, "error": { "code": "NO_HANDLERS", "error": "No handler for 'missing'" } }` |
| `TIMEOUT` | Aggregated or single request | The request exceeded `timeoutMs`. | Increase `timeoutMs`, reduce handler processing time, or split work. | `{ "handlerId": "ExampleHandler", "ok": false, "error": { "code": "TIMEOUT", "error": "Request timeout" } }` |
| `CONNECTION_NOT_FOUND` | Single‑sid request | Target `sid` is not connected/known. | Use an active `sid` or retry after reconnect. | `{ "handlerId": "WebSocketManager", "ok": false, "error": { "code": "CONNECTION_NOT_FOUND", "error": "Connection 'sid-123' not found" } }` |
| `HARNESS_UNKNOWN_EVENT` | Developer harness | Harness test handler received an unsupported event name. | Update harness sources or disable the step before running automation. | `{ "handlerId": "python.websocket_handlers.dev_websocket_test_handler.DevWebsocketTestHandler", "ok": false, "error": { "code": "HARNESS_UNKNOWN_EVENT", "error": "Unhandled event", "details": "ws_tester_foo" } }` |

Notes
- Error payload shape follows the contract documented in `contracts/event-schemas.md` (`RequestResultItem.error`).
- Codes are case‑sensitive. Use exactly as listed.
- Future codes will be appended here and referenced by inline docstrings/JSDoc.

### Client-Side Error Codes (Draft)

The frontend can originate errors during validation, connection, or request execution. Today these surface as thrown exceptions/promise rejections (not as `RequestResultItem`). When server→client request/ack lands in the future, these codes will also be serialised in `RequestResultItem.error.code` for protocol symmetry.

| Code | Scope | Current Delivery | Meaning | Typical Remediation | Example |
|------|-------|------------------|---------|---------------------|---------|
| `VALIDATION_ERROR` | Producer options / payload | Exception (throw) | Invalid options (e.g., bad `timeoutMs`/`correlationId`) or non-object payload | Fix caller options and payload shapes | `new Error("timeoutMs must be a non-negative number")` |
| `PAYLOAD_TOO_LARGE` | Size precheck (50MB cap) | Exception (throw) | Client precheck rejects payloads exceeding cap before emit | Reduce payload or chunk via HTTP; keep binaries off WS | `new Error("Payload size exceeds maximum (.. > .. bytes)")` |
| `NOT_CONNECTED` | Socket status | Exception (throw) | Auto-connect could not establish a session (user logged out, server offline, handshake rejected) | Check login state, server availability, and Origin policy; optional `await websocket.connect()` for diagnostics | `new Error("Not connected")` |
| `REQUEST_TIMEOUT` | request() | Not used (end-state) | Timeouts are represented inside `results[]` as `error.code="TIMEOUT"` (Promise resolves). | Inspect `results[]` for `TIMEOUT` items and handle in UI. | N/A |
| `CONNECT_ERROR` | Socket connect_error | Exception (throw/log) | Transport/handshake failure | Check server availability, CORS, or network | `new Error("WebSocket connection failed: ...")` |

Notes
- These are currently local exceptions, not part of the aggregated results payload. Calling code should `try/catch` or handle promise rejections.
- When server→client request/ack is introduced, the same codes will be serialised into `RequestResultItem.error.code` to maintain symmetry with backend codes.
- Prefer branching on `code` when available; avoid coupling to full message strings.

### IDE Hints (Non‑enforcing)

To surface recognized codes without adding toolchain dependencies, front‑end can use a JSDoc union type near the helper exports:

```javascript
/** @typedef {('NO_HANDLERS'|'TIMEOUT'|'CONNECTION_NOT_FOUND')} WsErrorCode */
```

Back‑end can reference this registry via concise docstrings at error construction points (e.g., `_build_error_result`) to improve discoverability.

---

## Phase 6 – Registry & Helper Work Status

Current status
- This registry table is drafted and linked; it documents codes already produced by the manager/helpers today.

Remaining work (tracked in Phase 6 tasks)
- T148: Ensure the registry is complete and cross‑referenced from comments/docstrings (backend) and JSDoc typedefs (frontend). No new linter/tooling.
- T144: Reference the registry from contracts and quickstart examples; align all examples to documented codes.
- T141/T143: Add/adjust tests to assert known codes only in helper/manager paths.
- T145–T147: Ensure the harness logs/validates codes in envelopes/results as part of the automatic and manual suites.

Related references
- [`event-schemas.md`](../specs/003-websocket-event-handlers/contracts/event-schemas.md)
- [`websocket-handler-interface.md`](../specs/003-websocket-event-handlers/contracts/websocket-handler-interface.md)
- [`frontend-api.md`](../specs/003-websocket-event-handlers/contracts/frontend-api.md)
