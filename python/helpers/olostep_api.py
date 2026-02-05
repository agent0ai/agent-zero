"""
Olostep API Helper Module for Agent Zero

This module provides functions to interact with the Olostep API for:
- Web scraping (get markdown, HTML, text, or structured JSON from any URL)
- Web search and answers (get AI-powered answers with sources)
- Website mapping (get all URLs on a website)

API Documentation: https://docs.olostep.com
"""

import aiohttp
from typing import Optional, Any
import models


OLOSTEP_API_BASE = "https://api.olostep.com"


def get_api_key() -> str:
    """
    Get the Olostep API key using Agent Zero's standard API key mechanism.
    The key can be configured through:
    - The Web UI: Settings > API Keys > Olostep
    - Environment variable: OLOSTEP_API_KEY or API_KEY_OLOSTEP
    """
    return models.get_api_key("olostep")


def _get_headers() -> dict:
    """Get the headers for Olostep API requests."""
    api_key = get_api_key()
    if not api_key or api_key == "None":
        raise ValueError(
            "Olostep API key not found. Please configure it in Settings > API Keys > Olostep."
        )
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

async def scrape_url(
    url: str,
    formats: list[str] = ["markdown"],
    wait_before_scraping: int = 0,
    remove_css_selectors: str = "default",
    parser_id: Optional[str] = None,
    country: Optional[str] = None,
) -> dict[str, Any]:
    """
    Scrape a URL and return its content in specified formats.
    
    Args:
        url: The URL to scrape
        formats: Output formats - "markdown", "html", "text", "json", "screenshot"
        wait_before_scraping: Milliseconds to wait before scraping (for JS-heavy sites)
        remove_css_selectors: "default", "none", or specific selectors to remove
        parser_id: Optional parser ID for structured JSON extraction (e.g., "@olostep/google-search")
        country: Optional country code for geo-specific scraping (e.g., "US", "GB")
    
    Returns:
        Dictionary containing the scraped content with keys like:
        - markdown_content, html_content, text_content, json_content
        - Various hosted URLs for the content
        - links_on_page, page_metadata
    """
    endpoint = f"{OLOSTEP_API_BASE}/v1/scrapes"
    
    payload = {
        "url_to_scrape": url,
        "formats": formats,
    }
    
    if wait_before_scraping > 0:
        payload["wait_before_scraping"] = wait_before_scraping
    
    if remove_css_selectors:
        payload["remove_css_selectors"] = remove_css_selectors
    
    if parser_id:
        payload["parser"] = {"id": parser_id}
    
    if country:
        payload["country"] = country
    
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=_get_headers()) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Olostep API error ({response.status}): {error_text}")
            return await response.json()


async def get_answer(
    task: str,
    json_format: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Search the web and get an AI-powered answer with sources.
    
    Args:
        task: The question or task to answer (e.g., "What is the latest book by J.K. Rowling?")
        json_format: Optional JSON schema to structure the response
    
    Returns:
        Dictionary containing:
        - result.json_content: The answer in JSON format
        - result.json_hosted_url: Hosted URL for the answer
        - sources: List of sources used
    """
    endpoint = f"{OLOSTEP_API_BASE}/v1/answers"
    
    payload = {"task": task}
    
    if json_format:
        payload["json_format"] = json_format
    
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=_get_headers()) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Olostep API error ({response.status}): {error_text}")
            return await response.json()


async def map_website(
    url: str,
    include_urls: Optional[list[str]] = None,
    exclude_urls: Optional[list[str]] = None,
    top_n: Optional[int] = None,
) -> dict[str, Any]:
    """
    Get all URLs on a website.
    
    Args:
        url: The website URL to map
        include_urls: Glob patterns for URLs to include (e.g., ["/blog/**"])
        exclude_urls: Glob patterns for URLs to exclude
        top_n: Limit the number of URLs returned
    
    Returns:
        Dictionary containing:
        - urls: List of discovered URLs
        - cursor: Pagination cursor if more results available
    """
    endpoint = f"{OLOSTEP_API_BASE}/v1/maps"
    
    payload = {"url": url}
    
    if include_urls:
        payload["include_urls"] = include_urls
    
    if exclude_urls:
        payload["exclude_urls"] = exclude_urls
    
    if top_n:
        payload["top_n"] = top_n
    
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=_get_headers()) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Olostep API error ({response.status}): {error_text}")
            return await response.json()


async def google_search(
    query: str,
    country: str = "us",
    language: str = "en",
    num_results: int = 10,
) -> dict[str, Any]:
    """
    Perform a Google search and get structured results.
    
    Args:
        query: The search query
        country: Country code (e.g., "us", "uk", "de")
        language: Language code (e.g., "en", "es", "de")
        num_results: Number of results to return
    
    Returns:
        Dictionary containing structured search results with:
        - organic_results: List of search results with title, url, description
        - ai_overview: AI-generated overview if available
        - related_searches, people_also_ask, etc.
    """
    # Build Google search URL
    search_url = f"https://www.google.com/search?q={query}&gl={country}&hl={language}&num={num_results}"
    
    return await scrape_url(
        url=search_url,
        formats=["json"],
        parser_id="@olostep/google-search",
    )
