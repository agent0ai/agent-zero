import asyncio
import pickle
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from plugins._memory.helpers.native_store import NativeStore


def store(folder, model_name, embed):
    return NativeStore(folder, SimpleNamespace(embed_documents=embed), ["fixture", model_name], model_name, folder / "cache")


def test_model_change_reindexes_and_failed_replacement_preserves_memory(tmp_path):
    first = store(tmp_path, "first", lambda texts: [[1., 0.] for _ in texts])
    first.initialize()
    doc = Document(page_content="remember this", metadata={"id": "one", "area": "main"})
    first.put([doc])

    def fail(texts):
        raise RuntimeError("provider unavailable")

    second = store(tmp_path, "second", fail)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        second.initialize()
    assert first.search([1., 0.], 1)[0][0].page_content == doc.page_content
    second.embedding_function.embed_documents = lambda texts: [[0., 0., 1.] for _ in texts]
    second.initialize()
    assert second.search([0., 0., 1.], 1)[0][0].metadata == doc.metadata
    with pytest.raises(RuntimeError, match="embedding model"):
        first.put([doc], replace=True)
    second.embedding_function.embed_documents = fail
    with pytest.raises(RuntimeError, match="provider unavailable"):
        second.put([Document(page_content="updated", metadata={"id": "two"})], delete_ids=["one"])
    assert list(second.get_all_docs()) == ["one"]
    asyncio.run(second.adelete(["one"]))
    assert not second.get_by_ids(["one"])


def test_unrecognized_legacy_record_aborts_and_preserves_source(tmp_path):
    legacy = tmp_path / "index.pkl"
    original = pickle.dumps(Path("unsupported"))
    legacy.write_bytes(original)
    db = store(tmp_path, "test", lambda _: pytest.fail("unexpected embedding"))
    for _ in range(2):
        with pytest.raises(ValueError, match="Unsupported legacy"):
            db.initialize()
        assert legacy.read_bytes() == original
