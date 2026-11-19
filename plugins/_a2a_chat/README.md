# A2A Chat

Provides the `a2a_chat` tool, which communicates with remote FastA2A-compatible agents. Conversation context is preserved automatically per `agent_url`; pass `reset: true` to start a fresh conversation with the same agent.

Unauthenticated agents work without extra configuration. To connect to a protected Agent Zero peer, use its token-bearing connection URL from **Settings → A2A → Connection URL**. Credentials are never copied automatically from the ambient `A2A_TOKEN` environment variable to a model-selected destination.
