from fastapi import FastAPI

from . import schemas
from .services.orchestrator import ListingOrchestrator
from .services.pipelines.description_generator import DescriptionGenerator
from .services.pipelines.image_enhancer import ImageEnhancer
from .services.pipelines.publisher import ChannelPublisher

app = FastAPI(
    title="Autonomous Listing Service",
    description="Transforms seller inputs into multi-channel listings via AI pipelines.",
    version="0.1.0",
)

orchestrator = ListingOrchestrator(
    enhancer=ImageEnhancer(),
    copywriter=DescriptionGenerator(),
    publisher=ChannelPublisher(),
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/listings", response_model=schemas.ListingResponse)
async def create_listing(payload: schemas.ListingRequest) -> schemas.ListingResponse:
    """
    Entry point for creating a new autonomous listing.
    Downstream pipelines are mocked for now and should be replaced with actual AI services.
    """

    return await orchestrator.create_listing(payload)
