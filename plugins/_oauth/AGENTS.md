# OAuth Plugin DOX

## Purpose

- Own account-backed OAuth model-provider connections for Agent Zero.
- Provide local OpenAI-compatible proxy endpoints for connectable account providers.
- Keep provider-specific OAuth behavior inside this plugin, not in core model code.
- Preserve Codex/ChatGPT compatibility while allowing additional providers through the provider registry.

## Ownership

- `plugin.yaml`, `default_config.yaml`, and `README.md` own the plugin manifest, settings defaults, and user-facing connection notes.
- `conf/model_providers.yaml` owns OAuth-backed model provider definitions and their `api_key_mode: oauth` metadata.
- `api/` owns provider-aware settings modal endpoints such as status, login start, polling, manual callback, models, and disconnect.
- `helpers/providers/` owns provider implementations, provider metadata, registry wiring, token storage helpers, and provider-specific endpoint validation.
- `helpers/summary.py` owns the shared provider-status/account summary shape consumed by the status API, discovery cards, onboarding, and OAuth settings UI.
- `helpers/routes.py` owns local OAuth callback and OpenAI-compatible proxy routes mounted by the route bootstrap extension.
- `webui/config.html` and `webui/oauth-config-store.js` own the OAuth Connections settings UI.
- `extensions/python/_functions/models/get_api_key/end/` owns the dummy API-key extension used by OAuth model providers.
- `tests/test_oauth_*.py` own provider contract, security, static UI, and compatibility regressions.

## Local Contracts

- Core model code such as `models.py` must stay provider-agnostic. Do not add Codex, GitHub Copilot, Gemini, xAI, or other OAuth provider knowledge outside plugin-owned config or plugin hooks.
- Add OAuth model providers in `_oauth/conf/model_providers.yaml`, not `_model_config/provider_metadata.yaml`.
- Provider cards and model slot actions must be driven by backend provider status. Do not reintroduce hardcoded frontend provider lists or fallback provider catalogs.
- OAuth account surfaces in settings, discovery, and onboarding must use the provider registry/status summary rather than Codex-only frontend state.
- OAuth settings pending-auth controls such as device codes, manual callback input, and provider setup fields must render inline under the relevant provider row, not as a detached section below all providers.
- OAuth device-code polling must honor provider `interval`, `expires_at`, and `slow_down` updates; do not poll immediately or keep a stale fixed interval after a provider asks the client to slow down.
- OAuth settings model slots must keep provider choice editable per slot, list only connected OAuth account providers, and persist the selected provider IDs into `chat_model.provider` and `utility_model.provider`.
- When exactly one OAuth provider is connected, use it as an unsaved default only for empty slots or slots already using that provider. A different saved provider must keep the explicit `Choose connected provider` prompt until the user opts into the switch.
- OAuth provider rows show a status pill only for connected accounts; model catalogs open from the model-slot field or its embedded magnifier, not from provider-row model-check actions.
- OAuth model-slot fields must match `_model_config` input and below-field dropdown geometry while opening the catalog when the field is clicked.
- OAuth settings must dispatch `model-setup-changed` when a provider connection completes; provider defaults may be inferred from one connected account, but model-name selection remains explicit.
- `helpers/providers/registry.py` is the source of truth for connectable OAuth providers.
- The models API must preserve the legacy plain `models` slug list and may add `model_metadata` entries for richer provider catalogs.
- OAuth provider config must not expose the dummy `oauth` API key in `conf/model_providers.yaml`; the dummy key is a runtime-only shim supplied by the `get_api_key` extension after the account provider reports connected.
- Usage-plan metadata belongs only to connectable providers. Do not add metadata-only subscription families for providers this plugin cannot connect.
- API handlers should remain provider-aware. Missing or blank `provider_id` defaults to Codex only for existing backward compatibility; falsey non-string IDs must not silently default.
- Codex success contracts must preserve legacy fields such as `account_id` while allowing newer fields such as `account_label`.
- Do not modify Codex chat-to-responses multimodal conversion without preserving the image/text regression coverage in `tests/test_oauth_codex.py`.
- Token files are password-equivalent credentials. Store them under plugin-owned `usr/plugins/_oauth/<provider>/auth.json` paths with private permissions, and do not share rotating refresh-token files with external CLIs.
- Stored upstream base URLs and OAuth token endpoints must be validated against provider-owned allowlists before sending bearer or refresh tokens.
- Browser callback providers must support manual callback paste when the browser cannot reach the local callback route.
- Local proxy routes must remain loopback or token protected and must not add broad CORS access.
- Codex Responses proxy requests must include Codex client metadata and compatibility headers such as `client_metadata`, `x-codex-installation-id`, `originator`, `session-id`, and `thread-id`, and must forward `input` as a list for upstream Codex compatibility.

## Work Guidance

- When adding a connectable provider, add the provider class, registry entry, model-provider config, default settings, route registration, UI support when needed, tests, and README/DOX updates together.
- Keep provider classes explicit about their auth endpoints, scopes, refresh behavior, and safe API hosts.
- Use shared helpers only for duplicated mechanics such as callback parsing, attempt lookup, model-list parsing, and JSON/error helpers.
- Keep provider policy visible in each provider module; avoid abstracting away endpoint validation or billing/quota caveats.
- Prefer plugin-local imports such as `plugins._oauth.helpers...` for bundled plugin code.
- Keep `_oauth` account providers separate from API-key providers in core configuration.
- Keep the OAuth settings page account-backed only. API-key and local provider setup belongs in model configuration and onboarding.
- Treat Gemini API OAuth as a Google Cloud OAuth-client flow. Do not conflate it with Antigravity, Gemini Code Assist, Gemini CLI, Google AI Pro, or Google AI Ultra subscription quota.
- Treat Claude Code subscription auth and Antigravity product auth as non-connectable unless their vendors provide an explicit third-party provider contract.
- Keep user-facing errors safe: report setup or tier restrictions without exposing tokens, callback secrets, or raw auth payloads.

## Verification

- Run `pytest tests/test_oauth_*.py` after backend provider, route, token, or UI contract changes.
- Run `pytest tests/test_plugin_scan_prompt.py` after plugin structure, extension, or docs changes.
- Run onboarding or model-config tests when provider metadata, `api_key_mode`, or model-provider config changes.
- Run `git diff --check` before committing.
- For security-sensitive changes, include regressions that prove bearer tokens are not sent to malicious stored endpoints.
- For Codex changes, include `tests/test_oauth_codex.py` and preserve `account_id` and multimodal image bridge regressions.

## Child DOX Index

No child DOX files.
