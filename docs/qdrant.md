# Qdrant Memory Backend (Preview)

Configuration lives in `conf/memory.yaml`:

```yaml
backend: qdrant            # faiss | qdrant | hybrid
qdrant:
  url: http://localhost:6333
  api_key: ""
  collection: agent-zero
  prefer_hybrid: true
  score_threshold: 0.6
  limit: 20
fallback_to_faiss: true     # keep FAISS as a fallback
mirror_to_faiss: false      # mirror writes to FAISS (not enabled yet)
```

Notes:
- The effective collection name is `{collection}-{memory_subdir}` to isolate projects.
- Requires `qdrant-client` (added to `requirements.txt`).
- A local Qdrant instance should run on `localhost:6333` (see docker-compose addition planned).

## Run locally

```
cd docker/run
docker compose -f docker-compose.qdrant.yml up -d
```
