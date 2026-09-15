from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PlatformEnum(str, Enum):
    craigslist = "craigslist"
    mercari = "mercari"
    nextdoor = "nextdoor"
    offerup = "offerup"
    custom = "custom"


class SellerPreference(BaseModel):
    tone: Optional[str] = Field(
        None,
        description="Preferred copy tone (e.g., premium, playful, concise)",
    )
    min_price: Optional[float] = Field(
        None,
        description="Lowest acceptable price for auto-negotiation guardrails",
    )
    target_price: Optional[float] = Field(
        None,
        description="Ideal listing price suggested to pricing agent",
    )
    pickup_only: Optional[bool] = Field(
        False, description="If true, restrict listings to local pickup"
    )


class ListingAsset(BaseModel):
    source_uri: Optional[HttpUrl] = Field(
        None, description="Publicly accessible URL for the uploaded asset."
    )
    base64_payload: Optional[str] = Field(
        None,
        description="Optional base64 encoded asset body when direct upload is used.",
    )
    caption: Optional[str] = Field(None, description="User-provided caption or note.")


class ListingRequest(BaseModel):
    title_hint: Optional[str] = Field(
        None, description="Optional working title supplied by the seller."
    )
    raw_description: str = Field(
        ..., description="Free-form notes describing the item, condition, and story."
    )
    category: Optional[str] = Field(
        None, description="High-level category to help routing (e.g., furniture)."
    )
    location: Optional[str] = Field(
        None, description="City/region for localized marketplaces."
    )
    assets: List[ListingAsset] = Field(
        default_factory=list, description="Collection of reference photos/videos."
    )
    target_platforms: List[PlatformEnum] = Field(
        default_factory=lambda: [PlatformEnum.craigslist],
        description="Marketplaces that should receive this listing.",
    )
    preferences: SellerPreference = Field(
        default_factory=SellerPreference,
        description="Preferences controlling tone, pricing, negotiations.",
    )


class ListingStatus(BaseModel):
    listing_id: str = Field(..., description="Internal tracking identifier.")
    state: str = Field(
        ...,
        description="State machine stage (ingesting, enhancing, drafting, publishing, live, closed).",
    )
    platforms_live: List[PlatformEnum] = Field(
        default_factory=list, description="Platforms with confirmed publication."
    )
    notes: Optional[str] = Field(None, description="Additional context for the seller.")


class ListingResponse(BaseModel):
    status: ListingStatus
    recommended_price: Optional[float] = Field(
        None, description="Initial suggestion from valuation pipeline."
    )
    preview_description: Optional[str] = Field(
        None, description="First-pass marketing copy preview."
    )
    enhanced_assets: List[str] = Field(
        default_factory=list,
        description="URIs for enhanced images stored in object storage.",
    )
