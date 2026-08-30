import uuid
from typing import List, Tuple

from .pipelines.description_generator import DescriptionGenerator
from .pipelines.image_enhancer import ImageEnhancer
from .pipelines.publisher import ChannelPublisher
from .. import schemas


class ListingOrchestrator:
    """Thin coordination layer that chains the enhancement, copywriting, pricing and publishing steps."""

    def __init__(
        self,
        enhancer: ImageEnhancer,
        copywriter: DescriptionGenerator,
        publisher: ChannelPublisher,
    ) -> None:
        self._enhancer = enhancer
        self._copywriter = copywriter
        self._publisher = publisher

    async def create_listing(
        self, payload: schemas.ListingRequest
    ) -> schemas.ListingResponse:
        listing_id = str(uuid.uuid4())
        enhanced_assets = await self._enhancer.process(listing_id, payload.assets)

        preview_description, suggested_price = await self._copywriter.generate(
            listing_id=listing_id,
            request=payload,
            enhanced_assets=enhanced_assets,
        )

        publish_results = await self._publisher.schedule_publication(
            listing_id=listing_id,
            request=payload,
            enhanced_assets=enhanced_assets,
            description=preview_description,
            recommended_price=suggested_price,
        )

        status = schemas.ListingStatus(
            listing_id=listing_id,
            state="publishing" if publish_results.pending else "live",
            platforms_live=publish_results.confirmed_platforms,
            notes=publish_results.notes,
        )

        return schemas.ListingResponse(
            status=status,
            recommended_price=suggested_price,
            preview_description=preview_description,
            enhanced_assets=enhanced_assets,
        )


class PublishResult:
    def __init__(
        self,
        pending: bool,
        confirmed_platforms: List[schemas.PlatformEnum],
        notes: str = "",
    ) -> None:
        self.pending = pending
        self.confirmed_platforms = confirmed_platforms
        self.notes = notes
