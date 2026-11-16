"""Lazy search handoff; SearXNG and its dependencies stay inside the guest."""
from helpers.sandbox_worker import SandboxWorker

worker = SandboxWorker('_searxng')
STARTUP_NOTICE = 'Preparing search engine. First use may take a little while to install dependencies.'


async def search(query: str, progress=None) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 8192:
        raise ValueError('Search query must contain between 1 and 8192 characters')
    if progress and worker.status()['state'] != 'ready':
        progress(STARTUP_NOTICE)
    await worker.aprepare()
    if progress:
        progress('Searching the web')
    return await worker.acall({'query': query}, timeout=60)
