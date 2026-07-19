# OAuth Connections

Generic local OAuth bridge for Agent Zero.

The first provider is `Codex/ChatGPT Account`:

- signs in with OpenAI's Codex device-code flow
- writes Codex-compatible `auth.json` credentials
- refreshes local tokens when needed
- exposes a loopback OpenAI-compatible wrapper at `/oauth/codex/v1`

Tokens in `auth.json` are password-equivalent credentials. Keep this plugin on trusted local machines only.
