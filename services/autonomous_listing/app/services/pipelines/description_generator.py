from __future__ import annotations

import asyncio
import random
from typing import List, Tuple

from ... import schemas


class DescriptionGenerator:
    """
    Simplified marketing copy generator.
    Replace with actual LLM/RAG pipeline wired to provider SDKs.
    """

    async def generate(
        self,
        listing_id: str,
        request: schemas.ListingRequest,
        enhanced_assets: List[str],
    ) -> Tuple[str, float]:
        await asyncio.sleep(0.1)
        hero_line = request.title_hint or "Stunning find ready for a new home"
        detail = request.raw_description.strip()
        asset_note = (
            f"Includes {len(enhanced_assets)} professionally enhanced photos."
            if enhanced_assets
            else "Image enhancement pending."
        )

        narrative = (
            f"{hero_line}\n\n"
            f"{detail}\n\n"
            f"{asset_note} Curated for {', '.join([p.value for p in request.target_platforms])}."
        )

        suggested_price = request.preferences.target_price or round(
            random.uniform(20, 200), 2
        )

        return narrative, suggested_price
