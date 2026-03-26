# Plugin System Roadmap: Communication Channels & Infrastructure Gaps

> **Status**: RFC / Proposal for inclusion in the Plugin System PR
> **Author**: Community Contribution
> **Context**: Analysis of what the plugin system needs to support first-class communication channel plugins (Telegram, Slack, Discord, etc.) and other complex plugin use cases.
> **Companion Documents**: Communication Channels Spec (v2), Real-Time Voice Deep-Dive

---

## Motivation

The plugin system introduced in this PR establishes a solid convention-over-configuration foundation. Plugins can already contribute tools, extensions, API endpoints, prompts, agent profiles, helpers, and frontend components — all discovered from directory structure with zero manifest configuration.

However, building a **communication channel plugin** (e.g., a Telegram bridge that receives messages, routes them through Agent Zero, and returns responses) exposes several infrastructure gaps. These gaps also affect other plugin categories: monitoring dashboards, notification relays, scheduled integrations, and anything that needs to run a persistent background service or expose configuration to the user.

This document defines five capabilities the plugin system should provide, explains their implementation requirements, and proposes a phased roadmap. The goal is to give the community clear requirements so contributions can land incrementally without blocking each other.

---

## Table of Contents

1. [Plugin Manifest (`plugin.json`)](#1-plugin-manifest-pluginjson)
2. [Plugin Lifecycle Management](#2-plugin-lifecycle-management)
3. [Plugin-Scoped Settings & Configuration](#3-plugin-scoped-settings--configuration)
4. [WebSocket Handler Pluggability](#4-websocket-handler-pluggability)
5. [Pluggable Webhook Endpoints for Inbound Communication](#5-pluggable-webhook-endpoints-for-inbound-communication)
6. [Phased Roadmap](#6-phased-roadmap)
7. [Reference: Telegram Channel Plugin (Target Architecture)](#7-reference-telegram-channel-plugin-target-architecture)

---

## 1. Plugin Manifest (`plugin.json`)

### Problem

Today, runtime discovery is entirely convention-driven — which is excellent for simplicity but leaves no mechanism for a plugin to declare metadata, dependencies, required environment variables, or configuration schema. There is no way for the system (or users) to know what a plugin needs before it fails at runtime.

### Proposed Solution

Introduce an **optional** `plugin.json` manifest at the plugin root. The runtime discovery model remains convention-based (the manifest does not replace directory scanning), but the manifest enables:

- Human-readable metadata (name, description, author, version, license, homepage)
- Dependency declarations (Python packages, npm packages, system tools)
- Environment variable requirements with descriptions and defaults
- Configuration schema for plugin-scoped settings (see §3)
- Lifecycle declarations (see §2)
- Capability flags for the UI (e.g., `"has_settings": true`, `"has_frontend": true`)

### Proposed Schema

```jsonc
{
  // --- Metadata (informational, displayed in UI) ---
  "id": "telegram",
  "name": "Telegram Bridge",
  "description": "Bridges Telegram chats to Agent Zero conversations",
  "version": "1.0.0",
  "author": "community",
  "license": "MIT",
  "homepage": "https://github.com/example/a0-plugin-telegram",
  "tags": ["communication", "telegram", "bridge"],

  // --- Dependencies ---
  "dependencies": {
    "python": ["aiogram>=3.0,<4.0"],
    "system": []  // e.g., ["ffmpeg"] for media processing plugins
  },

  // --- Environment Variables ---
  "env": {
    "TELEGRAM_BOT_TOKEN": {
      "description": "Bot token from @BotFather",
      "required": true,
      "sensitive": true
    },
    "TELEGRAM_ALLOWED_CHAT_IDS": {
      "description": "Comma-separated list of allowed chat IDs (empty = allow all)",
      "required": false,
      "default": ""
    }
  },

  // --- Configuration Schema (feeds into plugin-scoped settings) ---
  "settings": {
    "polling_mode": {
      "type": "select",
      "label": "Inbound Mode",
      "options": ["polling", "webhook"],
      "default": "polling",
      "description": "Use long-polling or webhook for receiving Telegram updates"
    },
    "context_lifetime_hours": {
      "type": "number",
      "label": "Chat Lifetime (hours)",
      "default": 24,
      "description": "How long to keep a conversation context alive after last message"
    },
    "project": {
      "type": "text",
      "label": "Default Project",
      "default": "",
      "description": "Activate this A0 project for all Telegram conversations"
    }
  },

  // --- Lifecycle ---
  "lifecycle": {
    "background_service": true,  // Plugin runs a persistent background task
    "startup_extension": "extensions/backend/agent_init/_90_telegram_start.py"
  },

  // --- Capabilities (UI hints) ---
  "capabilities": {
    "has_settings": true,
    "has_frontend": true,
    "has_tools": true,
    "has_api": true,
    "has_webhook": true
  }
}
```

### Design Principles

- **Optional**: Plugins without `plugin.json` continue to work exactly as they do today. The manifest is additive.
- **Declarative**: The manifest describes *what* a plugin needs, not *how* it works. Runtime behaviour is still convention-driven from directory structure.
- **Machine-readable**: Enables future UI for plugin management (install, configure, enable/disable), dependency resolution, and a plugin registry/marketplace.

### Implementation Requirements

| Requirement | Detail |
|---|---|
| `plugins.py` reads `plugin.json` | Extend `list_plugins()` to parse manifest when present. Populate `Plugin` dataclass with metadata fields. |
| Validation helper | `validate_plugin_manifest(path) → list[str]` returning warnings/errors. Called at startup, results surfaced in UI banners. |
| Dependency check at startup | On plugin discovery, check `dependencies.python` against installed packages. Log warnings for missing deps. Do not hard-fail (allow graceful degradation). |
| Env var check at startup | For each `env` entry with `required: true`, check `os.environ`. Surface missing vars as UI warnings/notifications. |
| `sensitive` flag handling | Settings and env vars marked `sensitive: true` are masked in UI and never logged. |

### Priority: **Phase 1 (Foundation)**

The manifest is a prerequisite for plugin-scoped settings (§3) and clean lifecycle management (§2). It should land first.

---

## 2. Plugin Lifecycle Management

### Problem

Today, plugins that need a persistent background service (e.g., a Telegram bot polling for messages) must piggyback on the `agent_init` extension point. This creates several issues:

- `agent_init` fires per-agent-instantiation, not once at application startup. A singleton guard is needed to avoid spawning duplicate bot instances.
- There is no `on_stop` or `on_shutdown` hook. Background tasks cannot gracefully clean up (close connections, flush buffers, deregister webhooks).
- There is no health/status reporting mechanism. The UI cannot show whether a plugin's background service is running, errored, or stopped.
- Error recovery is manual. If the Telegram bot crashes, nothing restarts it.

### Proposed Solution

Introduce a plugin lifecycle protocol with four stages and corresponding hooks:

```
REGISTERED → STARTING → RUNNING → STOPPING → STOPPED
                ↓                      ↑
              ERROR ──────────────────→
```

#### Lifecycle Hooks

Plugins declare a lifecycle class (either via convention at `lifecycle.py` in the plugin root, or explicitly in `plugin.json`):

```python
# plugins/telegram/lifecycle.py
from python.helpers.plugin_lifecycle import PluginLifecycle

class TelegramLifecycle(PluginLifecycle):
    async def on_start(self, context: PluginContext) -> None:
        """Called once at application startup (after all plugins are discovered).
        Use for: starting background tasks, establishing connections, registering webhooks.
        """
        self.bridge = TelegramBridge(context.settings, context.env)
        self.task = asyncio.create_task(self.bridge.start())

    async def on_stop(self, context: PluginContext) -> None:
        """Called on application shutdown or plugin disable.
        Use for: graceful cleanup, deregistering webhooks, closing connections.
        """
        await self.bridge.stop()
        self.task.cancel()

    async def health_check(self) -> PluginHealth:
        """Called periodically by the plugin manager.
        Returns health status for UI display and monitoring.
        """
        if self.bridge.is_running:
            return PluginHealth(
                status="running",
                detail=f"Connected, {self.bridge.active_chats} active chats"
            )
        return PluginHealth(status="error", detail=self.bridge.last_error)
```

#### Plugin Context

The `PluginContext` object passed to lifecycle hooks provides:

```python
@dataclass
class PluginContext:
    plugin: Plugin                    # Plugin metadata
    settings: dict[str, Any]         # Resolved plugin-scoped settings (see §3)
    env: dict[str, str]              # Resolved environment variables
    logger: logging.Logger           # Plugin-scoped logger
    notification_manager: NotificationManager  # For sending notifications
```

#### Plugin Manager

A new `PluginManager` singleton (initialised in `run_ui.py` after plugin discovery) orchestrates lifecycle:

```python
class PluginManager:
    async def start_all(self) -> None:
        """Called once at application startup after discovery."""
        for plugin in plugins.list_plugins():
            lifecycle = self._load_lifecycle(plugin)
            if lifecycle:
                try:
                    await lifecycle.on_start(self._build_context(plugin))
                    self._states[plugin.id] = PluginState.RUNNING
                except Exception as e:
                    self._states[plugin.id] = PluginState.ERROR
                    self._errors[plugin.id] = str(e)

    async def stop_all(self) -> None:
        """Called on application shutdown."""
        for plugin_id, lifecycle in self._lifecycles.items():
            await lifecycle.on_stop(...)

    async def restart(self, plugin_id: str) -> None:
        """Restart a single plugin (callable from UI/API)."""
        await self.stop(plugin_id)
        await self.start(plugin_id)

    def get_status(self, plugin_id: str) -> PluginState:
        """Returns current lifecycle state for UI display."""
        ...
```

### Implementation Requirements

| Requirement | Detail |
|---|---|
| `PluginLifecycle` base class | New file: `python/helpers/plugin_lifecycle.py`. Abstract methods: `on_start`, `on_stop`, `health_check`. |
| `PluginManager` singleton | New file: `python/helpers/plugin_manager.py`. Manages lifecycle instances, states, error tracking, restart logic. |
| Integration in `run_ui.py` | Call `PluginManager.start_all()` after API handler registration. Register shutdown hook for `stop_all()`. |
| Supervision / restart policy | Configurable per-plugin: `restart_on_error: true` with backoff. Default: no auto-restart (log error, set state to ERROR). |
| API endpoint for plugin status | `GET /plugins_status` returns `{plugin_id: {state, health, error, uptime}}` for all plugins. |
| Frontend status display | Plugin management UI component showing state, health, restart/stop buttons. Auto-injected into Settings. |

### Priority: **Phase 2 (Core Infrastructure)**

Lifecycle management is the single most impactful capability for communication channel plugins. Without it, background services are fragile.

---

## 3. Plugin-Scoped Settings & Configuration

### Problem

There is no mechanism for a plugin to declare its own configurable settings that appear in the Agent Zero Settings UI. Plugin authors must resort to:

- Hardcoded values in source
- Environment variables (no UI, no validation, no documentation)
- JSON config files in the plugin directory (no UI, manual editing)

This makes plugins harder to install and configure for non-developer users.

> **Note (v2)**: The Communication Channels Spec implements a temporary workaround for this gap: settings fields added directly to A0's core `settings.py` dataclass with a settings panel in the web UI. This is explicitly a stopgap — the core file modifications are marked `TEMPORARY` and will be removed when plugin-scoped settings land. The workaround validates the UX requirements documented below while accepting the coupling cost short-term.

### Proposed Solution

Plugins declare settings in `plugin.json` (see §1) using a typed schema. The plugin system provides:

1. **Schema-driven UI generation** — A settings panel is auto-generated for each plugin that declares settings.
2. **Persistence** — Settings are stored in `usr/plugins/<plugin_id>/settings.json` (follows the existing override convention).
3. **Runtime access** — Settings are passed to lifecycle hooks via `PluginContext.settings` and accessible from tools/extensions via a helper.
4. **Validation** — Type checking and constraint validation on save.

#### Settings Schema Types

```jsonc
{
  "settings": {
    "field_name": {
      "type": "text" | "number" | "boolean" | "select" | "password",
      "label": "Human-readable label",
      "description": "Help text shown in UI",
      "default": "...",
      "required": false,
      // Type-specific:
      "options": ["a", "b"],     // for "select"
      "min": 0, "max": 100,     // for "number"
      "placeholder": "..."       // for "text" and "password"
    }
  }
}
```

#### Runtime Access

```python
# From any tool, extension, or helper within the plugin:
from python.helpers.plugins import get_plugin_settings

settings = get_plugin_settings("telegram")
token = settings.get("bot_token", "")
mode = settings.get("polling_mode", "polling")
```

#### Storage

```
usr/plugins/telegram/
└── settings.json    # {"polling_mode": "webhook", "context_lifetime_hours": 48}
```

Values not present in `settings.json` fall back to defaults declared in `plugin.json`. Sensitive values (passwords, tokens) are encrypted at rest using the same mechanism as project secrets.

### Implementation Requirements

| Requirement | Detail |
|---|---|
| Settings persistence | `get_plugin_settings(plugin_id)` reads `usr/plugins/{id}/settings.json`, merges with defaults from `plugin.json`. |
| Settings save API | `POST /plugins/{plugin_id}/settings` validates against schema, writes to `usr/plugins/{id}/settings.json`. |
| UI generation | Generic settings component that renders form fields from schema. Injected into Settings page under a "Plugins" section. |
| Encryption for sensitive fields | Fields with `"type": "password"` or `"sensitive": true` encrypted at rest. Masked in UI. Never returned in API responses (only `"*****"` placeholder). |
| Settings change notification | When settings are saved, emit an event (extension point or WebSocket) so running plugins can reload configuration without restart. Lifecycle hook: `on_settings_changed(new_settings)`. |

### Priority: **Phase 2 (Core Infrastructure)**

Settings are tightly coupled with lifecycle management — a plugin's `on_start` needs its settings, and settings changes may trigger a restart.

---

## 4. WebSocket Handler Pluggability

### Problem

The WebSocket infrastructure supports custom handlers placed in `python/websocket_handlers/`, but this path is not included in plugin discovery. Plugins cannot contribute WebSocket handlers. This matters for:

- Real-time notification forwarding (agent completes a task → push to Telegram/Slack)
- Plugin status streaming (live health/metrics to frontend)
- Bidirectional real-time communication between plugin frontend components and plugin backend logic
- Event bus participation (plugins reacting to WebSocket events from other plugins or core)

### Proposed Solution

Extend the WebSocket handler discovery in `run_ui.py` to scan plugin directories:

```
plugins/<plugin_id>/websocket_handlers/*.py    → namespace derived from plugin_id
```

#### Convention

```
plugins/telegram/
└── websocket_handlers/
    └── telegram_status.py    → namespace: /plugins/telegram
```

Handlers within a plugin's `websocket_handlers/` directory follow the same `WebSocketHandler` base class contract. They are auto-registered under a `/plugins/{plugin_id}` namespace to avoid collisions with core handlers.

#### Example

```python
# plugins/telegram/websocket_handlers/telegram_status.py
from python.helpers.websocket import WebSocketHandler

class TelegramStatusHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["telegram_status_request", "telegram_status_push"]

    async def process_event(self, event_type: str, data: dict, sid: str) -> dict | None:
        if event_type == "telegram_status_request":
            bridge = TelegramBridge.get_instance()
            return {
                "ok": True,
                "is_running": bridge.is_running,
                "active_chats": bridge.active_chats,
                "last_message_at": bridge.last_message_at,
            }
        return None
```

The plugin's frontend component can then subscribe:

```javascript
import { getNamespacedClient } from "/js/websocket.js";
const ws = getNamespacedClient("/plugins/telegram");
const { results } = await ws.request("telegram_status_request", {});
```

### Implementation Requirements

| Requirement | Detail |
|---|---|
| Handler discovery in `run_ui.py` | Extend `_build_websocket_handlers_by_namespace()` to scan `plugins/*/websocket_handlers/`. |
| Namespace isolation | Plugin WS handlers register under `/plugins/{plugin_id}` namespace. Core handlers remain at their existing namespaces. |
| Frontend namespace client | `getNamespacedClient("/plugins/{plugin_id}")` already works with the existing `websocket.js` implementation — no frontend changes needed. |
| Handler lifecycle | Plugin WS handlers follow the same singleton pattern as core handlers. `on_connect`/`on_disconnect` hooks available. |

### Priority: **Phase 3 (Enhancement)**

WebSocket pluggability is valuable but not blocking for the initial communication channel plugin, which can use REST polling or the notification system for status updates. It becomes important for real-time plugin dashboards and inter-plugin eventing.

---

## 5. Pluggable Webhook Endpoints for Inbound Communication

### Problem

Communication platforms (Telegram, Slack, Discord, GitHub) can push events to an HTTP endpoint (webhook) rather than requiring the plugin to poll. Today, plugins can already register API endpoints via `api/*.py`, but there are gaps:

- **No authentication bypass model**: Plugin API handlers inherit the core auth model (`requires_auth`, `requires_csrf`, `requires_api_key`). External webhooks need to bypass these and implement their own verification (e.g., Telegram's secret token header, Slack's signing secret, GitHub's HMAC signature).
- **No public URL discovery**: Webhook registration requires the plugin to know its own public URL. There is no mechanism for a plugin to ask "what is my externally-reachable URL?".
- **No webhook lifecycle management**: Registering and deregistering webhooks (e.g., `setWebhook` on Telegram API) should be tied to plugin start/stop, not left to manual setup.

### Proposed Solution

#### 5a. Webhook-Aware API Handlers

Extend `ApiHandler` with a webhook mode that provides platform-specific verification:

```python
# plugins/telegram/api/telegram_webhook.py
from python.helpers.api import ApiHandler, Request, Response

class TelegramWebhook(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # External service, no A0 auth

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def is_webhook(cls) -> bool:
        """Marks this endpoint as a webhook. Affects URL generation and
        skips all core auth. Plugin must implement its own verification."""
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        # Verify Telegram secret token
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        expected = get_plugin_settings("telegram").get("webhook_secret", "")
        if not hmac.compare_digest(secret, expected):
            return Response('{"error": "Unauthorized"}', status=403)

        # Process the Telegram Update
        update = input
        bridge = TelegramBridge.get_instance()
        asyncio.create_task(bridge.handle_update(update))

        return {"ok": True}
```

#### 5b. Public URL Resolution

Provide a helper that resolves the plugin's webhook URL using the configured base URL:

```python
from python.helpers.plugins import get_webhook_url

# Returns: "https://my-a0-instance.example.com/plugins/telegram/telegram_webhook"
url = get_webhook_url("telegram", "telegram_webhook")
```

This reads from the existing A0 tunnel/URL configuration. If no public URL is configured, it returns `None` and the plugin can fall back to polling mode.

#### 5c. Webhook Registration in Lifecycle

Webhook registration/deregistration is handled in the plugin's lifecycle hooks:

```python
class TelegramLifecycle(PluginLifecycle):
    async def on_start(self, context: PluginContext) -> None:
        if context.settings.get("polling_mode") == "webhook":
            webhook_url = get_webhook_url("telegram", "telegram_webhook")
            if webhook_url:
                secret = context.settings.get("webhook_secret", "")
                await self.bot.set_webhook(url=webhook_url, secret_token=secret)
            else:
                # Fall back to polling if no public URL available
                context.logger.warning("No public URL configured, falling back to polling")
                asyncio.create_task(self.bridge.start_polling())
        else:
            asyncio.create_task(self.bridge.start_polling())

    async def on_stop(self, context: PluginContext) -> None:
        if self.settings.get("polling_mode") == "webhook":
            await self.bot.delete_webhook()
        await self.bridge.stop()
```

### Implementation Requirements

| Requirement | Detail |
|---|---|
| `is_webhook()` class method on `ApiHandler` | When `True`, handler skips all core auth checks (auth, CSRF, API key). Plugin is responsible for its own verification. |
| `get_webhook_url(plugin_id, handler_name)` helper | Constructs full public URL from A0's configured base URL + plugin route prefix. Returns `None` if no public URL is available. |
| Public URL configuration | Leverage existing tunnel/URL config in A0 settings. Expose as `get_public_base_url()` helper. |
| Webhook endpoint registration logging | Log all webhook endpoint registrations at startup with their full URLs for debugging. |

### Priority: **Phase 3 (Enhancement)**

Webhooks are an optimisation over polling. The initial Telegram plugin should work with long-polling first, and webhook support can be layered on once lifecycle management and settings are in place.

---

## 6. Phased Roadmap

### Phase 1: Foundation

**Goal**: Establish the metadata and configuration substrate that all subsequent phases build on.

| Item | Effort | Depends On |
|---|---|---|
| `plugin.json` schema definition and parser | Medium | — |
| `Plugin` dataclass enrichment with manifest fields | Small | Manifest parser |
| Startup validation (deps, env vars) | Small | Manifest parser |
| UI: Plugin list with metadata display | Medium | Manifest parser |
| Documentation: Plugin authoring guide | Medium | All above |

**Deliverable**: Plugins can declare metadata, dependencies, and required env vars. The UI shows installed plugins with descriptions and health warnings for missing dependencies.

### Phase 2: Core Infrastructure

**Goal**: Enable plugins that run persistent background services with user-configurable settings.

| Item | Effort | Depends On |
|---|---|---|
| `PluginLifecycle` base class and protocol | Medium | — |
| `PluginManager` singleton with start/stop/restart | Medium | Lifecycle base |
| `PluginContext` with settings and env resolution | Small | Manifest parser |
| Integration into `run_ui.py` startup/shutdown | Small | PluginManager |
| Plugin-scoped settings persistence (`usr/plugins/`) | Medium | Manifest settings schema |
| Settings save/load API endpoints | Small | Settings persistence |
| Settings UI auto-generation from schema | Large | Settings API, manifest |
| `on_settings_changed` notification | Small | Settings save |
| Sensitive field encryption | Medium | Settings persistence |
| Health check polling and status API | Small | PluginManager |
| UI: Plugin management panel (status, restart, settings) | Large | All above |

**Deliverable**: A Telegram plugin can start a bot on A0 startup, expose its configuration in the Settings UI, and be restarted from the UI. Users can configure it without touching env vars or JSON files. The temporary core settings fields added by the Comms Spec can be migrated to plugin-scoped settings and the core file modifications removed.

### Phase 3: Enhancements

**Goal**: Add real-time capabilities and webhook support for production-grade channel plugins.

| Item | Effort | Depends On |
|---|---|---|
| WebSocket handler discovery from plugins | Medium | Plugin discovery |
| Namespace isolation for plugin WS handlers | Small | WS discovery |
| `is_webhook()` flag on `ApiHandler` | Small | — |
| `get_webhook_url()` helper | Small | Public URL config |
| Webhook lifecycle integration (register/deregister) | Small | PluginLifecycle |
| Documentation: Communication channel plugin cookbook | Medium | All above |

**Deliverable**: Plugins can contribute WebSocket handlers, register webhooks with external services, and build real-time dashboards.

### Phase 4: Ecosystem (Future)

**Goal**: Enable a plugin marketplace and community sharing.

| Item | Effort | Depends On |
|---|---|---|
| Plugin install from URL/git repo | Large | Manifest, lifecycle |
| Dependency auto-install on plugin install | Medium | Manifest deps |
| Plugin enable/disable without deletion | Medium | PluginManager |
| Plugin registry / marketplace API | Large | All above |
| Per-plugin resource isolation (memory limits, CPU) | Large | PluginManager |

---

## 7. Reference: Telegram Channel Plugin (Target Architecture)

This section shows what a complete Telegram channel plugin looks like once all phases are implemented. This serves as a design target and validation fixture for the plugin system.

```
plugins/telegram/
├── plugin.json                          # Manifest (Phase 1)
├── lifecycle.py                         # Start/stop/health (Phase 2)
├── api/
│   └── telegram_webhook.py             # Webhook endpoint (Phase 3)
├── extensions/
│   ├── backend/
│   │   └── agent_init/
│   │       └── _90_telegram_fallback.py # Fallback start if no lifecycle manager
│   └── frontend/
│       ├── sidebar.quick_actions.dropdown/
│       │   └── telegram-entry.html      # Quick action menu entry
│       └── settings.plugins/
│           └── telegram-status.html     # Status card in plugin settings
├── helpers/
│   ├── telegram_bridge.py              # Core bridge: Telegram ↔ AgentContext.communicate()
│   └── chat_mapping.py                 # chat_id ↔ context_id persistence
├── tools/
│   └── telegram_send.py                # Agent-callable: send Telegram message
├── prompts/
│   └── agent.system.tool.telegram_send.md
└── websocket_handlers/                  # Phase 3
    └── telegram_status.py              # Real-time status for frontend
```

### Message Flow (Inbound: Telegram → Agent Zero)

```
Telegram Update
    │
    ├─[webhook mode]──→ POST /plugins/telegram/telegram_webhook
    │                       │
    │                       ├─ Verify X-Telegram-Bot-Api-Secret-Token
    │                       └─ Pass to bridge.handle_update()
    │
    └─[polling mode]──→ bridge.polling_loop() via lifecycle.on_start()
                            │
                            └─ bridge.handle_update()
                                   │
                                   ├─ Resolve chat_id → context_id (create if new)
                                   ├─ Extract text, files → NormalisedAttachment
                                   ├─ Send typing indicator
                                   ├─ AgentContext.communicate(UserMessage)
                                   │     ↳ Wrapped in asyncio.wait_for(timeout=300)
                                   ├─ Receive response text
                                   └─ bot.send_message(chat_id, response)
```

### Message Flow (Outbound: Agent Zero → Telegram)

```
Agent decides to notify user
    │
    └─ Calls telegram_send tool {chat_id, message}
           │
           └─ TelegramBridge.send_message(chat_id, message)
                  │
                  └─ bot.send_message(chat_id, message)
```

### Chat Mapping Persistence

```python
# plugins/telegram/helpers/chat_mapping.py
# Stores in usr/plugins/telegram/chat_map.json
# Structure: {"telegram_chat_id": {"context_id": "...", "last_active": "...", "project": "..."}}
```

### Applying to Other Platforms

The architecture is identical for Slack and Discord — only the transport layer changes:

| Concern | Telegram | Slack | Discord |
|---|---|---|---|
| SDK | `aiogram>=3.0` | `slack-bolt>=1.18` | `discord.py>=2.3` |
| Inbound (polling) | `getUpdates` long-poll | Socket Mode (WebSocket) | Gateway (WebSocket) |
| Inbound (webhook) | `setWebhook` → HTTP POST | Events API → HTTP POST | Interactions Endpoint |
| Threading model | `chat_id → context_id` | `channel + thread_ts → context_id` | `channel/thread_id → context_id` |
| File handling | `bot.download_file()` | `files.info` + download | `attachment.read()` |
| Auth verification | Secret token header | Signing secret HMAC | Ed25519 signature |
| Outbound tool | `telegram_send` | `slack_send` | `discord_send` |

A shared `CommunicationBridge` base class in a `comms-core` plugin abstracts the common patterns (chat mapping, context lifecycle, attachment handling, voice pipeline, timeout protection, typing indicators), with platform-specific plugins inheriting from it. See the Communication Channels Spec (v2) for the full implementation.

---

## Design Principles

These principles should guide implementation of all five capabilities:

1. **Additive, not breaking** — Every new feature is opt-in. Plugins without `plugin.json`, lifecycle classes, or settings continue to work exactly as they do today.

2. **Convention over configuration** — Directory structure remains the primary discovery mechanism. The manifest enriches but does not replace it.

3. **User-first configuration** — Non-developers should be able to install and configure a Telegram plugin entirely through the UI. No terminal access, no env var editing, no JSON file manipulation.

4. **Graceful degradation** — Missing dependencies log warnings, don't crash. Missing settings fall back to defaults. Missing lifecycle hooks skip lifecycle management. Webhook URL unavailable → fall back to polling.

5. **Security by default** — Webhook endpoints require explicit auth bypass. Sensitive settings are encrypted. Plugin API endpoints are namespaced to prevent route collisions.

6. **Override convention preserved** — `usr/plugins/` takes priority for all plugin components, including settings, lifecycle overrides, and webhook handlers.
