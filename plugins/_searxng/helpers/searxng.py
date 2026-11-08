NOT_IMPLEMENTED_MESSAGE = "the searxng plugin is not yet fully implemented"


async def search(query: str) -> str:
    """Return the placeholder result without contacting a search service."""
    del query
    return NOT_IMPLEMENTED_MESSAGE
