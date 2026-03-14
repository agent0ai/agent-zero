### a2a_chat

This tool lets Agent Jumbo chat with any other FastA2A-compatible agent.
It automatically keeps conversation **context** (so each subsequent call
continues the same dialogue) and supports optional file attachments.

#### What the tool can do

* Start a brand-new conversation with a remote agent.
* Continue an existing conversation transparently (context handled for you).
* Send text plus optional file URIs (images, docs, etc.).
* Receive the assistant’s reply as plain text.

#### Arguments

* `agent_url` (string, required) – Base URL of the *remote* agent.
  • Accepts `host:port`, `http://host:port`, or full path ending in `/a2a`.
* `message` (string, required) – The text you want to send.
* `attachments` (list[string], optional) – URIs pointing to files you want
  to send along with the message (can be http(s):// or file path).
* `reset` (boolean, optional) – Set to `true` to start a **new** conversation
  with the same `agent_url` (clears stored context). Default `false`.

> Leave **context_id** out – the tool handles it internally.

#### Usage – first message

##### Request

```json
{
  "thoughts": [
    "I want to ask the weather-bot for today’s forecast."
  ],
  "headline": "Ask remote agent (weather-bot)",
  "tool_name": "a2a_chat",
  "tool_args": {
    "agent_url": "http://weather.example.com:8000/a2a",
    "message": "Hello! What’s the forecast for Berlin today?",
    "attachments": [],
    "reset": false
  }
}
```

##### Response (assistant-side)

```plaintext
☀️ It will be sunny with a high of 22 °C.
```

#### Usage – follow-up (context automatically preserved)

##### Request

```json
{
  "thoughts": [
    "Need tomorrow’s forecast too."
  ],
  "headline": "Follow-up question",
  "tool_name": "a2a_chat",
  "tool_args": {
    "agent_url": "http://weather.example.com:8000/a2a",
    "message": "And tomorrow?",
    "attachments": [],
    "reset": false
  }
}
```

##### Response

```plaintext
🌦️ Partly cloudy with showers, high 18 °C.
```

#### Notes

1. **New conversation** – omit previous `agent_url` or use a *different* URL.
2. **Attachments** – supply absolute URIs ("http://…", "file:/…").
3. The tool stores session IDs per `agent_url` inside the current
   `AgentContext` – no manual handling required.
4. Use `"reset": true` to forget previous context and start a new chat.
5. The remote agent must implement FastA2A v0.2+ protocol.
