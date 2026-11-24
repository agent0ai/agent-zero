# A2A Chat

The `a2a-chat` skill makes `a2a_chat` available on demand for communication with remote FastA2A-compatible agents. Follow-ups reuse the conversation for the same `agent_url`. Pass `reset: true` to start a fresh conversation with that agent.

Unauthenticated agents work without extra configuration. To connect to a protected Agent Zero peer, use its token-bearing connection URL from **Settings → A2A → Connection URL**. Credentials are never copied automatically from the ambient `A2A_TOKEN` environment variable to a model-selected destination.
