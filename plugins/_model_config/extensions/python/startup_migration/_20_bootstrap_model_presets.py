import os
import urllib.request

from helpers import files
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from plugins._model_config.helpers import model_config


REMOTE_PRESETS_URL = (
    "https://raw.githubusercontent.com/agent0ai/a0-presets/"
    "main/model_presets.yaml"
)
FETCH_TIMEOUT_SECONDS = 5
MAX_PRESETS_BYTES = 256 * 1024


class BootstrapModelPresets(Extension):
    """Ensure a missing user preset collection is initialized at startup."""

    def execute(self, **kwargs):
        presets_path = model_config._get_presets_path()

        # This is the normal startup path and must not perform network I/O.
        if os.path.exists(presets_path):
            return "existing"

        source = "remote"
        try:
            presets = self._download_presets()
        except Exception as exc:
            source = "fallback"
            PrintStyle.warning(
                "Could not initialize model presets from agent0ai/a0-presets; "
                f"using fallback presets. {exc}"
            )
            try:
                presets = model_config.parse_preset_collection(
                    files.read_file(model_config._get_fallback_presets_path())
                )
            except Exception as fallback_exc:
                PrintStyle.error(
                    f"Fallback model presets are invalid: {fallback_exc}"
                )
                return "error"

        try:
            model_config.save_presets(presets)
        except Exception as exc:
            # Runtime preset resolution still falls back to the local file if
            # initialization cannot be persisted.
            PrintStyle.error(f"Could not persist initial model presets: {exc}")
            return "error"

        if source == "remote":
            PrintStyle.info("Initialized model presets from agent0ai/a0-presets.")
        return source

    def _download_presets(self) -> list:
        request = urllib.request.Request(
            REMOTE_PRESETS_URL,
            headers={
                "Accept": "application/yaml, text/yaml, text/plain",
                "User-Agent": "AgentZero-Model-Preset-Bootstrap",
            },
        )
        with urllib.request.urlopen(
            request,
            timeout=FETCH_TIMEOUT_SECONDS,
        ) as response:
            payload = response.read(MAX_PRESETS_BYTES + 1)

        if len(payload) > MAX_PRESETS_BYTES:
            raise ValueError("Remote model preset file is too large.")

        text = payload.decode("utf-8-sig")
        return model_config.parse_preset_collection(text)
