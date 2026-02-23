<!-- SPDX-License-Identifier: Apache-2.0 -->

# Honcho Plugin for Agent Zero

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![SDK: honcho-ai](https://img.shields.io/badge/SDK-honcho--ai_v2.x-purple.svg)](https://pypi.org/project/honcho-ai/)
[![Agent Zero: v0.8+](https://img.shields.io/badge/Agent_Zero-v0.8%2B-green.svg)](https://github.com/agent0ai/agent-zero)

Connect [Agent Zero](https://github.com/agent0ai/agent-zero) with
[Honcho](https://honcho.dev) — a conversational-memory platform that gives
your agent **persistent user context** across sessions.

---

## Features

| Feature | Description |
|---|---|
| **Automatic Message Sync** | Every user and assistant message is pushed to Honcho in real time. |
| **Persistent User Context** | User preferences and facts survive across separate chat sessions. |
| **System-Prompt Injection** | Summarised context is injected automatically so the agent "remembers". |
| **Lazy Initialisation** | No restart required — add the API key and the plugin activates on the next message. |
| **Retry & Resilience** | API calls use exponential back-off; transient errors do not crash the agent. |
| **Secure by Default** | API key loaded only from the secrets manager; never logged. |

---

## Architecture

```
┌─────────────────────────┐          ┌───────────────────────┐
│      Agent Zero         │          │     Honcho Cloud       │
│                         │          │                       │
│  ┌───────────────────┐  │   REST   │  ┌─────────────────┐ │
│  │  agent_init       │  │─────────▶│  │  Sessions        │ │
│  │  _20_honcho_init  │  │          │  │  Peers           │ │
│  └─────────┬─────────┘  │          │  │  Messages        │ │
│           │              │          │  │  Context/Summary │ │
│  ┌─────────┴─────────┐  │          │  └─────────────────┘ │
│  │  hist_add_before  │  │─────────▶│                       │
│  │  _20_honcho_sync  │  │  push    │  Messages are stored   │
│  └─────────┬─────────┘  │  msgs    │  and summarised by     │
│           │              │          │  Honcho’s backend.     │
│  ┌─────────┴──────────┐ │          │                       │
│  │  system_prompt      │ │─────────▶│  Context is fetched    │
│  │  _30_honcho_context │ │  fetch   │  and cached (120s TTL) │
│  └──────────┬─────────┘ │  ctx     │                       │
│           │              │          │                       │
│  ┌─────────┴─────────┐  │          │                       │
│  │  honcho_helper.py │  │          │                       │
│  │  (shared core)    │  │          │                       │
│  └───────────────────┘  │          │                       │
└─────────────────────────┘          └───────────────────────┘
```

### Data Flow

1. **`_20_honcho_init`** — On agent start, creates a Honcho session
   mapped to the A0 chat ID (`chat-{context.id}`).
2. **`_20_honcho_sync`** — Before each message is persisted in A0’s
   history, it is pushed to the Honcho session.
3. **`_30_honcho_context`** — When the system prompt is assembled,
   summarised user context is fetched (with caching) and appended.
4. **`honcho_helper.py`** — Shared library handling SDK calls, retries,
   caching, validation, and secret management.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Agent Zero | v0.8 or later |
| Python | 3.10+ |
| `honcho-ai` SDK | 2.x (`pip install honcho-ai`) |
| Honcho API key | [app.honcho.dev/api-keys](https://app.honcho.dev/api-keys) |

---

## Installation

### 1. Install the SDK

```bash
pip install honcho-ai
```

### 2. Copy the plugin

Place the `honcho/` directory inside your Agent Zero `plugins/` folder:

```
agent-zero/
└── plugins/
    └── honcho/          ← this folder
```

### 3. Configure secrets

Open **Settings → Secrets** in the Agent Zero UI and add:

| Secret | Required | Default | Description |
|---|---|---|---|
| `HONCHO_API_KEY` | **Yes** | — | Your Honcho API key |
| `HONCHO_WORKSPACE_ID` | No | `agent-zero` | Workspace identifier |
| `HONCHO_USER_ID` | No | `user` | User identifier |

### 4. Restart Agent Zero (or just start chatting)

The plugin uses lazy initialisation — it activates automatically on the
next message once the API key is present.

---

## Plugin Structure

```
plugins/honcho/
├── helpers/
│   └── honcho_helper.py                           # Core client & utilities
├── extensions/
│   └── python/
│       ├── agent_init/
│       │   └── _20_honcho_init.py                  # Bootstrap on agent start
│       ├── hist_add_before/
│       │   └── _20_honcho_sync.py                  # Push messages to Honcho
│       └── system_prompt/
│           └── _30_honcho_context.py                # Inject user context
├── README.md
└── LICENSE
```

---

## Configuration Reference

| Parameter | Source | Default | Description |
|---|---|---|---|
| `HONCHO_API_KEY` | Secrets | — | API key for Honcho (required) |
| `HONCHO_WORKSPACE_ID` | Secrets | `agent-zero` | Logical workspace grouping |
| `HONCHO_USER_ID` | Secrets | `user` | Identity for the human user |
| `CONTEXT_CACHE_TTL` | Code constant | `120` (seconds) | How long fetched context is cached |
| `MAX_MESSAGE_LENGTH` | Code constant | `10 000` (chars) | Messages are truncated before sending |
| `_RETRY_ATTEMPTS` | Code constant | `3` | Max retries on transient API errors |
| `_RETRY_BASE_DELAY` | Code constant | `0.5` (seconds) | Initial back-off delay (doubles each retry) |

---

## Disabling the Plugin

Remove (or clear) `HONCHO_API_KEY` from **Settings → Secrets**.  The
integration will silently skip all hooks on the next message.

Alternatively, move or delete the `plugins/honcho/` directory.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No context injected | API key missing or empty | Add `HONCHO_API_KEY` in Settings → Secrets |
| `Honcho SDK not installed` in logs | `honcho-ai` package missing | Run `pip install honcho-ai` in the A0 container |
| `sync_message failed` errors | Network / Honcho outage | Check connectivity; retries handle transient issues automatically |
| Stale context | Cache TTL not expired | Wait ~2 min or restart agent; cache TTL is 120 s |
| `Invalid message role` warning | Extension received unexpected role | Ensure only `user`/`assistant` messages reach the sync hook |
| Plugin not activating | Plugin directory misplaced | Verify path is `plugins/honcho/` at the A0 root |

### Logging

All plugin logs use the `honcho` logger.  Increase verbosity with:

```python
import logging
logging.getLogger("honcho").setLevel(logging.DEBUG)
```

Message **content is never logged in full** — only a truncated preview
(≤80 chars) appears at `DEBUG` level.

---

## Security Notes

- The API key is retrieved exclusively from Agent Zero’s secrets manager
  and is **never** written to log output.
- Message content is truncated in all log messages.
- No file-based debug logs are created.
- No hard-coded paths or virtual-environment references.
- Input validation prevents empty or malformed data from reaching the API.

---

## SDK Compatibility

| SDK | Tested |
|---|---|
| `honcho-ai` 2.0.x | ✅ |
| `honcho-ai` 2.1.x | ✅ (expected) |

---

## Screenshots

<!-- TODO: Add screenshots showing:
  - Settings > Secrets configuration
  - System prompt with injected Honcho context
  - Agent log output demonstrating sync
-->

---

## License

[Apache License 2.0](LICENSE) — matching the Honcho SDK license.

---

## Links

- [Honcho Documentation](https://docs.honcho.dev)
- [Honcho Python SDK](https://github.com/plastic-labs/honcho-python)
- [Agent Zero](https://github.com/agent0ai/agent-zero)
- [Agent Zero Plugin System](https://github.com/agent0ai/agent-zero/pull/998)
