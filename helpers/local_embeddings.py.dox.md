# Local ONNX embeddings

`OnnxSentenceTransformer` implements the validated bundled `all-MiniLM-L6-v2`
pipeline: exact revision and SHA-256 assets declared in the module, BERT tokenizer,
256 tokens including specials, right padding, attention-mask mean pooling and
model-defined L2 normalization, float32 CPU output. Batches are bounded at 32 and
retain caller order. `models.py` owns shared instance reuse and rate limits.

`model_assets()` checks both immutable asset hashes and defaults to local-only
Hugging Face cache lookup. Running `python -m helpers.local_embeddings` calls
the existing backed-up, idempotent legacy model-config migration, then
`prepare_model()` to prepare missing assets and verify inference during build/setup/upgrade.
`configured_asset_options()` resolves the global configuration and every saved
preset plus persisted raw chat overrides through model-config inheritance,
scope resolution and alias normalization. It reads chat metadata without restoring
agents or loading indexes. Docker readiness follows config migration and preset
bootstrap so newly migrated scope selections are included.
For the bundled model it deduplicates cache/access options and passes
`cache_folder` and `use_auth_token` to both preparation and readiness checks.
When none select the bundled model, default bundled-asset preparation remains.
The preparation subprocess reads these settings itself; tokens never go in its
command line. Runtime
requests never install dependencies or download assets. No Torch weights ship in
new images. Tokenizer defaults come from the exact bundled tokenizer JSON.

Only this model/revision and CPU are validated. Other local models, devices,
remote code and nonempty `model_kwargs` fail explicitly before index access;
they are never replaced with the default. `cache_folder` and `use_auth_token`
retain cache/access meanings. Docker source upgrades prepare all saved selection
caches without deleting their old contents; local setup runs the preparation command
after configuring a custom cache and before inference.
The wrapper keeps its legacy name and logical model identity for existing callers
and caches. Remote provider dispatch is unchanged.

Verify with `test_local_embeddings.py`, `test_embedding_model_preload.py`, and
`integration_onnx_compatibility.py` in separate old/new offline runtimes. Numerical
parity is specific to the pinned default; never extend the accepted model set
without persisted-index compatibility evidence.
