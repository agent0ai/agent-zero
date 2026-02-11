"""
Centralized branding configuration.

All user-visible brand identity reads from environment variables,
allowing fork operators to customize the project name, URL, and
GitHub link without modifying source code.

Environment variables:
    BRAND_NAME       — Display name (default: "Apollos AI")
    BRAND_SLUG       — URL/filename-safe slug (default: "apollos-ai")
    BRAND_URL        — Project website URL (default: "https://apollos.ai")
    BRAND_GITHUB_URL — GitHub repository URL (default: "https://github.com/jrmatherly/agent-zero")
"""

import os

BRAND_NAME: str = os.getenv("BRAND_NAME", "Apollos AI")
BRAND_SLUG: str = os.getenv("BRAND_SLUG", "apollos-ai")
BRAND_URL: str = os.getenv("BRAND_URL", "https://apollos.ai")
BRAND_GITHUB_URL: str = os.getenv(
    "BRAND_GITHUB_URL", "https://github.com/jrmatherly/agent-zero"
)
