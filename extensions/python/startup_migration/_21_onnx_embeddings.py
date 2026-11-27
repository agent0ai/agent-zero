"""Provision assets after preset migration/bootstrap and before chat restoration."""
import subprocess
import sys

from helpers import files, runtime
from helpers.extension import Extension


class OnnxEmbeddings(Extension):
    def execute(self, **kwargs):
        if not runtime.is_dockerized():
            return
        from huggingface_hub.errors import LocalEntryNotFoundError
        from helpers.local_embeddings import configured_asset_options, model_assets

        options = configured_asset_options()
        try:
            for entry in options:
                model_assets(**entry)
        except LocalEntryNotFoundError:
            # A subprocess verifies the new runtime without stale imports from before _05.
            subprocess.run(
                [sys.executable, "-m", "helpers.local_embeddings"],
                cwd=files.get_base_dir(), check=True, timeout=180,
            )
            for entry in options:
                model_assets(**entry)
        # Keep old packages/cache on source upgrades for private consumers and rollback.
        # Rebuilt images omit the old stack without deleting anything from user installations.
