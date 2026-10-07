import math
import re
import time
from datetime import date

import httpx

from helpers import cache


CACHE_AREA = "context_window_currency(plugins)"


async def get_exchange_rate(currency: str) -> dict | None:
    if currency == "USD" or not re.fullmatch(r"[A-Z]{3}", currency):
        return None
    cached = cache.get(CACHE_AREA, currency)
    if cached and time.monotonic() < cached[0]:
        return cached[1]

    result = None
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"https://api.frankfurter.dev/v2/rate/USD/{currency}")
            response.raise_for_status()
            data = response.json()
        rate = float(data["rate"])
        rate_date = date.fromisoformat(data["date"]).isoformat()
        if (
            data.get("base") != "USD" or data.get("quote") != currency
            or isinstance(data["rate"], bool) or not math.isfinite(rate) or rate <= 0
        ):
            raise ValueError("Invalid exchange rate")
        result = {"code": currency, "rate": rate, "date": rate_date}
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        pass

    cache.add(CACHE_AREA, currency, (time.monotonic() + (86400 if result else 300), result))
    return result
