# Telegram Bot Integration

This guide covers setting up a real-time Telegram bot that runs inside the Agent Zero Docker container, allowing you to interact with the same AI model through Telegram as a messaging interface.

> [!NOTE]
> This integration uses a long-polling daemon running inside the Agent Zero container. All bot data is volume-mounted and persists across container rebuilds.

## Overview

The Telegram integration provides:
- **Real-time messaging** — long-poll daemon responds to messages in seconds
- **Full AI capabilities** — uses the same LLM as the main Agent Zero interface
- **Shell tool access** — the bot can execute commands inside the container
- **Conversation history** — per-chat history persisted across restarts
- **Automated alerts** — scheduled weather and news digest scripts
- **Bot commands** — `/start`, `/help`, `/clear`, `/status`

## Architecture

```
User sends Telegram message
        │
        ▼
Telegram API (long-poll, 30s timeout)
        │
        ▼  (instantly)
Daemon inside Agent Zero container
    → spawns background thread
    → calls LLM API (same model as main AI)
    → executes shell commands if needed (tool calling)
    → sends reply via Telegram Bot API
        │
        ▼
User receives response in seconds
```

## File Structure

```
/a0/usr/workdir/telegram/
├── SKILL.md                        ← Documentation
├── .env                            ← Bot configuration (token, model, etc.)
├── .daemon_offset                  ← Persists last Telegram update_id
├── .chat_histories.json            ← Per-chat conversation history
├── .weather_alert_state.json       ← Weather alert state tracking
└── scripts/
    ├── pip_telegram_daemon.py      ← Main real-time daemon
    ├── telegram_api.py             ← CLI helper tool
    ├── weather_alert.py            ← Harsh weather alert script
    ├── weather_report.py           ← Daily weather report script
    ├── news_alert.py               ← Daily news digest script
    └── security_reminder.py        ← Security reminder script
```

---

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Choose a name and username for your bot
4. BotFather will give you a **Bot Token** — save it securely

> [!IMPORTANT]
> Never share your bot token publicly. Anyone with the token can control your bot.

---

## Step 2: Get Your Chat ID

1. Start a conversation with your new bot (send any message)
2. Visit the following URL in your browser (replace `<TOKEN>` with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Find `"chat":{"id": 123456789}` in the JSON response
4. Note your **Chat ID** — you'll need it for the configuration

---

## Step 3: Configure Environment Variables

### Primary Configuration — `data/.env`

The main Agent Zero environment file (`data/.env`) is loaded by the container via `docker-compose.yml`. Add your Telegram bot token here:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

### Bot-Specific Configuration — `usr/workdir/telegram/.env`

This file contains all Telegram daemon settings. Create or edit it at `usr/workdir/telegram/.env`:

```env
# ─── Required ───────────────────────────────────────────
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# ─── LLM API (OpenAI-compatible endpoint) ───────────────
OPENAI_API_BASE=https://your-api-endpoint/v1
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# ─── Optional: Restrict access to specific users ────────
# Comma-separated Telegram chat IDs. Leave empty to allow all.
TELEGRAM_ALLOWED_IDS=YOUR_CHAT_ID_HERE

# ─── Model & Behaviour ──────────────────────────────────
TELEGRAM_MODEL=claude-sonnet-4-6
TELEGRAM_MAX_HISTORY=40
TELEGRAM_MAX_TOOL_ITER=8

# ─── System Prompt (customize the bot's persona) ────────
TELEGRAM_SYSTEM_PROMPT=You are a highly capable AI assistant running inside an Agent Zero Docker container. You can execute shell commands when needed. Be concise but thorough. Use markdown formatting when helpful.

# ─── Alert Scripts ──────────────────────────────────────
# Used by weather_alert.py and news_alert.py
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
```

### Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | — | Bot token from @BotFather |
| `OPENAI_API_KEY` | ✅ Yes | — | API key for your LLM provider |
| `OPENAI_API_BASE` | ✅ Yes | — | Base URL for OpenAI-compatible API |
| `TELEGRAM_MODEL` | No | `claude-sonnet-4-6` | LLM model to use for responses |
| `TELEGRAM_MAX_HISTORY` | No | `40` | Max messages kept per conversation |
| `TELEGRAM_MAX_TOOL_ITER` | No | `8` | Max shell tool call iterations per response |
| `TELEGRAM_ALLOWED_IDS` | No | *(all)* | Comma-separated chat IDs to whitelist |
| `TELEGRAM_CHAT_ID` | No | — | Default chat ID for alert scripts |
| `TELEGRAM_SYSTEM_PROMPT` | No | *(built-in)* | Custom system prompt for the bot |

---

## Step 4: Docker Compose Setup

The `docker-compose.yml` mounts the `data/` and `usr/` directories into the container and loads `data/.env` automatically:

```yaml
services:
  agent0:
    image: agent0ai/agent-zero:latest
    container_name: agent0
    restart: unless-stopped
    ports:
      - "8443:80"
    volumes:
      - ./data:/a0/data
      - ./usr:/a0/usr
    env_file:
      - ./data/.env
```

> [!TIP]
> The daemon reads both `data/.env` (for `OPENAI_API_KEY`) and `usr/workdir/telegram/.env` (for bot-specific settings). Values in `telegram/.env` take priority.

---

## Step 5: Start the Daemon

### Using supervisord (Recommended for persistence)

The daemon is managed by `supervisord` inside the container. Add the following section to your `supervisord.conf`:

```ini
[program:telegram_daemon]
command=/opt/venv/bin/python3 /a0/usr/workdir/telegram/start_daemon.py
directory=/a0/usr/workdir/telegram
autostart=true
autorestart=true
stderr_logfile=/tmp/telegram_daemon.log
stdout_logfile=/tmp/telegram_daemon.log
```

To persist the supervisord config across container rebuilds, copy it to the host:

```bash
# Copy current config from container to host
docker cp agent0:/etc/supervisor/conf.d/supervisord.conf ./supervisord.conf

# Then mount it in docker-compose.yml:
# volumes:
#   - ./supervisord.conf:/etc/supervisor/conf.d/supervisord.conf
```

### Manual Start

```bash
# Enter the container
docker exec -it agent0 bash

# Start the daemon manually
cd /a0/usr/workdir/telegram
/opt/venv/bin/python3 start_daemon.py
```

---

## Daemon Management

All daemon management is done via `supervisorctl` inside the container:

```bash
# Check status
supervisorctl status telegram_daemon

# Start / stop / restart
supervisorctl start telegram_daemon
supervisorctl stop telegram_daemon
supervisorctl restart telegram_daemon

# View live logs
tail -f /tmp/telegram_daemon.log

# Reload config after editing supervisord.conf
supervisorctl reread && supervisorctl update
```

---

## CLI Helper Tool

The `telegram_api.py` script provides a command-line interface for managing the bot:

```bash
PY=/opt/venv/bin/python3
SCRIPTS=/a0/usr/workdir/telegram/scripts

# Show bot info (username, ID)
$PY $SCRIPTS/telegram_api.py status

# Send a message to a chat
$PY $SCRIPTS/telegram_api.py send <chat_id> Hello from Agent Zero!

# Show pending (unprocessed) updates
$PY $SCRIPTS/telegram_api.py poll

# Clear conversation history for a user
$PY $SCRIPTS/telegram_api.py clear <chat_id>

# Tail the daemon log (last 50 lines)
$PY $SCRIPTS/telegram_api.py log
```

---

## Bot Commands

Users can send these commands directly in Telegram:

| Command | Description |
|---|---|
| `/start` | Welcome message and instructions |
| `/help` | Show available commands |
| `/clear` | Reset your conversation history |
| `/status` | Show container system status (uptime, disk, memory) |

---

## Automated Alert Scripts

The `scripts/` directory contains scheduled scripts that send proactive notifications to Telegram.

### Weather Alert (`weather_alert.py`)

Monitors Calgary weather every 30 minutes and sends alerts when harsh conditions are detected (and a de-escalation when they clear).

**Triggers alerts for:**
- Sustained wind ≥ 60 km/h
- Gusts ≥ 70 km/h
- Feels-like temperature ≤ −20°C or ≥ 36°C
- Heavy precipitation ≥ 5 mm in next 6 hours
- Severe WMO weather codes (heavy snow, thunderstorms, hail, etc.)

**Required env vars:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**Cron example (inside container):**
```bash
*/30 * * * * /opt/venv/bin/python3 /a0/usr/workdir/telegram/scripts/weather_alert.py
```

### News Digest (`news_alert.py`)

Sends a daily morning news digest at 8:00 AM Calgary time, pulling headlines from:
- 🌍 World News (BBC, The Guardian)
- 💰 Business (CNBC, The Guardian)
- 🔬 Technology (TechCrunch, Ars Technica)
- 🏥 Health (The Guardian, NPR)
- 🇨🇦 Canada (Global News, CBC)

**Required env vars:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**Cron example (inside container):**
```bash
0 15 * * * /opt/venv/bin/python3 /a0/usr/workdir/telegram/scripts/news_alert.py
# (15:00 UTC = 8:00 AM MST / 9:00 AM MDT)
```

---

## Data Persistence

All bot data is stored in the volume-mounted `usr/workdir/telegram/` directory and persists across container rebuilds:

| File | Purpose |
|---|---|
| `.env` | Bot configuration |
| `.daemon_offset` | Last processed Telegram `update_id` (prevents duplicate messages) |
| `.chat_histories.json` | Per-chat conversation history (JSON) |
| `.weather_alert_state.json` | Tracks whether a weather alert is currently active |

---

## Troubleshooting

### Bot not responding

1. Check the daemon is running:
   ```bash
   supervisorctl status telegram_daemon
   ```
2. Check the logs for errors:
   ```bash
   tail -f /tmp/telegram_daemon.log
   ```
3. Verify the bot token is valid:
   ```bash
   $PY $SCRIPTS/telegram_api.py status
   ```

### `TELEGRAM_BOT_TOKEN not set` error

- Ensure `TELEGRAM_BOT_TOKEN` is set in `usr/workdir/telegram/.env` or `data/.env`
- Verify the file is readable inside the container:
  ```bash
  docker exec agent0 cat /a0/usr/workdir/telegram/.env
  ```

### `OPENAI_API_KEY not set` error

- The daemon requires `OPENAI_API_KEY` to call the LLM
- Set it in `data/.env` (loaded automatically by Docker) or in `usr/workdir/telegram/.env`

### Messages not being received

- Check if `TELEGRAM_ALLOWED_IDS` is set — if so, your chat ID must be in the list
- Use the CLI helper to check pending updates:
  ```bash
  $PY $SCRIPTS/telegram_api.py poll
  ```
- Verify the offset file isn't stale:
  ```bash
  cat /a0/usr/workdir/telegram/.daemon_offset
  ```

### Daemon crashes on startup

- Check Python dependencies are installed (`requests`, `openai`):
  ```bash
  docker exec agent0 /opt/venv/bin/pip list | grep -E "requests|openai"
  ```
- Review the full log:
  ```bash
  docker exec agent0 cat /tmp/telegram_daemon.log
  ```

---

## Security Considerations

- **Restrict access** — always set `TELEGRAM_ALLOWED_IDS` to your own chat ID(s) to prevent unauthorized use
- **Protect your token** — never commit `data/.env` or `usr/workdir/telegram/.env` to version control (both are in `.gitignore`)
- **Shell access** — the bot can execute shell commands inside the container; only share access with trusted users
- **API keys** — store all API keys in `.env` files, never hardcode them in scripts

---

## Related Documentation

- [MCP Setup](mcp-setup.md) — Connecting external MCP servers to Agent Zero
- [Advanced MCP Configuration](../developer/mcp-configuration.md) — Detailed MCP configuration reference
- [Notifications](../developer/notifications.md) — Agent Zero's built-in notification system
- [Tasks & Scheduling](usage.md#tasks--scheduling) — Scheduling automated tasks in Agent Zero
