import math
from typing import Any

def _resolve_voice(
    pipeline: Any, voice: str, voice_weights: dict[str, float]
) -> Any:
    if not voice_weights:
        return voice

    total = sum(voice_weights.values())
    if not math.isfinite(total) or total <= 0:
        return voice
    blend = None
    for voice_id, weight in voice_weights.items():
        weighted_pack = pipeline.load_single_voice(voice_id) * (weight / total)
        blend = weighted_pack if blend is None else blend + weighted_pack
    return blend

