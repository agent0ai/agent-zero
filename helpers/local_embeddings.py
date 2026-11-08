"""Pinned, offline MiniLM inference without the training stack."""
import hashlib
from pathlib import Path

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
# The upstream FP32 graph contains the exact bundled safetensors weights.
ASSETS = {
    "onnx/model.onnx": "6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452",
    "tokenizer.json": "be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037",
}


def configured_asset_options():
    """Prepare bundled-model caches reachable through saved model selections."""
    from plugins._model_config.helpers.model_config import get_saved_embedding_model_configs

    options = []
    for config in get_saved_embedding_model_configs():
        if config.provider != "huggingface" or config.name != MODEL:
            continue
        kwargs = config.build_kwargs()
        entry = {"cache_folder": kwargs.get("cache_folder"), "token": kwargs.get("use_auth_token")}
        if entry not in options:
            options.append(entry)
    return options or [{}]


def model_assets(*, cache_folder=None, token=None, download=False):
    from huggingface_hub import hf_hub_download

    paths = {}
    for name, digest in ASSETS.items():
        path = Path(hf_hub_download(
            MODEL, name, revision=REVISION, cache_dir=cache_folder,
            token=token, local_files_only=not download,
        ))
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest:
            raise ValueError(f"Embedding asset checksum mismatch: {name}")
        paths[name] = path
    return paths


class OnnxSentenceTransformer:
    """The validated bundled sentence-transformer pipeline, on CPU in float32."""

    def __init__(self, model, *, device=None, cache_folder=None, use_auth_token=None,
                 revision=None, trust_remote_code=False, model_kwargs=None):
        if model not in (MODEL, MODEL.removeprefix("sentence-transformers/")):
            raise ValueError(
                f"Local ONNX embeddings currently support only {MODEL}. "
                "Other local models need a separately validated ONNX pipeline; "
                "no model was substituted and no index was changed."
            )
        if revision not in (None, REVISION) or device not in (None, "cpu") or trust_remote_code or model_kwargs:
            raise ValueError(
                "Local ONNX embeddings require the bundled revision, CPU, "
                "trust_remote_code=false and no model_kwargs. "
                "These options cannot be silently translated to ONNX."
            )
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.np = np
        paths = model_assets(cache_folder=cache_folder, token=use_auth_token)
        self.tokenizer = Tokenizer.from_file(str(paths["tokenizer.json"]))
        self.tokenizer.enable_truncation(max_length=256, strategy="longest_first")
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        # Bound CPU use across concurrent framework requests and avoid oversized thread pools.
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(str(paths["onnx/model.onnx"]),
                                           sess_options=options, providers=["CPUExecutionProvider"])

    def encode(self, inputs, convert_to_tensor=False):
        if convert_to_tensor:
            raise ValueError("ONNX embeddings return NumPy arrays, not Torch tensors")
        if not isinstance(inputs, list) or any(not isinstance(text, str) for text in inputs):
            raise TypeError("Local embedding inputs must be a list of strings")
        np = self.np
        batches = []
        # Match SentenceTransformer's bounded batches; order is preserved without sorting.
        for offset in range(0, len(inputs), 32):
            tokens = self.tokenizer.encode_batch([text.strip() for text in inputs[offset:offset + 32]])
            feed = {
                "input_ids": np.asarray([t.ids for t in tokens], dtype=np.int64),
                "attention_mask": np.asarray([t.attention_mask for t in tokens], dtype=np.int64),
                "token_type_ids": np.asarray([t.type_ids for t in tokens], dtype=np.int64),
            }
            hidden = self.session.run(["last_hidden_state"], feed)[0]
            mask = feed["attention_mask"].astype(np.float32)[..., None]
            pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
            # Normalize is a model module; encode(normalize_embeddings=False) still runs it.
            pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            batches.append(pooled)
        return np.concatenate(batches) if batches else np.empty((0, 384), dtype=np.float32)


def prepare_model():
    """Provision and verify the bundled model in every configured cache."""
    from huggingface_hub.errors import LocalEntryNotFoundError

    for options in configured_asset_options():
        try:
            model_assets(**options)
        except LocalEntryNotFoundError:
            model_assets(download=True, **options)
        vector = OnnxSentenceTransformer(
            MODEL, cache_folder=options.get("cache_folder"), use_auth_token=options.get("token"),
        ).encode(["offline readiness"])
        assert vector.shape == (1, 384)
    print(f"Prepared {MODEL}@{REVISION} for offline ONNX inference")


if __name__ == "__main__":
    from plugins._model_config.extensions.python.startup_migration._10_migrate_model_config import MigrateModelConfig

    MigrateModelConfig(None).execute()
    prepare_model()
