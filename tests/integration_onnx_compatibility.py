"""Generate the fixture with the old image’s integration script, then run new and restart here.

The fixture contains only this public synthetic corpus. Never use a user database.
"""
import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

import numpy as np

import models
from helpers import files
from langchain_core.documents import Document
from plugins._memory.helpers.memory import Memory
from plugins._model_config.helpers import model_config

CORPUS = [
    "The observatory opens on Monday at nine.",
    "The observatory opens on Tuesday at nine.",
    "The library closes at six on Friday.",
    "A lithium battery stores electrical energy.",
    "Photosynthesis converts sunlight into chemical energy.",
    "Jan lives in Brno and enjoys cycling.",
    "Žluťoučký kůň úpěl ďábelské ódy. Café naïve résumé.",
    "你好世界。東京の図書館。 مرحبا بالعالم 🌍",
    "", " ", "\n\t", "duplicate document", "duplicate document",
    "[CLS] a [SEP] b [MASK]", "Hello\u0000world\u200b!",
    *["word " * n + "final suffix" for n in (252, 253, 254, 255, 256, 257, 512, 2048)],
    "  mixed\n whitespace\t and CAPS  ", "e\u0301 and é", "123 0.00001 -99.9",
    *[f"public fixture number {n}" for n in range(12)],
]
QUERIES = ["When does the observatory open?", "Where does Jan live?", "energy from sunlight",
           "東京", "duplicate document", "word " * 255, "\t", "[MASK]", "fixture number 7"]
ATOL = 2e-6


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vectors(db):
    with sqlite3.connect(db.path) as connection:
        return np.stack([np.frombuffer(row[0], dtype="<f4") for row in
                         connection.execute("SELECT vector FROM docs ORDER BY rowid")])


async def main(mode, root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    files._base_dir = str(root)
    cfg = models.ModelConfig(models.ModelType.EMBEDDING, "huggingface", "sentence-transformers/all-MiniLM-L6-v2")
    model_config.get_embedding_model_config = lambda agent=None: {
        "provider": cfg.provider, "name": cfg.name, "kwargs": {}}
    start = time.perf_counter()
    encoder = model_config.build_embedding_model()
    warm = encoder.embed_query("offline readiness")
    startup = time.perf_counter() - start
    assert len(warm) == 384
    assert encoder.model_name == "all-MiniLM-L6-v2"
    start = time.perf_counter()
    raw = np.asarray(encoder.embed_documents(CORPUS), dtype=np.float32)
    batch_seconds = time.perf_counter() - start
    query = np.asarray(encoder.embed(QUERIES), dtype=np.float32)
    singles = np.asarray([encoder.embed_query(x) for x in CORPUS], dtype=np.float32)
    np.testing.assert_allclose(raw, singles, atol=ATOL, rtol=0)
    np.testing.assert_allclose(raw, await encoder.aembed_documents(CORPUS), atol=ATOL, rtol=0)
    np.testing.assert_allclose(query[0], await encoder.aembed_query(QUERIES[0]), atol=ATOL, rtol=0)
    assert encoder.embed([]) == []
    assert np.isfinite(raw).all()
    np.testing.assert_allclose(np.linalg.norm(raw, axis=1), 1, atol=ATOL, rtol=0)
    counts = []
    original = models.LocalSentenceTransformerWrapper.embed

    def counted(self, inputs):
        counts.extend(inputs)
        return original(self, inputs)

    models.LocalSentenceTransformerWrapper.embed = counted
    expected = json.loads((root/'old.json').read_text())
    old = np.load(root/'old-vectors.npz')
    np.testing.assert_allclose(raw, old['raw'], atol=ATOL, rtol=0)
    np.testing.assert_allclose(query, old['query'], atol=ATOL, rtol=0)
    counts.clear()
    db, created = Memory.initialize(None, cfg, "fixture")
    assert not created and not counts, "Memory migration should reuse existing embeddings"
    memory = Memory(db, "fixture")
    await memory.preload_knowledge(None, ["fixture"], "fixture")
    assert not counts, "Unchanged knowledge was re-embedded"
    docs = db.get_all_docs()
    assert list(docs) == expected["memory"]["ids"]
    assert {key: {"text": doc.page_content, "metadata": doc.metadata}
            for key, doc in docs.items()} == expected["memory"]["documents"]
    np.testing.assert_array_equal(vectors(db), old["memory"])
    for rel, checksum in expected["hashes"].items():
        assert digest(root/rel) == checksum, rel
    max_error = 0.
    for q, previous in zip(QUERIES, expected["retrieval"]["memory"]):
        hits = db.search(await memory.embed_query(q), len(docs))
        assert len(hits) == len(previous)
        scores = dict(previous)
        for (doc, score), (_, previous_score) in zip(hits, previous):
            max_error = max(max_error, abs(score - scores[doc.id]))
            assert abs(score - previous_score) <= 2 * ATOL
        for threshold in (0.5, 0.7, 0.9):
            assert {d.id for d, s in hits if (1+s)/2 >= threshold} == {
                key for key, s in previous if (1+s)/2 >= threshold}
    assert max_error <= ATOL
    db.put([Document(page_content="A new telescope observes Jupiter.", metadata={"id":"new-insert"})])
    assert "new-insert" in [doc.id for doc in await memory.search_similarity_threshold("telescope Jupiter", 3, .5)]
    print(json.dumps(dict(memories=len(docs), queries=len(QUERIES), max_score_error=max_error,
                          startup_seconds=startup, batch_seconds=batch_seconds)))


def restart(root):
    files._base_dir = str(Path(root).resolve())
    cfg = models.ModelConfig(models.ModelType.EMBEDDING, "huggingface", "sentence-transformers/all-MiniLM-L6-v2")
    db, created = Memory.initialize(None, cfg, "fixture")
    assert not created
    vector = db.embedding_function.embed_query("telescope Jupiter")
    assert "new-insert" in [doc.id for doc, _ in db.search(vector, 3)]
    np.testing.assert_array_equal(vectors(db)[:-1], np.load(Path(root)/"old-vectors.npz")["memory"])
    print("Separate-process restart preserved mixed old/new memories")


if __name__ == "__main__":
    mode, folder = sys.argv[1:]
    if mode == "restart":
        restart(folder)
    elif mode == "new":
        asyncio.run(main(mode, folder))
    else:
        raise SystemExit("Use the old image and its script to generate the fixture")
