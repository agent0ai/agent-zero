# OAuth Connections

Generic local OAuth bridge for Agent Zero.

Tokens in `auth.json` are password-equivalent credentials. Keep this plugin on trusted local machines only. Do not configure `auth_file_path` to share a rotating refresh-token file with Codex CLI or another client.

The settings UI groups providers as account-backed connections. More than one account provider can be connected at the same time, and the Main/Utility model slots can choose models from any connected OAuth provider.

Each model slot has its own provider selector. The selector lists connected OAuth accounts only, so Main and Utility can use different account-backed providers when more than one account is connected.

OAuth-backed model providers do not require users to enter API keys. Agent Zero supplies a local dummy key only at runtime after the selected account provider is connected, so unconnected providers stay blank in API-key surfaces.

## Providers

### Codex/ChatGPT (`codex_oauth`)

- Uses the existing Codex device-code flow.
- Writes Codex-compatible credentials to an Agent Zero-owned `auth.json` file.
- Refreshes local tokens when needed.
- Exposes the local OpenAI-compatible wrapper at `/oauth/codex/v1`.

### GitHub Copilot (`github_copilot_oauth`)

- Uses GitHub's OAuth device flow.
- Exchanges the GitHub access token for a Copilot API token.
- Stores credentials under `usr/plugins/_oauth/github_copilot/auth.json`.

### Google Cloud Gemini (`gemini_api_oauth`)

- Uses Google's OAuth authorization-code flow with PKCE.
- Requires a user-provided Google Cloud OAuth client with the Generative Language API enabled.
- Proxies the official Gemini OpenAI-compatible endpoint at `/oauth/gemini-api/v1`.
- Stores credentials under `usr/plugins/_oauth/gemini_api/auth.json`.
- Uses Gemini API billing and quotas. It does not use Antigravity, Gemini Code Assist, Gemini CLI, Google AI Pro, or Google AI Ultra subscription quota.

### xAI Grok (`xai_grok_oauth`)

- Uses xAI's browser-based PKCE flow.
- Supports manual callback paste for remote hosts where the browser cannot reach the local callback directly.
- Stores credentials under `usr/plugins/_oauth/xai_grok/auth.json`.

## Usage Plan Metadata

The status API exposes `usage_plan_catalog` for subscription and billing context. It covers only connectable providers: Codex, GitHub Copilot, Google Cloud Gemini, and xAI Grok.

The same status response also includes `oauth_accounts`, a compact summary used by the settings modal, welcome discovery card, and onboarding wizard. Keep that summary provider-registry driven so new OAuth providers appear consistently across those surfaces.

## Remote xAI Callback

When Agent Zero is running on a remote host, the browser may complete the xAI authorization step somewhere other than the machine serving the local callback route. In that case, paste the callback value into the xAI card.

The xAI card accepts any of these formats:

- Full callback URL.
- Query string such as `?code=...&state=...`.
- Bare authorization code.
