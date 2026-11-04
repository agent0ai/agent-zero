import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests

ANYSEARCH_BASE_URL = "https://api.anysearch.com"
ANYSEARCH_MAX_RESULTS = 10
ANYSEARCH_TIMEOUT = 30


class AnySearchError(Exception):
    """Raised when an AnySearch request does not succeed."""


def api_key() -> str:
    """Return the configured AnySearch API key, or "" for anonymous use."""
    return os.getenv("ANYSEARCH_API_KEY", "").strip()


def _headers() -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "agent-zero/anysearch",
    }
    key = api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _post(endpoint: str, payload: dict) -> dict:
    try:
        response = requests.post(
            ANYSEARCH_BASE_URL + endpoint,
            json=payload,
            headers=_headers(),
            timeout=ANYSEARCH_TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as e:
        raise AnySearchError(f"{endpoint} request failed: {str(e)}") from e

    if not isinstance(body, dict):
        raise AnySearchError(f"{endpoint} returned a non-object body")

    code = body.get("code", 0)
    if code != 0:
        raise AnySearchError(
            f"{endpoint} returned code {code}: "
            f"{body.get('message', 'no message')}"
        )

    data = body.get("data")
    if not isinstance(data, dict):
        raise AnySearchError(f"{endpoint} returned no data object")
    return data


def search(
    query: str,
    max_results: int = ANYSEARCH_MAX_RESULTS,
    tag: str = "",
    params: dict | None = None,
    zone: str = "",
    language: str = "",
) -> list[dict]:
    """Run a web search and return normalized results.

    Each result has the keys ``title``, ``url``, ``snippet`` and
    ``content``. ``content`` holds the parsed page body, so the agent
    usually does not need a separate fetch step.

    Anonymous access works: with no API key the request is rate limited
    per IP but otherwise succeeds.

    Args:
        query: The search query.
        max_results: Maximum number of results, clamped to [1, 10].
        tag: Vertical domain tag, for example ``"code.doc"``.
        params: Tag specific parameters, for example ``{"library":
            "golang"}``. Some tags reject a request without them.
        zone: ``"cn"`` or ``"intl"``; empty means the server default.
        language: Language code, empty means the server default.

    Raises:
        AnySearchError: On transport failure or a business error.
        ValueError: If zone is not empty, ``"cn"`` or ``"intl"``.
    """
    if zone and zone not in ("cn", "intl"):
        raise ValueError(f"Invalid zone: {zone}. Use 'cn' or 'intl'.")

    limit = max(1, min(int(max_results), ANYSEARCH_MAX_RESULTS))
    payload: dict = {
        "query": query,
        "max_results": limit,
        "format": "markdown",
    }
    if tag:
        payload["tag"] = tag
    if params:
        payload["params"] = params
    if zone:
        payload["zone"] = zone
    if language:
        payload["language"] = language

    raw = _post("/v1/search", payload).get("results", [])
    if not isinstance(raw, list):
        raise AnySearchError("/v1/search returned no results list")

    results = []
    for item in raw[:limit]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "snippet": str(item.get("snippet", "")),
                "content": str(item.get("content", "")),
            }
        )
    return results


def search_parallel(
    queries: list[str],
    max_results: int = ANYSEARCH_MAX_RESULTS,
    max_workers: int = 4,
    tag: str = "",
    params: dict | None = None,
    zone: str = "",
    language: str = "",
) -> dict[str, list[dict]]:
    """Run several searches concurrently and return one list per query.

    AnySearch exposes no batch endpoint, so parallel search is done by
    issuing one request per query from a thread pool. Duplicate queries
    are collapsed and the mapping follows the input order.

    A query that fails maps to an empty list instead of aborting the whole
    batch: one bad query must not destroy the results of the others, which
    is exactly why a caller would fan out in the first place.

    Args:
        queries: The queries to execute.
        max_results: Maximum number of results per query.
        max_workers: Size of the thread pool.
        tag: Vertical domain tag applied to every query, for example
            ``"code.doc"``.
        params: Tag specific parameters applied to every query.
        zone: ``"cn"`` or ``"intl"``; empty means the server default.
        language: Language code, empty means the server default.

    Returns:
        dict[str, list[dict]]: Mapping from query to its result list.

    Raises:
        ValueError: If zone is not empty, ``"cn"`` or ``"intl"``.
    """
    if zone and zone not in ("cn", "intl"):
        raise ValueError(f"Invalid zone: {zone}. Use 'cn' or 'intl'.")

    unique_queries = list(dict.fromkeys(queries))
    if not unique_queries:
        return {}

    workers = max(1, min(int(max_workers), len(unique_queries)))

    def run(query: str) -> list[dict]:
        try:
            return search(
                query=query,
                max_results=max_results,
                tag=tag,
                params=params,
                zone=zone,
                language=language,
            )
        except Exception:
            # Failure isolation: one query must not sink the batch.
            return []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        batches = list(pool.map(run, unique_queries))
    return dict(zip(unique_queries, batches))


def extract(url: str) -> dict:
    """Fetch a web page and return its parsed content.

    Args:
        url: Absolute HTTP/HTTPS URL of the page to parse.

    Returns:
        dict: With the keys ``url``, ``title`` and ``content``.

    Raises:
        AnySearchError: On transport failure or a business error.
        ValueError: If url is not an absolute HTTP/HTTPS URL.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    data = _post("/v1/extract", {"url": url})
    return {
        "url": str(data.get("url", url)),
        "title": str(data.get("title", "")),
        "content": str(data.get("content", "")),
    }
