---
name: a2a-chat
description: Message another Agent Zero or FastA2A-compatible agent at its connection URL and continue the same remote conversation on follow-up.
triggers: [agent-to-agent, A2A, another Agent Zero, remote agent]
metadata:
  tool:
    name: a2a_chat
    parameters:
      type: object
      required: [agent_url, message]
      properties:
        agent_url: {type: string}
        message: {type: string}
        attachments: {type: array, items: {type: string}}
        reset: {type: boolean}
      additionalProperties: true
---

# A2A Chat

Use `a2a_chat` to send a message to a remote agent. Pass its connection URL as `agent_url`. For a protected Agent Zero peer, use the connection URL it provides under Settings → A2A.

~~~json
{
  "tool_name": "a2a_chat",
  "tool_args": {
    "agent_url": "https://peer.example.invalid/a2a",
    "message": "What is the current status of the handoff?"
  }
}
~~~

- Reuse the same `agent_url` for follow-ups. The callable manages the remote context ID for this chat.
- Set `reset: true` only when starting a fresh conversation with that peer.
- Use `attachments` for optional absolute URIs or paths to send with the message.
