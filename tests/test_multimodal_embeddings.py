from types import SimpleNamespace

import models


def test_embed_forwards_provider_ready_inputs(monkeypatch):
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
    monkeypatch.setattr(models, "_merge_litellm_call_kwargs", lambda kwargs: kwargs)
    monkeypatch.setattr(models, "apply_rate_limiter_sync", lambda *_args: None)
    wrapper = models.LiteLLMEmbeddingWrapper("gemini-embedding-2", "gemini")
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
