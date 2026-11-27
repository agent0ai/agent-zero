# Local ONNX embeddings

The bundled `huggingface / sentence-transformers/all-MiniLM-L6-v2` model runs on
CPU using ONNX Runtime. Its provider, model name, cache namespace and index
metadata remain unchanged. The pinned revision is
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; the full-precision upstream ONNX graph
matches the previously bundled safetensors weights. No quantization is used.

The pipeline retains the exact tokenizer, 256-token truncation including special
tokens, attention-mask mean pooling, model-defined L2 normalization, float32 and
384 dimensions. There are no query/document prefixes or extra encode-time
normalization. Existing default-model databases require no reindexing.

Docker builds prepare and checksum-check the ONNX graph and tokenizer, and run
an inference check. A fresh container can embed offline. Source/local setup is:

```sh
python -m pip install -r requirements.txt
python -m helpers.local_embeddings
```

The explicit preparation command first runs the existing legacy model-settings
migration (preserving backups), then can download missing public model assets;
embedding requests never do. Preparation covers the global configuration and all
saved presets and persisted raw chat overrides using the bundled model, including
project and agent-profile selections. Each selection retains its resolved `cache_folder` and
`use_auth_token`, including Default inheritance. Configure custom caches before
running the command, and rerun it after adding or changing a cache location. Docker
source upgrades prepare these caches after settings migration and preset
initialization, preserving their old contents.
`use_auth_token` retains its Hugging Face access meaning.

Only the bundled model/revision on CPU is validated. Other local models, a
changed revision, GPU devices, remote model code and nonempty `model_kwargs`
raise an actionable error without substituting a model or touching indexes.
Additional architectures need their own parity validation before support can be
claimed. Remote embeddings and local server providers such as Ollama still use
the existing provider dispatch. Changing embedding models through settings keeps
the existing model-change/reindex behavior.

A source update installs ONNX Runtime and prepares missing assets before startup
continues. It conservatively retains the previous training packages and cached
weights for private plugins and source rollback. Their implicit availability is
absent in new images; custom consumers must declare and install their own
requirements in their intended runtime. Rebuild both base and application images
to remove the old packages and reclaim their immutable layers. Speech/document
worker dependencies remain in their existing guests.

The reproducible compatibility runner is `tests/integration_onnx_compatibility.py`.
Run `old /tmp/onnx-compat` in the previous runtime, copy that synthetic fixture
unchanged into the new runtime at the same path, then run `new /tmp/onnx-compat`
and `restart /tmp/onnx-compat` in separate processes. It covers memory, unchanged
knowledge import, Document Query indexes, raw vector/score/norm tolerance,
ranking/thresholds, new inserts, sync/async batching and cache-bypass assertions.
The accepted absolute tolerance is 0.000002; near ties within twice that tolerance
may reorder. Empty strings are supported; an empty batch now returns an empty
list (the old sentence-transformers version raised IndexError).
