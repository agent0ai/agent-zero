from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_onboarding_contains_guided_cloud_local_flow():
    html = (PROJECT_ROOT / "plugins/_onboarding/webui/onboarding.html").read_text(encoding="utf-8")
    store = (PROJECT_ROOT / "plugins/_onboarding/webui/onboarding-store.js").read_text(encoding="utf-8")

    assert "Cloud" in html
    assert "Local" in html
    assert "Welcome to Agent Zero" in html
    assert "Choose how to use AI models in Agent Zero" in html + store
    assert "Choose your cloud AI provider" in html + store
    assert "Choose your local LLM provider" in html + store
    assert "cloud-card.webp" in html
    assert "local-card.webp" in html
    assert "Connect ChatGPT/Codex Account" in html
    assert "Main model" in html
    assert "Refresh model list" in html
    assert "Search or enter Utility Model" in html
    assert "Advanced Settings" in html
    assert "selectedProviderName() + ' Docs'" in html
    assert "openSelectedProviderDocs" in html + store
    assert "Connect via device code" in html + store
    assert "accountActionLabel" in html + store
    assert "Click here if you don't see your provider" in html
    assert "provider-description" not in html
    assert "!$store.onboarding.isStep('cloud')" in html
    assert "!$store.onboarding.isStep('local')" in html
    assert "main-model-field" in html
    assert "wide-inline-field" in html
    assert "utility-panel" in html
    assert "showApiBaseField()" in html + store
    assert "localGuidance()" in html + store


def test_onboarding_provider_grid_names_are_present_in_metadata():
    provider_yaml = (PROJECT_ROOT / "conf/model_providers.yaml").read_text(encoding="utf-8")
    provider_ui = (PROJECT_ROOT / "plugins/_onboarding/webui/onboarding-providers.js").read_text(encoding="utf-8")
    model_metadata = (PROJECT_ROOT / "plugins/_model_config/provider_metadata.yaml").read_text(encoding="utf-8")

    assert "TOP_CLOUD_PROVIDER_IDS" in provider_ui
    assert '"venice"' in provider_ui
    assert '"xai"' in provider_ui
    assert '"nebius"' in provider_ui
    assert provider_ui.index('"venice"') < provider_ui.index('"zai"')
    assert provider_ui.index('"xai"') > provider_ui.index("MORE_CLOUD_PROVIDER_IDS")
    assert 'name: "Google"' in provider_ui
    assert 'docs_url: "https://openrouter.ai/workspaces/default/keys"' in provider_ui
    assert 'docs_url: "https://ai.google.dev/gemini-api/docs/api-key"' in provider_ui
    assert 'docs_url: "https://docs.venice.ai/guides/getting-started/generating-api-key"' in provider_ui
    assert 'docs_url: "https://docs.tokenfactory.nebius.com/api-reference/introduction"' in provider_ui
    assert 'docs_url: "https://lmstudio.ai/docs/developer/core/authentication"' in provider_ui
    assert 'docs_url: ""' in provider_ui
    assert "api_key_mode: none" in model_metadata
    assert "api_key_mode: optional" in model_metadata
    assert "Ollama Cloud" in provider_yaml
    assert "https://ollama.com/v1" in provider_yaml
    assert "Nebius Token Factory" in provider_yaml
    assert "https://api.tokenfactory.nebius.com/v1" in provider_yaml
    assert not (PROJECT_ROOT / "plugins/_model_config/conf/model_providers.yaml").exists()

    for name in [
        "OpenRouter",
        "Agent Zero API",
        "OpenAI",
        "Anthropic",
        "Google",
        "DeepSeek",
        "xAI",
        "Moonshot AI",
        "Nebius Token Factory",
        "Z.AI",
        "Mistral AI",
        "Azure OpenAI",
    ]:
        assert name in provider_yaml + provider_ui

    for name in ["Ollama Cloud", "AWS Bedrock", "Groq"]:
        assert name in provider_yaml + provider_ui

    for forbidden in [
        "onboarding_category",
        "onboarding_rank",
        "short_description",
        "setup_url",
        "api_key_url",
        "docs_url",
        "logo:",
        "api_key_mode",
        "model_list_autoload",
        "default_chat_model",
        "default_utility_model",
        "default_api_base",
    ]:
        assert forbidden not in provider_yaml

    for logo in [
        "google-gemini.svg",
        "groq.svg",
        "sambanova.png",
        "cometapi.ico",
        "github-copilot.svg",
        "zai-logo.svg",
    ]:
        assert logo in provider_ui


def test_nebius_provider_config_uses_openai_compatible_token_factory_endpoint():
    provider_path = PROJECT_ROOT / "conf/model_providers.yaml"
    provider_config = yaml.safe_load(provider_path.read_text(encoding="utf-8"))
    nebius = provider_config["chat"]["nebius"]

    assert nebius["name"] == "Nebius Token Factory"
    assert nebius["litellm_provider"] == "openai"
    assert nebius["kwargs"]["api_base"] == "https://api.tokenfactory.nebius.com/v1"
    assert nebius["models_list"]["endpoint_url"] == "/models"
    assert "api_key_mode" not in nebius


def test_discovery_auto_modal_extension_contains_required_guards():
    content = (PROJECT_ROOT / "plugins/_discovery/extensions/webui/initFw_end/auto-modal.js").read_text(encoding="utf-8")

    assert "auto_modal_path" in content
    assert "chat-created" in content
    assert "modalAlreadyOpen" in content
    assert "discovery_auto_modal_closed" in content
    assert "auto_modal_surfaces" in content


def test_onboarding_success_filters_codex_discovery_card():
    content = (
        PROJECT_ROOT
        / "plugins/_discovery/extensions/webui/onboarding-success-end/discovery-cards.html"
    ).read_text(encoding="utf-8")

    assert "discovery-codex-oauth" in content
    assert "filter(card => card.id !== 'discovery-codex-oauth')" in content
