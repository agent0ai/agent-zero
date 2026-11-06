from types import SimpleNamespace

import pytest

import models


def test_embed_forwards_provider_ready_inputs_without_chat_api_mode(monkeypatch):
    calls: list[dict] = []

    def fake_embedding(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            data=[
                {"embedding": [float(index)]}
                for index, _ in enumerate(kwargs["input"])
            ]
        )

    monkeypatch.setattr(models, "embedding", fake_embedding)
    monkeypatch.setattr(models, "configure_litellm", lambda: None)
    monkeypatch.setattr(models, "_merge_litellm_call_kwargs", lambda kwargs: dict(kwargs))
    monkeypatch.setattr(models, "apply_rate_limiter_sync", lambda *_args: None)
    wrapper = models.LiteLLMEmbeddingWrapper(
        "gemini-embedding-2", "gemini", a0_api_mode="responses"
    )
    inputs = [
        "plain text",
        "data:image/png;base64,image",
        "data:audio/wav;base64,audio",
        "data:video/mp4;base64,video",
    ]

    assert wrapper.embed(inputs) == [[0.0], [1.0], [2.0], [3.0]]
    assert calls == [{"model": "gemini/gemini-embedding-2", "input": inputs}]


def test_langchain_embedding_methods_use_embed_entry_point():
    wrapper = models.LiteLLMEmbeddingWrapper("model", "provider")
    calls: list[list[str]] = []

    def fake_embed(inputs: list[str]) -> list[list[float]]:
        calls.append(inputs)
        return [[float(index)] for index, _ in enumerate(inputs)]

    wrapper.embed = fake_embed  # type: ignore[method-assign]

    assert wrapper.embed_query("query") == [0.0]
    assert wrapper.embed_documents(["first", "second"]) == [[0.0], [1.0]]
    assert calls == [["query"], ["first", "second"]]


def _wrapper_returning(monkeypatch, data):
    monkeypatch.setattr(
        models, "embedding", lambda **_kwargs: SimpleNamespace(data=data)
    )
    monkeypatch.setattr(models, "configure_litellm", lambda: None)
    monkeypatch.setattr(models, "_merge_litellm_call_kwargs", lambda kwargs: dict(kwargs))
    monkeypatch.setattr(models, "apply_rate_limiter_sync", lambda *_args: None)
    return models.LiteLLMEmbeddingWrapper("qwen/qwen3-embedding:8b", "openai")


def test_embed_reads_vectors_from_wrapped_gateway_response(monkeypatch):
    # Shape returned by some OpenAI-compatible gateways (issue #1942):
    # {"data": {"object": "list", "data": [{"embedding": [...]}]}}
    wrapper = _wrapper_returning(
        monkeypatch,
        {
            "model": "qwen/qwen3-embedding:8b",
            "object": "list",
            "usage": {"prompt_tokens": 2, "total_tokens": 2},
            "data": [{"index": 0, "embedding": [0.1, 0.2]}],
        },
    )

    assert wrapper.embed_query("example") == [0.1, 0.2]


def test_embed_reports_unreadable_response_clearly(monkeypatch):
    wrapper = _wrapper_returning(monkeypatch, {"error": "nope"})

    with pytest.raises(ValueError, match="expected 'data' to be a list"):
        wrapper.embed(["example"])
