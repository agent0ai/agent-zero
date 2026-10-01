from concurrent.futures import ThreadPoolExecutor
import threading
from types import SimpleNamespace

import pytest

import models


def _clear_local_embedding_models():
    with models._LOCAL_EMBEDDING_MODELS_LOCK:
        models._LOCAL_EMBEDDING_MODELS.clear()


def test_local_embedding_preload_is_reused_with_runtime_model_config(monkeypatch):
    created = []

    class FakeSentenceTransformer:
        def __init__(self, model, **kwargs):
            created.append((model, kwargs))

    monkeypatch.setattr(models, "SentenceTransformer", FakeSentenceTransformer)
    _clear_local_embedding_models()

    try:
        preload = models.LocalSentenceTransformerWrapper(
            "huggingface",
            "sentence-transformers/example",
            device="cpu",
            model_kwargs={"revision": "stable", "trust_remote_code": False},
        )
        runtime_config = SimpleNamespace(name="runtime")
        runtime = models.LocalSentenceTransformerWrapper(
            "huggingface",
            "sentence-transformers/example",
            model_config=runtime_config,
            model_kwargs={"trust_remote_code": False, "revision": "stable"},
            device="cpu",
        )

        assert runtime.model is preload.model
        assert runtime.a0_model_conf is runtime_config
        assert created == [
            (
                "example",
                {
                    "device": "cpu",
                    "model_kwargs": {
                        "revision": "stable",
                        "trust_remote_code": False,
                    },
                },
            )
        ]
    finally:
        _clear_local_embedding_models()


def test_local_embedding_cache_tracks_effective_constructor_options(monkeypatch):
    created = []

    class FakeSentenceTransformer:
        def __init__(self, model, **kwargs):
            created.append((model, kwargs))

    monkeypatch.setattr(models, "SentenceTransformer", FakeSentenceTransformer)
    _clear_local_embedding_models()

    try:
        first = models.LocalSentenceTransformerWrapper(
            "huggingface", "sentence-transformers/example", device="cpu"
        )
        second = models.LocalSentenceTransformerWrapper(
            "huggingface", "sentence-transformers/example", device="cuda"
        )

        assert second.model is not first.model
        assert created == [
            ("example", {"device": "cpu"}),
            ("example", {"device": "cuda"}),
        ]
        assert len(models._LOCAL_EMBEDDING_MODELS) == 1
    finally:
        _clear_local_embedding_models()


def test_concurrent_preload_and_runtime_share_one_model(monkeypatch):
    created = []
    construction_started = threading.Event()
    release_construction = threading.Event()

    class FakeSentenceTransformer:
        def __init__(self, model, **kwargs):
            created.append((model, kwargs))
            construction_started.set()
            assert release_construction.wait(timeout=2)

    monkeypatch.setattr(models, "SentenceTransformer", FakeSentenceTransformer)
    _clear_local_embedding_models()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(
                models.LocalSentenceTransformerWrapper,
                "huggingface",
                "sentence-transformers/example",
            )
            assert construction_started.wait(timeout=2)
            second = executor.submit(
                models.LocalSentenceTransformerWrapper,
                "huggingface",
                "sentence-transformers/example",
            )
            release_construction.set()

            assert second.result().model is first.result().model

        assert created == [("example", {})]
    finally:
        release_construction.set()
        _clear_local_embedding_models()


def test_failed_model_change_keeps_the_working_cached_model(monkeypatch):
    created = []

    class FakeSentenceTransformer:
        def __init__(self, model, **kwargs):
            created.append((model, kwargs))
            if model == "broken":
                raise RuntimeError("model unavailable")

    monkeypatch.setattr(models, "SentenceTransformer", FakeSentenceTransformer)
    _clear_local_embedding_models()

    try:
        working = models.LocalSentenceTransformerWrapper(
            "huggingface", "sentence-transformers/working"
        )
        with pytest.raises(RuntimeError, match="model unavailable"):
            models.LocalSentenceTransformerWrapper(
                "huggingface", "sentence-transformers/broken"
            )
        reused = models.LocalSentenceTransformerWrapper(
            "huggingface", "sentence-transformers/working"
        )

        assert reused.model is working.model
        assert created == [("working", {}), ("broken", {})]
    finally:
        _clear_local_embedding_models()


@pytest.mark.asyncio
async def test_preload_uses_the_runtime_embedding_configuration(monkeypatch):
    import preload
    from plugins._model_config.helpers import model_config

    config = SimpleNamespace(
        provider="huggingface",
        name="sentence-transformers/example",
        build_kwargs=lambda: {"device": "cpu"},
    )
    calls = []
    embedded = []

    class FakeEmbeddings:
        async def aembed_query(self, text):
            embedded.append(text)

    def get_embedding_model(provider, name, **kwargs):
        calls.append((provider, name, kwargs))
        return FakeEmbeddings()

    monkeypatch.setattr(
        model_config, "get_embedding_model_config_object", lambda: config
    )
    monkeypatch.setattr(preload.models, "get_embedding_model", get_embedding_model)

    await preload.preload()

    assert calls == [
        (
            "huggingface",
            "sentence-transformers/example",
            {"model_config": config, "device": "cpu"},
        )
    ]
    assert embedded == ["test"]
