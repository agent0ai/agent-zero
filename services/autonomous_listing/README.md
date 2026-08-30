# Autonomous Listing Service (MVP Scaffold)

This folder contains a FastAPI-based microservice that simulates the AI pipeline defined in `docs/autonomous_listing_service.md`. It is not production-ready yet, but it provides a runnable skeleton that:

1. Accepts listing requests with seller notes, assets, preferences, and target platforms.
2. Runs through placeholder pipelines for image enhancement, marketing copy, and multi-platform publishing.
3. Returns a structured preview containing the listing status, suggested price, generated description, and enhanced asset URIs.

## Quick Start

```bash
cd services/autonomous_listing
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

POST a sample request:

```bash
curl -X POST http://localhost:8000/listings \
  -H "Content-Type: application/json" \
  -d '{
    "raw_description": "Mid-century walnut coffee table, gentle wear, includes glass top.",
    "category": "furniture",
    "location": "Austin, TX",
    "assets": [{"source_uri": "https://example.com/photo1.jpg"}],
    "target_platforms": ["craigslist", "mercari"],
    "preferences": {"tone": "premium", "target_price": 350}
  }'
```

## Next Steps
- Replace the stubbed pipelines (`image_enhancer`, `description_generator`, `publisher`) with real AI agents and marketplace adapters.
- Connect to object storage for asset handling and to the knowledge/memory layers described in the main blueprint.
- Embed telemetry + mission diary hooks so the service feeds the agency’s iterative improvement loop.
