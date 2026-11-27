"""A chat's temporary chunk index. All database and FAISS operations run in the guest."""
import base64
import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
import re

import faiss
from simpleeval import InvalidExpression, simple_eval
import numpy as np

from plugins._document_query.helpers.chunks import index_chunks


def handle(request, directory=Path("/index")):
    op = request["operation"]
    if op == "split":
        return index_chunks(request["text"], request["config"])
    with closing(sqlite3.connect(directory / "chunks.sqlite3")) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS chunks (uri TEXT, id TEXT PRIMARY KEY, text TEXT, metadata TEXT, vector BLOB)")
        uri = request.get("uri")
        if op == "put":
            chunks = request["chunks"]
            raw = base64.b64decode(request["vectors"], validate=True)
            width = request["dimension"] * 4
            if not chunks or width <= 0 or len(raw) != len(chunks) * width:
                raise ValueError("Invalid chunk vectors")
            existing = db.execute("SELECT length(vector) FROM chunks WHERE uri != ? LIMIT 1", (uri,)).fetchone()
            if (existing and width != existing[0]) or not np.isfinite(np.frombuffer(raw, dtype="<f4")).all():
                raise ValueError("Invalid chunk embedding dimensions or values")
            ids = [uuid.uuid4().hex for _ in chunks]
            db.execute("DELETE FROM chunks WHERE uri=?", (uri,))
            for i, (key, chunk) in enumerate(zip(ids, chunks)):
                meta = dict(request["metadata"], id=key, document_uri=uri, chunk_index=i, total_chunks=len(ids))
                db.execute("INSERT INTO chunks VALUES (?,?,?,?,?)",
                           (uri, key, chunk, json.dumps(meta), raw[i*width:(i+1)*width]))
            return ids
        if op == "exists":
            return db.execute("SELECT 1 FROM chunks WHERE uri=? LIMIT 1", (uri,)).fetchone() is not None
        if op == "delete":
            return db.execute("DELETE FROM chunks WHERE uri=?", (uri,)).rowcount > 0
        if op == "list":
            return [row[0] for row in db.execute("SELECT DISTINCT uri FROM chunks ORDER BY uri")]
        if op == "chunks":
            return [{"page_content": text, "metadata": json.loads(meta)} for text, meta in
                    db.execute("SELECT text, metadata FROM chunks WHERE uri=? ORDER BY rowid", (uri,))]
        if op != "search":
            raise ValueError(f"Unknown index operation: {op}")
        uris = request.get("uris")
        where = "" if uris is None else " WHERE uri IN (SELECT value FROM json_each(?))"
        rows = db.execute("SELECT text,metadata,vector FROM chunks" + where + " ORDER BY rowid",
                          () if uris is None else (json.dumps(uris),)).fetchall()
        limit = min(request["limit"], len(rows))
        if limit <= 0:
            return []
        matrix = np.stack([np.frombuffer(row[2], dtype="<f4") for row in rows])
        query = np.asarray([request["vector"]], dtype="float32")
        if query.shape != (1, matrix.shape[1]) or not np.isfinite(query).all():
            raise ValueError("Query and document dimensions differ")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        condition = request.get("filter", "")
        if len(condition) > 512 or (condition and not re.fullmatch(r"""[\w. \t'"=<>!()\[\],:+-]+""", condition)):
            return []
        scores, positions = index.search(query, len(rows) if condition else limit)
        result = []
        for score, pos in zip(scores[0], positions[0]):
            if max(0., min(1., (1. + float(score)) / 2)) < request["threshold"]:
                break
            meta = json.loads(rows[pos][1])
            if condition:
                try:
                    if not simple_eval(condition, names=meta, functions={}):
                        continue
                except (InvalidExpression, KeyError, TypeError, ValueError, SyntaxError, ArithmeticError):
                    continue
            result.append({"page_content": rows[pos][0], "metadata": meta})
            if len(result) == limit:
                break
        return result
