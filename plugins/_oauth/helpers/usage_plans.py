from __future__ import annotations

from copy import deepcopy
from typing import Any

CODEX_PROVIDER_ID = "codex_oauth"
GITHUB_COPILOT_PROVIDER_ID = "github_copilot_oauth"
GEMINI_API_PROVIDER_ID = "gemini_api_oauth"
XAI_GROK_PROVIDER_ID = "xai_grok_oauth"


USAGE_PLAN_CATALOG: dict[str, dict[str, Any]] = {
    CODEX_PROVIDER_ID: {
        "provider_id": CODEX_PROVIDER_ID,
        "display_name": "OpenAI Codex",
        "implemented": True,
        "plans": [
            {"id": "free", "label": "Free", "billing": "$0/month", "usage": "Quick coding tasks with plan-specific limits."},
            {"id": "go", "label": "Go", "billing": "$8/month", "usage": "Lightweight coding tasks."},
            {"id": "plus", "label": "Plus", "billing": "$20/month", "usage": "Focused coding sessions, latest Codex models, and credit extension."},
            {"id": "pro", "label": "Pro", "billing": "From $100/month", "usage": "Higher Codex limits than Plus, including Pro tiers."},
            {"id": "business", "label": "Business", "billing": "Pay as you go", "usage": "Standard or usage-based Codex seats, credits, admin controls, and no training by default."},
            {"id": "enterprise_edu", "label": "Enterprise / Edu", "billing": "Contact sales", "usage": "Enterprise controls, priority processing, audit and usage monitoring."},
            {"id": "api_key", "label": "API Key", "billing": "Token-based API pricing", "usage": "CLI, SDK, or IDE automation without ChatGPT cloud features."},
        ],
        "notes": [
            "Codex is included across ChatGPT Free, Go, Plus, Pro, Business, Edu, and Enterprise plans.",
            "The Pro 2x/boost promotion ended on 2026-05-31.",
            "API-key usage is separate from ChatGPT subscription usage and may receive delayed access to some new Codex models.",
        ],
        "sources": [
            {"label": "OpenAI Codex pricing", "url": "https://developers.openai.com/codex/pricing"},
            {"label": "Using Codex with your ChatGPT plan", "url": "https://help.openai.com/en/articles/11369540"},
        ],
    },
    GITHUB_COPILOT_PROVIDER_ID: {
        "provider_id": GITHUB_COPILOT_PROVIDER_ID,
        "display_name": "GitHub Copilot",
        "implemented": True,
        "plans": [
            {"id": "free", "label": "Copilot Free", "billing": "Free", "usage": "Entry Copilot access with monthly completion limits."},
            {"id": "student", "label": "Copilot Student", "billing": "Free for eligible users", "usage": "Student-entitled Copilot access."},
            {"id": "pro", "label": "Copilot Pro", "billing": "$10/month", "usage": "Individual Copilot access with paid entitlements."},
            {"id": "pro_plus", "label": "Copilot Pro+", "billing": "$39/month", "usage": "Larger individual AI-credit pool."},
            {"id": "max", "label": "Copilot Max", "billing": "$100/month", "usage": "Highest individual monthly AI-credit allowance and priority model access."},
            {"id": "business", "label": "Copilot Business", "billing": "$19/seat/month", "usage": "Team and organization plan with centralized management."},
            {"id": "enterprise", "label": "Copilot Enterprise", "billing": "$39/seat/month", "usage": "Enterprise Cloud plan with larger AI-credit pool and enterprise controls."},
        ],
        "notes": [
            "AI-credit availability and model access can differ by seat and organization policy.",
            "GitHub docs list new signup pauses for several Copilot plans beginning in April 2026.",
            "Beginning 2026-06-01, GitHub docs describe Copilot Max as upgrade-only for users with existing Copilot plans.",
        ],
        "sources": [
            {"label": "GitHub Copilot plans", "url": "https://docs.github.com/en/copilot/get-started/plans"},
        ],
    },
    GEMINI_API_PROVIDER_ID: {
        "provider_id": GEMINI_API_PROVIDER_ID,
        "display_name": "Google Cloud Gemini",
        "implemented": True,
        "plans": [
            {"id": "oauth_cloud_project", "label": "Google Cloud project", "billing": "Google Cloud project", "usage": "Official OAuth access using a user-provided Google Cloud OAuth client."},
            {"id": "api_key", "label": "API key", "billing": "Gemini API pricing", "usage": "Standard Gemini API key access through Google AI Studio or Google Cloud."},
            {"id": "vertex_ai", "label": "Vertex AI", "billing": "Google Cloud", "usage": "Enterprise Gemini API access through Vertex AI projects and IAM."},
        ],
        "notes": [
            "Gemini API OAuth requires the Google Generative Language API to be enabled on the user's Cloud project.",
            "OAuth Gemini API usage is separate from Antigravity, Gemini Code Assist, Gemini CLI, Google AI Pro, and Google AI Ultra subscription quotas.",
            "A quota project may be required so Google can attribute billing and quota to the correct Cloud project.",
        ],
        "sources": [
            {"label": "Gemini API OAuth", "url": "https://ai.google.dev/gemini-api/docs/oauth"},
            {"label": "Gemini OpenAI compatibility", "url": "https://ai.google.dev/gemini-api/docs/openai"},
            {"label": "Gemini API billing", "url": "https://ai.google.dev/gemini-api/docs/billing"},
        ],
    },
    XAI_GROK_PROVIDER_ID: {
        "provider_id": XAI_GROK_PROVIDER_ID,
        "display_name": "xAI Grok",
        "implemented": True,
        "plans": [
            {"id": "free", "label": "Free", "billing": "$0/month", "usage": "Grok app access with free limits."},
            {"id": "supergrok_lite", "label": "SuperGrok Lite", "billing": "Subscription", "usage": "Intermediate Grok app limits."},
            {"id": "supergrok", "label": "SuperGrok", "billing": "$30/month", "usage": "Higher app limits, Grok 4 model, connectors, image and video generation."},
            {"id": "supergrok_heavy", "label": "SuperGrok Heavy", "billing": "Subscription", "usage": "Highest individual Grok app tier."},
            {"id": "business", "label": "Business", "billing": "Team plan", "usage": "Team seats, billing, role-based access, and admin controls."},
            {"id": "enterprise", "label": "Enterprise", "billing": "Contact sales", "usage": "Custom rate limits, SSO, SCIM, data residency, and volume pricing."},
            {"id": "api_credits", "label": "API credits", "billing": "Prepaid/usage credits", "usage": "xAI API access after account setup and credit loading."},
        ],
        "notes": [
            "xAI API billing is separate from Grok app subscriptions unless xAI explicitly entitles the account.",
            "The API quickstart uses API keys from the xAI console and requires loading credits.",
        ],
        "sources": [
            {"label": "xAI pricing", "url": "https://x.ai/pricing"},
            {"label": "xAI API quickstart", "url": "https://docs.x.ai/developers/quickstart"},
        ],
    },
}


def usage_plan_catalog() -> dict[str, dict[str, Any]]:
    return deepcopy(USAGE_PLAN_CATALOG)
