"""Run `old FIXTURE`, then `new FIXTURE` in separate old/new offline runtimes.

The fixture contains only this public synthetic corpus. Never use a user database.
`candidate` tests the new helper through the old shared wrapper before switching it.
"""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

import models
from helpers import files
from helpers.vector_db import VectorDB, MyFaiss, cosine_normalizer
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
from plugins._memory.helpers.memory import Memory
from plugins._document_query.helpers.document_query import DocumentQueryStore
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
    return db.index.reconstruct_n(0, db.index.ntotal)


def snapshot(db):
    return {"ids": list(db.index_to_docstore_id.values()),
            "documents": {k: {"text": v.page_content, "metadata": v.metadata}
                          for k, v in db.get_all_docs().items()}}


async def main(mode, root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    files._base_dir = str(root)
    cfg = models.ModelConfig(models.ModelType.EMBEDDING, "huggingface", "sentence-transformers/all-MiniLM-L6-v2")
    model_config.get_embedding_model_config = lambda agent=None: {
        "provider": cfg.provider, "name": cfg.name, "kwargs": {}}
    if mode == "candidate":
        from helpers.local_embeddings import OnnxSentenceTransformer
        models._get_local_embedding_model = lambda name, kwargs: OnnxSentenceTransformer(name, **kwargs)
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
    if mode != "old":
        assert encoder.embed([]) == []
    assert np.isfinite(raw).all()
    np.testing.assert_allclose(np.linalg.norm(raw, axis=1), 1, atol=ATOL, rtol=0)
    counts = []
    original = models.LocalSentenceTransformerWrapper.embed

    def counted(self, inputs):
        counts.extend(inputs)
        return original(self, inputs)

    models.LocalSentenceTransformerWrapper.embed = counted
    agent = SimpleNamespace(get_embedding_model=lambda: encoder)
    store = DocumentQueryStore.__new__(DocumentQueryStore)
    store.agent = agent
    store.config = {"chunk_size": 1000, "chunk_overlap": 100}
    store.vector_db = None
    if mode == "old":
        db, created = Memory.initialize(None, cfg, "fixture")
        assert created
        memory = Memory(db, "fixture")
        await memory.insert_documents([Document(page_content=t, metadata={"area": "main"}) for t in CORPUS])
        knowledge = root / 'usr/knowledge/fixture'
        knowledge.mkdir(parents=True)
        (knowledge / 'manual.txt').write_text("Knowledge fixture: the silver telescope is in the observatory.")
        await memory.preload_knowledge(None, ["fixture"], "fixture")
        for i, text in enumerate(CORPUS):
            if text.strip():
                ok, _ = await store.add_document(text, f"https://fixture.invalid/document-{i}")
                assert ok
        store.vector_db.db.save_local(str(root / 'document-index'))
        np.savez(root / 'old-vectors.npz', raw=raw, query=query,
                 memory=vectors(db), document=vectors(store.vector_db.db))
        expected = {"memory": snapshot(db), "document": snapshot(store.vector_db.db)}
        expected['retrieval'] = {}
        for name, active in [('memory', db), ('document', store.vector_db.db)]:
            expected['retrieval'][name] = [
                [(d.metadata['id'], float(s)) for d, s in active.similarity_search_with_score(q, k=active.index.ntotal)]
                for q in QUERIES]
        expected['hashes'] = {str(p.relative_to(root)): digest(p) for folder in
                              [root/'usr/memory/fixture', root/'document-index']
                              for p in folder.iterdir() if p.is_file()}
        (root/'old.json').write_text(json.dumps(expected, indent=2))
        metrics = {"mode": mode, "startup_seconds": startup, "batch_seconds": batch_seconds}
    else:
        expected = json.loads((root/'old.json').read_text())
        old = np.load(root/'old-vectors.npz')
        np.testing.assert_allclose(raw, old['raw'], atol=ATOL, rtol=0)
        np.testing.assert_allclose(query, old['query'], atol=ATOL, rtol=0)
        counts.clear()
        db, created = Memory.initialize(None, cfg, "fixture")
        assert not created and not counts, 'Memory load rebuilt or embedded old data'
        memory = Memory(db, "fixture")
        await memory.preload_knowledge(None, ["fixture"], "fixture")
        assert not counts, 'Unchanged knowledge was re-embedded'
        restored = VectorDB.__new__(VectorDB)
        restored.agent, restored.cache, restored.embeddings = agent, False, encoder
        restored.db = MyFaiss.load_local(str(root/'document-index'), encoder,
                                         allow_dangerous_deserialization=True,
                                         distance_strategy=DistanceStrategy.COSINE,
                                         relevance_score_fn=cosine_normalizer)
        store.vector_db = restored
        for name, active in [('memory', db), ('document', restored.db)]:
            assert snapshot(active) == expected[name]
            np.testing.assert_array_equal(vectors(active), old[name])
        for rel, h in expected['hashes'].items():
            assert digest(root/rel) == h, rel
        max_score_error = 0
        tie_swaps = 0
        for name, active in [('memory', db), ('document', restored.db)]:
            for i, q in enumerate(QUERIES):
                before_count = len(counts)
                actual = [(d.metadata['id'], float(s)) for d, s in active.similarity_search_with_score(q, k=active.index.ntotal)]
                assert len(counts) > before_count, 'Old query cache masked new encoder'
                before = expected['retrieval'][name][i]
                old_scores = dict(before)
                err = max(abs(s-old_scores[doc]) for doc,s in actual)
                max_score_error = max(err,max_score_error)
                assert err <= ATOL
                for pos, (doc, score) in enumerate(actual):
                    if doc != before[pos][0]:
                        assert abs(old_scores[doc] - before[pos][1]) <= 2*ATOL, 'Material ranking change'
                        tie_swaps += 1
                for threshold in (0.5, 0.7, 0.9):
                    old_hits = {doc for doc,s in before if (1+s)/2 >= threshold}
                    new_hits = {doc for doc,s in actual if (1+s)/2 >= threshold}
                    assert old_hits == new_hits
        assert await memory.search_similarity_threshold(QUERIES[0], 5, .5)
        assert await store.search_documents(QUERIES[0], 5, .5)
        for name, active in [('memory', db), ('document', restored.db)]:
            old_count = active.index.ntotal
            active.add_documents([Document(page_content='A new telescope observes Jupiter.', metadata={'id':'new-insert'})], ids=['new-insert'])
            np.testing.assert_array_equal(vectors(active)[:old_count], old[name])
            assert 'new-insert' in [d.metadata['id'] for d in active.similarity_search('telescope Jupiter', k=3)]
        Memory._save_db_file(db, 'fixture')
        restored.db.save_local(str(root/'document-index'))
        metrics = {"mode": mode, "startup_seconds": startup, "batch_seconds": batch_seconds,
                   "max_vector_error": float(np.abs(raw-old['raw']).max()),
                   "max_query_error": float(np.abs(query-old['query']).max()),
                   "max_norm_error": float(np.abs(np.linalg.norm(raw,axis=1)-np.linalg.norm(old['raw'],axis=1)).max()),
                   "max_inner_product_error": max_score_error, "tie_position_swaps": tie_swaps,
                   "atol": ATOL, "corpus_count": len(CORPUS), "queries_count": len(QUERIES)}
    (root/f'{mode}-metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics))


def restart(root):
    root = Path(root).resolve()
    files._base_dir = str(root)
    cfg = models.ModelConfig(models.ModelType.EMBEDDING, 'huggingface', 'sentence-transformers/all-MiniLM-L6-v2')
    db, created = Memory.initialize(None, cfg, 'fixture')
    assert not created
    assert 'new-insert' in [d.metadata['id'] for d in db.similarity_search('telescope Jupiter', k=3)]
    old = np.load(root/'old-vectors.npz')
    np.testing.assert_array_equal(vectors(db)[:-1], old['memory'])
    encoder = models.get_embedding_model(cfg.provider, cfg.name)
    doc = MyFaiss.load_local(str(root/'document-index'), encoder, allow_dangerous_deserialization=True)
    np.testing.assert_array_equal(vectors(doc)[:-1], old['document'])
    assert 'new-insert' in [d.metadata['id'] for d in doc.similarity_search('telescope Jupiter', k=3)]
    print('Separate-process restart: mixed old/new vectors and retrieval passed')


if __name__ == '__main__':
    mode, folder = sys.argv[1:]
    if mode == 'restart':
        restart(folder)
    else:
        asyncio.run(main(mode, folder))
