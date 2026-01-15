
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models


@pytest.mark.asyncio
async def test_rate_limiter_openrouter():
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    provider = "openrouter"
    name = "deepseek/deepseek-r1"

    model = models.get_chat_model(
        provider=provider,
        name=name,
        model_config=models.ModelConfig(
            type=models.ModelType.CHAT,
            provider=provider,
            name=name,
            limit_requests=5,
            limit_input=15000,
            limit_output=1000,
        ),
    )

    response, reasoning = await model.unified_call(
        user_message="Tell me a joke"
    )
    assert response
