"""Persistent memory records and exact inner-product search in the framework."""
import asyncio
from contextlib import closing
import hashlib
from itertools import batched
import json
import os
from pathlib import Path
import pickle
import sqlite3
import tempfile
import threading
import uuid

import faiss
import numpy as np
from langchain_core.documents import Document


class _LegacyRecord:
    pass


def _numeric_scalar(dtype, raw):
    if not isinstance(dtype, np.dtype) or dtype.kind not in "bfiu" or not isinstance(raw, bytes) or len(raw) != dtype.itemsize:
        raise ValueError("Unsupported legacy memory scalar")
    return np.frombuffer(raw, dtype=dtype, count=1)[0].item()


class _LegacyReader(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in {
            ("langchain_community.docstore.in_memory", "InMemoryDocstore"),
            ("langchain_core.documents.base", "Document"),
        }:
            return _LegacyRecord
        # Some old consolidation metadata contains NumPy scalar scores.
        if module in {"numpy.core.multiarray", "numpy._core.multiarray"} and name == "scalar":
            return _numeric_scalar
        if (module, name) == ("numpy", "dtype"):
            return np.dtype
        raise ValueError(f"Unsupported legacy memory data type: {module}.{name}")


def _legacy_documents(path):
    with path.open("rb") as stream:
        store, order = _LegacyReader(stream).load()
    if set(order) != set(range(len(order))) or set(order.values()) != set(store._dict) or len(order) != len(store._dict):
        raise ValueError("Legacy memory IDs do not match its document store")
    docs = []
    for position in range(len(order)):
        key = order[position]
        fields = vars(store._dict[key])["__dict__"]
        doc = Document(page_content=fields["page_content"], metadata=fields["metadata"], id=key)
        if doc.metadata.get("id") != key:
            raise ValueError("Legacy memory metadata ID does not match its stored ID")
        docs.append(doc)
    return docs


def _json_scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Unsupported memory metadata type: {type(value).__name__}")


class NativeStore:
    filename = "memory.sqlite3"

    def __init__(self, folder, model, identity, namespace, cache):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / self.filename
        self.embedding_function = model
        self.identity = json.dumps(identity)
        self.namespace = namespace
        self.cache = Path(cache) if cache else None
        self._volatile_cache = {}
        self._lock = threading.RLock()
        self._revision = None
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)

    def _embeddings(self, docs):
        # Preserve the legacy CacheBackedEmbeddings file keys for offline migrations.
        keys = []
        for doc in docs:
            digest = hashlib.sha1(doc.page_content.encode()).hexdigest()
            keys.append(self.namespace + str(uuid.uuid5(uuid.UUID(int=1985), digest)))
        values = {}
        missing = {}
        for key, doc in zip(keys, docs):
            if key in values or key in missing:
                continue
            if self.cache and (self.cache / key).is_file():
                values[key] = json.loads((self.cache / key).read_bytes())
            elif key in self._volatile_cache:
                values[key] = self._volatile_cache[key]
            else:
                missing[key] = doc.page_content
        for batch in batched(missing, 64):
            vectors = self.embedding_function.embed_documents([missing[key] for key in batch])
            for key, vector in zip(batch, vectors, strict=True):
                values[key] = vector
                if self.cache:
                    with tempfile.NamedTemporaryFile(dir=self.cache, mode="w", delete=False) as stream:
                        try:
                            json.dump(vector, stream)
                            stream.close()
                            os.replace(stream.name, self.cache / key)
                        finally:
                            Path(stream.name).unlink(missing_ok=True)
                else:
                    self._volatile_cache[key] = vector
        return [values[key] for key in keys]

    def _connect(self):
        return sqlite3.connect(self.path, timeout=60)

    def initialize(self):
        with closing(self._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError(f"Unsupported memory database version: {version}")
            conn.execute("PRAGMA user_version=1")
            conn.execute("CREATE TABLE IF NOT EXISTS settings (model TEXT, revision INTEGER)")
            conn.execute("CREATE TABLE IF NOT EXISTS docs (id TEXT PRIMARY KEY, text TEXT, metadata TEXT, vector BLOB)")
            state = conn.execute("SELECT model FROM settings").fetchone()
            if state and state[0] == self.identity:
                return False
            if state:
                docs = list(self._read_docs(conn).values())
            else:
                legacy = self.folder / "index.pkl"
                if not legacy.exists() and (self.folder / "index.faiss").exists():
                    raise ValueError("Legacy memory records are missing: index.pkl")
                docs = _legacy_documents(legacy) if legacy.exists() else []
            vectors = self._embeddings(docs)
            self._write(conn, docs, vectors, replace=True)
            if state:
                conn.execute("UPDATE settings SET model=?, revision=revision+1", (self.identity,))
            else:
                conn.execute("INSERT INTO settings VALUES (?, 1)", (self.identity,))
            return not docs

    @staticmethod
    def _read_docs(conn):
        return {key: Document(id=key, page_content=text, metadata=json.loads(metadata))
                for key, text, metadata in conn.execute("SELECT id,text,metadata FROM docs ORDER BY rowid")}

    def get_all_docs(self):
        with closing(self._connect()) as conn:
            return self._read_docs(conn)

    def get_by_ids(self, ids):
        if isinstance(ids, str):
            ids = [ids]
        with closing(self._connect()) as conn:
            result = []
            for key in ids:
                row = conn.execute("SELECT text,metadata FROM docs WHERE id=?", (key,)).fetchone()
                if row:
                    result.append(Document(id=key, page_content=row[0], metadata=json.loads(row[1])))
            return result

    def _check_model(self, conn):
        model, revision = conn.execute("SELECT model, revision FROM settings").fetchone()
        if model != self.identity:
            raise RuntimeError("The embedding model for this memory has changed. Reload memory before continuing.")
        return revision

    @staticmethod
    def _write(conn, docs, vectors, replace):
        rows = []
        for doc, vector in zip(docs, vectors, strict=True):
            v = np.asarray(vector, dtype="<f4")
            if v.ndim != 1 or not v.size or not np.isfinite(v).all():
                raise ValueError("Invalid memory embedding")
            rows.append((doc.metadata["id"], doc.page_content, json.dumps(doc.metadata, default=_json_scalar), v.tobytes()))
        if rows:
            sizes = {len(row[3]) for row in rows}
            if len(sizes) != 1:
                raise ValueError("Inconsistent embedding dimensions")
        sql = "INSERT INTO docs VALUES (?,?,?,?)"
        if replace:
            sql += " ON CONFLICT(id) DO UPDATE SET text=excluded.text,metadata=excluded.metadata,vector=excluded.vector"
        conn.executemany(sql, rows)

    def put(self, docs, *, replace=False, delete_ids=()):
        vectors = self._embeddings(docs)
        with closing(self._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            self._check_model(conn)
            dimension = conn.execute("SELECT length(vector)/4 FROM docs LIMIT 1").fetchone()
            if dimension and any(len(vector) != dimension[0] for vector in vectors):
                raise ValueError("Embedding dimension differs from existing memories")
            if replace:
                present = conn.execute("SELECT id FROM docs WHERE id IN (SELECT value FROM json_each(?))",
                                       (json.dumps([d.metadata["id"] for d in docs]),)).fetchall()
                if {row[0] for row in present} != {d.metadata["id"] for d in docs}:
                    raise ValueError("Cannot update a memory that was deleted")
            conn.executemany("DELETE FROM docs WHERE id=?", ((key,) for key in delete_ids))
            self._write(conn, docs, vectors, replace)
            conn.execute("UPDATE settings SET revision=revision+1")

    async def adelete(self, ids):
        await asyncio.to_thread(self._delete, ids)

    def _delete(self, ids):
        with closing(self._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            self._check_model(conn)
            conn.executemany("DELETE FROM docs WHERE id=?", [(key,) for key in ids])
            conn.execute("UPDATE settings SET revision=revision+1")

    def search(self, vector, limit, predicate=None):
        if limit <= 0:
            return []
        with self._lock, closing(self._connect()) as conn:
            conn.execute("BEGIN")
            revision = self._check_model(conn)
            if revision != self._revision:
                rows = conn.execute("SELECT id,vector FROM docs ORDER BY rowid").fetchall()
                self._ids = [row[0] for row in rows]
                self._index = None
                if rows:
                    vectors = np.stack([np.frombuffer(row[1], dtype="<f4") for row in rows])
                    self._index = faiss.IndexFlatIP(vectors.shape[1])
                    self._index.add(vectors)
                self._revision = revision
            if self._index is None:
                return []
            query = np.asarray([vector], dtype="float32")
            if query.shape != (1, self._index.d) or not np.isfinite(query).all():
                raise ValueError("Query embedding dimension differs from the memory index")
            scores, positions = self._index.search(query, min(20 if predicate else limit, len(self._ids)))
            hits = []
            for score, pos in zip(scores[0], positions[0]):
                key = self._ids[pos]
                text, metadata = conn.execute("SELECT text,metadata FROM docs WHERE id=?", (key,)).fetchone()
                metadata = json.loads(metadata)
                if predicate is None or predicate(metadata):
                    hits.append((Document(id=key, page_content=text, metadata=metadata), float(score)))
                    if len(hits) == limit:
                        break
            return hits
