from __future__ import annotations

import asyncio
from typing import List

from ... import schemas


class ImageEnhancer:
    """
    Placeholder enhancer that emulates an asynchronous vision pipeline.
    In production, this would call GPU-backed services (Real-ESRGAN, ControlNet, etc.).
    """

    async def process(
        self, listing_id: str, assets: List[schemas.ListingAsset]
    ) -> List[str]:
        if not assets:
            return []

        await asyncio.sleep(0.1)  # simulate async workload
        enhanced_uris = [
            asset.source_uri or f"s3://placeholder/{listing_id}/{idx}.jpg"
            for idx, asset in enumerate(assets)
        ]
        return enhanced_uris
