import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import models


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [None, "none", "requests", "input", "output"])
async def test_rate_limiter_counts_tokens_only_when_limits_are_configured(monkeypatch, limit):
    monkeypatch.setattr(models, "rate_limiters", {})
    counted = []
    monkeypatch.setattr(models, "approximate_tokens", lambda text: counted.append(text) or 3)
    config = models.ModelConfig(
        type=models.ModelType.CHAT, provider="openai", name="test",
    ) if limit is not None else None
    if limit in ("requests", "input", "output"):
        setattr(config, f"limit_{limit}", 10)

    limiter = await models.apply_rate_limiter(config, "prompt")

    if limit in (None, "none"):
        assert limiter is None
        assert counted == []
        assert models.rate_limiters == {}
    else:
        assert counted == ["prompt"]
        assert limiter.limits[limit] == 10
        assert await limiter.get_total("input") == 3
        assert await limiter.get_total("requests") == 1
