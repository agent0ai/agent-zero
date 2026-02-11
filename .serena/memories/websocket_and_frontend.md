# Apollos AI - WebSocket & Frontend Reference

## WebSocket Architecture

### Backend (Python)
- **Transport**: Socket.IO over ASGI (python-socketio + uvicorn)
- **Namespaces**: `/` (root), `/state_sync`, extensible
- **Discovery**: Auto-discovers handlers from `python/websocket_handlers/`
- **Manager**: `WebSocketManager` routes events, buffers offline messages, tracks connections
- **Security**: Origin validation (RFC 6455), CSRF on connect, optional auth

### Backend Handlers
| Handler | Namespace | Purpose |
|---------|-----------|---------|
| `RootDefaultHandler` | `/` | Diagnostics only (no auth) |
| `StateSyncHandler` | `/state_sync` | Bidirectional state sync |
| `HelloHandler` | `/hello` | Sample/testing handler |

### Frontend Client (`webui/js/websocket.js`)
- **WebSocketClient**: Socket.IO wrapper per namespace
- **Patterns**: `emit()` (fire-and-forget), `request()` (request-response), `subscribe()` (events)
- **Reconnection**: Exponential backoff (250ms base, 10s cap)
- **Payload validation**: Correlation IDs, server envelope validation

## Frontend Architecture

### Tech Stack
- **No framework** — vanilla JS + Alpine.js for reactivity
- **State**: Alpine.js stores extending `AlpineStore` base class
- **WebSocket**: Socket.IO client for real-time updates
- **REST**: Fetch API with CSRF token management

### Directory Structure
```
webui/
├── index.html          Main entry point
├── index.js            Global init (DOMContentLoaded)
├── index.css           Global styles
├── js/                 Core modules
│   ├── websocket.js    Socket.IO wrapper (WebSocketClient)
│   ├── api.js          REST API + CSRF management
│   ├── messages.js     Message rendering (64KB)
│   ├── AlpineStore.js  Alpine.js reactive store base
│   ├── components.js   Component registration
│   └── modals.js       Modal management
├── components/         Alpine.js reactive components
│   ├── chat/           Chat interface (input, messages, attachments, speech)
│   ├── sync/           State synchronization store
│   ├── sidebar/        Navigation (chats, tasks, preferences)
│   ├── notifications/  Toast notifications
│   ├── settings/       Settings panels (MCP, tunnel, skills, backup, dev tools)
│   └── messages/       Message rendering components
├── css/                Modular stylesheets
├── vendor/             Third-party (Socket.IO, Flatpickr, Ace editor, KaTeX)
└── public/             Static assets
```

### Key Stores
| Store | File | Purpose |
|-------|------|---------|
| `syncStore` | sync/sync-store.js | State sync (handshake, sequences, degradation) |
| `inputStore` | chat/input/input-store.js | Message input field |
| `chatsStore` | sidebar/chats/chats-store.js | Chat list |
| `tasksStore` | sidebar/tasks/tasks-store.js | Task list |
| `notificationStore` | notifications/notification-store.js | Toast queue |
| `preferencesStore` | sidebar/bottom/preferences/preferences-store.js | User prefs |
| `speechStore` | chat/speech/speech-store.js | TTS/STT |
| `attachmentsStore` | chat/attachments/attachmentsStore.js | File uploads |

### State Sync Flow
1. Client connects to `/state_sync` namespace
2. Sends `state_request` with context, log ranges, timezone
3. Server returns `seq_base` + `runtimeEpoch`
4. Client enters HEALTHY mode, receives incremental updates
5. On gap → DEGRADED → auto-recovers on re-sync
