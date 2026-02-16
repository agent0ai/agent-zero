# Honcho Conversational Memory Integration

This extension connects Agent Zero with [Honcho](https://honcho.dev), a
conversational memory platform by [Plastic Labs](https://plasticlabs.ai) that
provides **persistent user context across sessions**.

## Features

| Feature | Description |
|---------|-------------|
| **Automatic Message Sync** | Every user and assistant message is synced to Honcho in real time |
| **Persistent User Context** | User preferences and information persist across conversations |
| **Lazy Initialization** | No restart required — activates on first message after configuration |
| **Context Caching** | TTL-based cache prevents excessive API calls |
| **Graceful Degradation** | Silently skips if unconfigured or SDK is missing |

## Prerequisites

1. Install the Honcho SDK:
   ```bash
   pip install honcho-ai
   ```

2. Obtain a Honcho API key from [app.honcho.dev/api-keys](https://app.honcho.dev/api-keys)

## Configuration

Add the following to Agent Zero **Secrets** (Settings → Secrets):

| Secret | Required | Description |
|--------|----------|-------------|
| `HONCHO_API_KEY` | Yes | Your Honcho API key |
| `HONCHO_WORKSPACE_ID` | No | Workspace identifier (default: `agent-zero`) |
| `HONCHO_USER_ID` | No | User identifier (default: `user`) |

## File Structure

```
extensions/
├── honcho_helper.py                    # Core client utilities & caching
├── agent_init/
│   └── _20_honcho_init.py              # Initialize session on agent start
├── hist_add_before/
│   └── _20_honcho_sync.py              # Sync messages to Honcho
└── system_prompt/
    └── _30_honcho_context.py           # Inject user context into prompts
```

## How It Works

```
User sends message  ─→  hist_add_before  ─→  sync to Honcho
Agent responds      ─→  hist_add_before  ─→  sync to Honcho
New session starts  ─→  system_prompt    ─→  fetch & inject user context
```

1. **Lazy Init**: The first message triggers Honcho setup if an API key exists.
2. **Message Sync**: Every history entry is forwarded to Honcho via the
   `hist_add_before` extension hook.
3. **Context Injection**: On each prompt cycle the `system_prompt` hook
   retrieves a summary / peer-representation from Honcho and appends it
   to the system prompt.

## Installation

Copy the extension files into your Agent Zero user extensions directory:

```bash
# From Agent Zero root
cp -r agents/_example/extensions/honcho_helper.py       usr/extensions/
cp -r agents/_example/extensions/agent_init/_20_honcho_init.py  usr/extensions/agent_init/
cp -r agents/_example/extensions/hist_add_before/_20_honcho_sync.py usr/extensions/hist_add_before/
cp -r agents/_example/extensions/system_prompt/_30_honcho_context.py usr/extensions/system_prompt/
```

Then add your `HONCHO_API_KEY` in **Settings → Secrets** and send a message.

## Verifying

After configuration the agent logs will show:
```
[Honcho] Integration enabled for session: chat-xxx
```

## SDK Compatibility

Tested with **honcho-ai 2.x** (PyPI: `honcho-ai`).

## Disabling

Remove `HONCHO_API_KEY` from Secrets — the integration silently deactivates.

## Learn More

- [Honcho Documentation](https://docs.honcho.dev)
- [Honcho Python SDK](https://github.com/plastic-labs/honcho-python)
- [Plastic Labs](https://plasticlabs.ai)
