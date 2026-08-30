# Token Compression Protocol (TCP)

This document defines an easy-to-implement protocol for compressing LLM prompts
and responses while preserving the original encoding and a persistent context.
It is designed to run as a local TCP service and integrate cleanly with browser
extensions via a lightweight native-host bridge.

## Goals

- Encode user prompts in base64.
- Accept model responses in base54.
- Decode responses back into the original encoding (utf-8, ascii, etc).
- Maintain a persistent, base64-rendered context across conversations.
- Provide token savings diagnostics via `**show savings**` and `**show total**`.
- Keep the wire format simple: newline-delimited JSON over TCP.

## Server Overview

The TCP server lives at:

- Module: `python/helpers/token_compression_protocol.py`
- Default host: `127.0.0.1`
- Default port: `7543`
- Context dataset: `memory/token_compression_context.json`

Run it locally:

```bash
python3 /workspace/python/helpers/token_compression_protocol.py
```

The server accepts one JSON object per line and returns one JSON object per line.

## Base54 Alphabet

The response payload uses base54 with this alphabet:

```
123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstyz
```

This avoids ambiguous characters (0, O, I, l) and a few lower-case letters to
hit an even base of 54.

## Transport Protocol (TCP)

Each request is a single JSON line terminated by `\n` (LF). Each response is
also a single JSON line terminated by `\n`.

### Common Envelope

All responses include:

```json
{
  "ok": true,
  "result": { ... }
}
```

Errors are returned as:

```json
{
  "ok": false,
  "error": "error_code",
  "detail": "optional detail"
}
```

### Actions

#### `prompt`

Encode a user prompt to base64, update context, and return the new context.

Request:

```json
{
  "action": "prompt",
  "conversation_id": "optional",
  "text": "user prompt text",
  "encoding": "utf-8",
  "language": "en"
}
```

Notes:
- If `conversation_id` is omitted, the server generates one.
- `encoding` and `language` are stored and reused for the conversation.
- If `**show savings**` or `**show total**` is present in `text`, it is stripped
  before encoding and applied to the next `response`.

Response:

```json
{
  "ok": true,
  "result": {
    "conversation_id": "uuid",
    "encoding": "utf-8",
    "language": "en",
    "encoded_prompt_b64": "SGVsbG8=",
    "context_b64": "dXNlcjogSGVsbG8=",
    "context_tokens": { "raw": 2, "encoded": 2, "saved": 0 },
    "prompt_tokens": { "raw": 2, "encoded": 2, "saved": 0 },
    "savings_request": { "show_savings": true, "show_total": false }
  }
}
```

#### `response`

Submit a base54 response payload from the model, decode it, and update context.

Request:

```json
{
  "action": "response",
  "conversation_id": "uuid",
  "payload_b54": "base54response"
}
```

Response (base form):

```json
{
  "ok": true,
  "result": {
    "conversation_id": "uuid",
    "encoding": "utf-8",
    "language": "en",
    "response_b54": "base54response",
    "decoded_text": "model response",
    "response_tokens": { "raw": 4, "encoded": 3, "saved": 1 },
    "context_b64": "dXNlcjogSGVsbG8K...==",
    "context_tokens": { "raw": 6, "encoded": 5, "saved": 1 }
  }
}
```

If `**show savings**` or `**show total**` was set in the last prompt, the
response includes a `savings` object, `tagline`, and `decoded_text_with_tagline`:

```json
{
  "ok": true,
  "result": {
    "...": "...",
    "tagline": "Token savings (prompt/response/context/combined): 0/1/1/2.",
    "decoded_text_with_tagline": "model response\nToken savings ...",
    "savings": {
      "prompt": { "raw": 2, "encoded": 2, "saved": 0 },
      "response": { "raw": 4, "encoded": 3, "saved": 1 },
      "context": { "raw": 6, "encoded": 5, "saved": 1 },
      "combined_saved": 2,
      "totals": {
        "prompt": { "raw": 10, "encoded": 10, "saved": 0 },
        "response": { "raw": 20, "encoded": 18, "saved": 2 },
        "context": { "raw": 30, "encoded": 25, "saved": 5 },
        "combined_saved": 7
      }
    }
  }
}
```

#### `context_get`

Fetch the current base64 context for a conversation (or all conversations).

Request:

```json
{
  "action": "context_get",
  "conversation_id": "uuid"
}
```

Response:

```json
{
  "ok": true,
  "result": {
    "conversation_id": "uuid",
    "context_b64": "dXNlcjogSGVsbG8=",
    "encoding": "utf-8",
    "language": "en",
    "context_tokens": { "raw": 2, "encoded": 2, "saved": 0 }
  }
}
```

#### `context_reset`

Delete a conversation from the dataset.

Request:

```json
{
  "action": "context_reset",
  "conversation_id": "uuid"
}
```

#### `ping`

Request:

```json
{ "action": "ping" }
```

Response:

```json
{ "ok": true, "result": { "message": "pong" } }
```

## Browser Extension Integration

Browsers cannot open raw TCP sockets directly. The easiest integration pattern
is a lightweight local bridge that the extension can message.

### Option A: Native Messaging Host (Recommended)

Use the browser's native messaging API to launch a small helper process that
connects to the TCP server and forwards JSON lines.

Flow:

1. Extension sends a JSON message to the native host.
2. Native host writes the JSON line to `127.0.0.1:7543`.
3. Native host reads the JSON response line and returns it to the extension.

Advantages:
- Works in Chrome and Firefox.
- No CORS or HTTP server needed.
- Minimal bridging logic (just pass-through JSON lines).

Native host pseudo-code:

```python
import json, socket, sys

def tcp_exchange(payload):
    data = json.dumps(payload).encode("utf-8") + b"\n"
    with socket.create_connection(("127.0.0.1", 7543)) as sock:
        sock.sendall(data)
        response = sock.recv(1024 * 1024).split(b"\n", 1)[0]
    return json.loads(response.decode("utf-8"))
```

### Option B: Local HTTP/WS Bridge

If you prefer `fetch` or WebSocket from the extension, run a local bridge that
translates HTTP/WS into the TCP line protocol:

- `POST /tcp` -> send JSON line over TCP, return JSON response
- `GET /context/:conversation_id` -> map to `context_get`

This is a thin shim and keeps the TCP protocol unchanged.

## Example End-to-End Session

1) Encode prompt:

```json
{"action":"prompt","text":"Summarize this. **show savings**","encoding":"utf-8","language":"en"}
```

2) Send `encoded_prompt_b64` to the model (outside TCP server).

3) Encode model output to base54 (client-side), then send:

```json
{"action":"response","conversation_id":"...","payload_b54":"..."}
```

4) Receive decoded text plus savings tagline.

## Data Persistence

Context is stored in `memory/token_compression_context.json`. The server keeps a
background thread that refreshes and persists the context every few seconds.

## Security Notes

- Run the TCP server on `127.0.0.1` only.
- Treat `context_b64` as sensitive; it contains full conversation history.
- Use the native messaging approach if you need strict extension isolation.

## Troubleshooting

- `missing_payload_b54`: Ensure you send base54 for responses, not base64.
- `invalid_base54`: Check the alphabet and strip any non-base54 characters.
- `unknown_conversation_id`: Use the `conversation_id` returned by `prompt`.
