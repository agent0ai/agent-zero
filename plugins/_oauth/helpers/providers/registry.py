from __future__ import annotations

from plugins._oauth.helpers.providers.base import (
    CODEX_PROVIDER_ID,
    OAuthProvider,
)
from plugins._oauth.helpers.providers.codex import CodexOAuthProvider


def provider_registry() -> dict[str, OAuthProvider]:
    from plugins._oauth.helpers.providers.gemini_api import GeminiApiOAuthProvider
    from plugins._oauth.helpers.providers.github_copilot import GitHubCopilotOAuthProvider
    from plugins._oauth.helpers.providers.xai_grok import XaiGrokOAuthProvider

    providers: list[OAuthProvider] = [
        CodexOAuthProvider(),
        GitHubCopilotOAuthProvider(),
        GeminiApiOAuthProvider(),
        XaiGrokOAuthProvider(),
    ]
    return {provider.provider_id: provider for provider in providers}


def get_provider(provider_id: str | None = None) -> OAuthProvider:
    if provider_id is None:
        normalized = CODEX_PROVIDER_ID
    else:
        normalized = str(provider_id).strip()
        if not normalized:
            normalized = CODEX_PROVIDER_ID
    registry = provider_registry()
    try:
        return registry[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown OAuth provider: {normalized}") from exc


def oauth_provider_ids() -> set[str]:
    return set(provider_registry())
