from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_oauth_settings_exposes_provider_cards_and_model_slots():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    assert "providerCards" in config_html + store_js
    assert "OAuth Connections" in config_html + store_js
    assert "OAUTH_PROVIDERS" not in store_js
    assert "PROVIDER_FALLBACKS" not in store_js
    assert "Connected accounts" not in config_html
    assert "Choose your models" in config_html
    assert "Main model" in store_js
    assert "Utility model" in store_js
    assert "provider_map" in store_js
    assert "<h3>Accounts</h3>" not in config_html
    assert "oauth-plan-catalog" not in config_html
    assert "oauth-model-provider-field" in config_html
    assert "slotProviderChoices(slot.key)" in config_html
    assert "<span>Provider</span>" not in config_html
    assert ':aria-label="`${slot.title} provider`"' in config_html
    assert "connectedProviderCards().length" in config_html
    assert "useProviderForSlot(slot.key, $event.target.value)" in config_html
    assert ":value=\"$store.oauthConfig.slotCanUseModels(slot.key) ? $store.oauthConfig.modelSlot(slot.key).provider : ''\"" in config_html
    assert "slotCanUseModels(slot.key)" in config_html
    assert "<span>Account</span>" not in config_html
    assert "oauth-connected-panel" not in config_html
    assert "oauth-provider-usage" in config_html
    assert "usageWindows(card.provider_id)" in config_html
    assert "connectedUsageWindows()" not in config_html
    assert "Agent Zero models" not in config_html
    assert "Usage plans" not in config_html
    assert "usagePlanEntries" in store_js
    assert "usage_plan_catalog" in (PROJECT_ROOT / "plugins/_oauth/helpers/summary.py").read_text(encoding="utf-8")
    assert "copyMainToUtility" in config_html + store_js
    assert "connectedSummaryLabel()" not in config_html


def test_oauth_settings_exposes_provider_specific_controls_and_generic_copy():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    assert "Check models" not in config_html
    assert "card.connected ? 'Connected' : 'Available'" not in config_html
    assert '<span class="oauth-account-state connected" x-show="card.connected">Connected</span>' in config_html
    assert "Select account-backed models used by the Main model and Utility model slots." not in config_html
    assert "Primary model for chat, reasoning, and browser tasks." not in config_html + store_js
    assert "Background model for summaries, memory, and prompt preparation." not in config_html + store_js
    assert '@click="$store.oauthConfig.openModelDropdown(slot.key, $el)"' in config_html
    assert "top: calc(100% + 4px);" in config_html
    assert "enterprise_domain" in config_html + store_js
    assert "manualCallback" in config_html + store_js
    assert "Paste callback URL, query string, or code" in config_html + store_js
    assert "supports_enterprise_domain" in config_html + store_js
    assert "supports_manual_callback" in config_html + store_js
    assert "supports_oauth_client_config" in config_html + store_js
    assert "supports_quota_project" in config_html + store_js
    assert "OAuth client ID" in config_html
    assert "quota_project_id" in config_html + store_js
    assert "providerDetailOpen(card.provider_id)" in config_html + store_js
    assert "providerDevice(card.provider_id)?.user_code" in config_html
    assert "submitManualCallback(card.provider_id)" in config_html
    assert "cancelConnect(card.provider_id)" in config_html
    assert "selectedProvider()" not in config_html
    assert "oauth-auth-attempt" in config_html
    assert "oauth-provider-row-detail" in config_html
    assert "oauth-provider-detail" not in config_html
    assert "oauth-detail-metrics" not in config_html
    assert "Codex/ChatGPT Account" not in config_html + store_js
    assert "activeModelsDescription()" in config_html + store_js
    assert "activeProviderModels()" in config_html + store_js
    assert "Available models from Codex account" not in config_html
    assert "disconnectProvider(card.provider_id)" in config_html
    assert "disconnectProvider($store.oauthConfig.selectedProviderId)" not in config_html
    assert "color: #35d07f;" not in config_html
    assert ".oauth .oauth-provider-row.connected .oauth-provider-row-copy span" in config_html
    assert ".oauth .oauth-provider-row.connected .oauth-usage-head strong" in config_html
    assert ".oauth .oauth-provider-row.connected .oauth-usage-window p" in config_html
    assert "var(--color-text-secondary, rgba(255, 255, 255, .72))" in config_html


def test_oauth_connect_buttons_disable_during_any_provider_connection():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    assert "providerPrimaryDisabled" in config_html + store_js
    assert "this.connectingProvider || this.disconnectingProvider" in store_js
    assert ':disabled="Boolean($store.oauthConfig.connectingProvider) || $store.oauthConfig.disconnectingProvider"' not in config_html
    assert "cancelConnect(providerId = \"\")" in store_js
    assert "if (this.connectingProvider === providerId) this.connectingProvider = \"\";" in store_js


def test_oauth_available_models_list_sits_above_advanced_without_borders():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")

    assert "activeModelsDescription()" in config_html
    assert config_html.index("<h3>Providers</h3>") < config_html.index("Choose your models")
    assert config_html.index("<h3>Providers</h3>") < config_html.index("<summary>Advanced</summary>")
    assert config_html.index("Available models") < config_html.index("<summary>Advanced</summary>")
    assert ".oauth-models-panel {\n      display: grid;\n      gap: 10px;\n      padding: 0;\n      border: 0;\n    }" in config_html
    assert ".oauth-provider-list {\n      display: grid;\n      gap: 12px;\n      padding: 0;\n      border: 0;" in config_html
    assert ".oauth-provider-row-detail {\n      display: grid;\n      grid-column: 1 / -1;" in config_html
    assert ".oauth-advanced {\n      border: 0;\n      border-radius: 0;\n      padding: 0;\n    }" in config_html
    model_chip_rule = config_html.split(".oauth-models span {", 1)[1].split("}", 1)[0]
    assert "border:" not in model_chip_rule


def test_oauth_model_slots_reuse_model_config_api():
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    assert 'import { store as modelConfigStore } from "/plugins/_model_config/webui/model-config-store.js";' in store_js
    assert 'const MODEL_CONFIG_API = "/plugins/_model_config";' in store_js
    assert "model_config_get" in store_js
    assert "model_config_set" in store_js
    assert "isOauthProvider" in store_js
    assert "providerCards()" in store_js
    assert "saveModelConfigIfDirty" in store_js
    assert "slotProviderChoices()" in store_js
    assert "modelProviderOptionLabel(provider)" in store_js
    assert "return this.connectedProviderCards();" in store_js
    assert "if (!this.providerConnected(providerId)) return;" in store_js
    assert "const providerId = slot.provider;" in store_js
    assert "const providerId = this.isOauthProvider(this.activeModelProvider)" not in store_js
    assert "applySoleConnectedProviderDefaults" in store_js
    assert "this.applySoleConnectedProviderDefaults();" in store_js
    assert "if (providers.length !== 1 || !this.modelConfig) return;" in store_js
    assert "if (model.provider && model.provider !== providerId) continue;" in store_js
    assert "model.name = \"\";" in store_js
    assert "this.modelSlotCurrentProviders[key] ?? slot.provider" in store_js
    assert "currentChatModelConfigured" not in store_js
    assert "providerDefaultModel" not in store_js
    assert 'new CustomEvent("model-setup-changed"' in store_js
    assert 'detail: { source: "_oauth", providerId }' in store_js
    assert "await this.handleProviderConnected(providerId)" in store_js


def test_browser_callback_completion_is_observed_from_modal():
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    assert "startCallbackPolling(providerId)" in store_js
    assert "stopCallbackPolling(providerId)" in store_js
    assert "this.providerConnected(providerId)" in store_js
    assert "await this.handleProviderConnected(providerId, { statusLoaded: true })" in store_js


def test_device_polling_honors_provider_interval_updates():
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")

    start_polling = store_js.split("startPolling(providerId = CODEX_PROVIDER)", 1)[1].split(
        "pollProvider(providerId = CODEX_PROVIDER)",
        1,
    )[0]
    assert "window.setTimeout(tick, delayMs)" in start_polling
    assert "window.setInterval(tick" not in start_polling
    assert "void tick();" not in start_polling
    assert "interval: response.interval || device.interval" in start_polling
    assert "expires_at: response.expires_at || device.expires_at" in start_polling
    assert "Date.now() / 1000 > expiresAt" in start_polling


def test_usage_plan_catalog_stays_backend_only_on_oauth_settings_page():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")
    store_js = (PROJECT_ROOT / "plugins/_oauth/webui/oauth-config-store.js").read_text(encoding="utf-8")
    plans_py = (PROJECT_ROOT / "plugins/_oauth/helpers/usage_plans.py").read_text(encoding="utf-8")

    assert "oauth-plan-catalog" not in config_html
    assert "usagePlanEntries" in store_js
    assert "Google Cloud Gemini" in plans_py
    assert "Google Cloud project" in plans_py
    assert "GEMINI_API_PROVIDER_ID" in plans_py
    assert "Google Gemini / Antigravity" not in plans_py
    assert "Claude Code" not in plans_py
    assert "antigravity_subscription_oauth" not in plans_py
    assert "claude_code_oauth" not in plans_py


def test_oauth_model_wrappers_do_not_add_box_borders_or_lateral_padding():
    config_html = (PROJECT_ROOT / "plugins/_oauth/webui/config.html").read_text(encoding="utf-8")

    assert ".oauth-model-config {\n      display: grid;\n      gap: 12px;\n      padding: 0;\n      border: 0;\n    }" in config_html
    assert ".oauth-model-card {\n      display: grid;" in config_html
    assert "      padding: 0;\n      border: 0;\n      background: transparent;" in config_html
    assert "oauth-model-card.is-codex" not in config_html
    assert "'is-codex'" not in config_html


def test_oauth_discovery_card_renders_in_welcome_account_panel():
    discovery_cards = (
        PROJECT_ROOT
        / "plugins/_discovery/extensions/python/banners/10_discovery_cards.py"
    ).read_text(encoding="utf-8")
    welcome_cards = (
        PROJECT_ROOT
        / "plugins/_discovery/extensions/webui/welcome-actions-end/discovery-cards.html"
    ).read_text(encoding="utf-8")
    discovery_store = (PROJECT_ROOT / "plugins/_discovery/webui/discovery-store.js").read_text(encoding="utf-8")

    assert "discovery-oauth-accounts" in discovery_cards
    assert "Your AI accounts" in discovery_cards
    assert "Use your subscription-backed logins for model access." in discovery_cards
    assert "Link account-backed providers such as" not in discovery_cards
    assert "Connected OAuth accounts" not in discovery_cards
    assert "discovery-codex-oauth" not in discovery_cards
    assert "5h and weekly limits are ready." not in discovery_cards
    assert "account providers connected and ready for model selection" not in discovery_cards
    assert '"icon": "account_circle"' not in discovery_cards
    assert "usage_windows" in discovery_cards
    assert "account_chips" in discovery_cards
    assert "discovery-account-card" in welcome_cards
    assert "discovery-account-chip" in welcome_cards
    assert "discovery-account-icon" not in welcome_cards
    assert ".discovery-account-chip {\n            display: inline-grid;" in welcome_cards
    assert "            border-radius: 8px;" in welcome_cards
    assert "discovery-account-usage" in welcome_cards
    assert "formatRemainingPercent(window)" in welcome_cards
    assert "formatRemainingPercent(window)" in discovery_store
    assert "usageWidth(window)" in discovery_store
    assert "oauthAccountCards" in discovery_store
    assert 'card.id === "discovery-oauth-accounts"' in discovery_store
