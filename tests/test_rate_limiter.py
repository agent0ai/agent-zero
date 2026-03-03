import pytest


@pytest.mark.asyncio
async def test_apply_rate_limiter_increments_request_and_input_counters():
    import models

    conf = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider="test-provider",
        name="test-model",
        limit_requests=10,
        limit_input=0,
        limit_output=0,
    )

    limiter = await models.apply_rate_limiter(conf, "hello world")
    assert limiter is not None
    assert await limiter.get_total("requests") == 1
    assert await limiter.get_total("input") > 0

