import pytest

from helpers import extension
from helpers.llm_result import LLMResult
from models import LiteLLMChatWrapper


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "result"),
    [
        ("unified_call", ("response", "reasoning")),
        ("unified_turn", LLMResult(response="response")),
    ],
)
async def test_unified_model_calls_expose_function_extensions(
    monkeypatch, method_name, result
):
    points = []

    async def call_extensions(point, agent=None, **kwargs):
        points.append(point)
        if point.endswith("/start"):
            kwargs["data"]["result"] = result

    monkeypatch.setattr(extension, "call_extensions_async", call_extensions)

    actual = await getattr(LiteLLMChatWrapper, method_name)(object())

    assert actual is result
    assert points == [
        f"_functions/models/LiteLLMChatWrapper/{method_name}/start",
        f"_functions/models/LiteLLMChatWrapper/{method_name}/end",
    ]
