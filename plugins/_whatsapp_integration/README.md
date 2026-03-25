# WhatsApp Integration Plugin

Communicate with Agent Zero via WhatsApp using a Baileys-based Node.js bridge.

## Requirements

- **Node.js** (v18+) installed on the system
- A WhatsApp account on a phone (for QR code pairing)

## Setup

1. Enable the plugin in Settings > External > WhatsApp Integration
2. Configure allowed phone numbers (optional)
3. Start Agent Zero — the bridge will auto-start and display a QR code in the logs
4. Scan the QR code with WhatsApp on your phone
5. Send a message from an allowed number to start a chat

The WhatsApp session persists across restarts in `usr/whatsapp/sessions/`. No re-pairing needed unless you manually unlink the device from WhatsApp.

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable bridge and polling | `false` |
| `mode` | `dedicated` (separate number) or `self-chat` (personal number) | `dedicated` |
| `bridge_port` | Local HTTP port for bridge | `3100` |
| `poll_interval_seconds` | Poll frequency (min 2) | `3` |
| `allowed_users` | Phone numbers without + prefix | `[]` (all) |
| `project` | Activate project for WA chats | `""` |
| `agent_instructions` | Extra agent instructions | `""` |

## How It Works

1. The bridge connects to WhatsApp via Baileys and exposes HTTP endpoints on localhost
2. The plugin polls the bridge for new messages every few seconds
3. Incoming messages are routed to existing chats by WhatsApp chat ID or new chats are created
4. Agent responses are sent back via the bridge as WhatsApp messages
5. Media (images, documents) is supported in both directions

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
