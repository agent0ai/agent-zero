from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List

from ... import schemas
from ..orchestrator import PublishResult


@dataclass
class PublicationTask:
    platform: schemas.PlatformEnum
    status: str
    reference_id: str


class ChannelPublisher:
    """
    Stubbed marketplace publisher.
    Replace with real adapters (Craigslist headless automation, Mercari API, etc.).
    """

    async def schedule_publication(
        self,
        listing_id: str,
        request: schemas.ListingRequest,
        enhanced_assets: List[str],
        description: str,
        recommended_price: float,
    ) -> PublishResult:
        await asyncio.sleep(0.1)
        confirmed: List[schemas.PlatformEnum] = []
        pending = False

        for platform in request.target_platforms:
            if platform in (schemas.PlatformEnum.craigslist, schemas.PlatformEnum.nextdoor):
                # emulate asynchronous approval queues for certain platforms
                pending = True
            else:
                confirmed.append(platform)

        notes = (
            "Some platforms require manual review before going live."
            if pending
            else "All requested platforms confirmed."
        )

        return PublishResult(
            pending=pending,
            confirmed_platforms=confirmed,
            notes=notes,
        )
