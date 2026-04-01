# WhatsApp Integration Plugin

Communicate with Agent Zero via WhatsApp using a Baileys-based Node.js bridge.

## Requirements

- **Node.js** (v18+) and npm installed on the system
- A WhatsApp account on a phone (for QR code pairing)

## Setup

### Install bridge dependencies

```bash
cd plugins/_whatsapp_integration/whatsapp-bridge
npm install --production
```

Dependencies are auto-installed on first bridge start if missing.

### Configure and pair

1. Enable the plugin in Settings > External > WhatsApp Integration
2. Configure allowed phone numbers
3. Click Show QR Code and scan with WhatsApp on your phone
4. Send a message from an allowed number to start a chat

The WhatsApp session persists across restarts in `tmp/whatsapp/session/`. No re-pairing needed unless you disconnect via settings.
Be careful: if you use your personal number and leave `allowed_numbers` open, other people could misuse your Agent Zero.

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable bridge and polling | `false` |
| `mode` | `self-chat` (personal number) or `dedicated` (separate number) | `self-chat` |
| `allow_group` | Respond in group chats when mentioned or replied to | `false` |
| `bridge_port` | Local HTTP port for bridge | `3100` |
| `poll_interval_seconds` | Poll frequency (min 2) | `3` |
| `allowed_numbers` | Phone numbers without + prefix | `[]` (all) |
| `project` | Activate project for WA chats | `""` |
| `agent_instructions` | Extra agent instructions | `""` |

## How It Works

1. The bridge connects to WhatsApp via Baileys and exposes HTTP endpoints on localhost
2. In personal-number mode, you can message your own WhatsApp number to talk to the agent, and the agent can also handle messages that other people send to that number
3. The plugin polls the bridge for new messages every few seconds
4. Incoming messages are routed to existing chats by WhatsApp chat ID or new chats are created
5. Agent responses are sent back via the bridge as WhatsApp messages
6. Media (images, documents) is supported in both directions

## Architecture

```
WhatsApp Phone
    ↕ (WhatsApp protocol via Baileys)
whatsapp-bridge/bridge.js  (Node.js subprocess)
    ↕ (HTTP API on localhost)
Python helpers (wa_client, handler, bridge_manager)
    ↕ (Framework extensions)
Agent Zero
```
