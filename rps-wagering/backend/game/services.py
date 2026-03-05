import os
from decimal import Decimal

import requests

ONEINCH_BASE_URL = os.environ.get("ONEINCH_BASE_URL", "https://api.1inch.dev/swap/v6.0")
DEFAULT_CHAIN_ID = int(os.environ.get("ONEINCH_CHAIN_ID", "137"))


def fetch_oneinch_quote(*, chain_id: int, from_token: str, to_token: str, amount: str) -> dict:
    params = {
        "src": from_token,
        "dst": to_token,
        "amount": amount,
    }
    headers = {}
    api_key = os.environ.get("ONEINCH_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(
        f"{ONEINCH_BASE_URL}/{chain_id}/quote",
        params=params,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def estimate_aave_yield(*, principal_wei: int, apr_bps: int, days: int = 30) -> int:
    # Minimal off-chain estimate. Replace with on-chain Aave reserve data in production.
    apr = Decimal(apr_bps) / Decimal(10_000)
    estimated = Decimal(principal_wei) * apr * (Decimal(days) / Decimal(365))
    return int(estimated)
