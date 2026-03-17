from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import async_playwright


@dataclass
class RenderResult:
    url: str
    final_url: str
    title: str
    html: str
    screenshot_path: str | None = None


async def _render_url_async(
    url: str,
    *,
    screenshot_path: str | None = None,
    viewport_width: int = 1200,
    viewport_height: int = 900,
    timeout_ms: int = 30000,
) -> RenderResult:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-http2"])
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        title = (await page.title()) or ""
        final_url = page.url
        html = await page.content()
        if screenshot_path:
            p = Path(screenshot_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(p), full_page=False)
        await context.close()
        await browser.close()
        return RenderResult(
            url=url,
            final_url=final_url,
            title=title,
            html=html,
            screenshot_path=screenshot_path,
        )


async def render_url_async(
    url: str,
    *,
    screenshot_path: str | None = None,
    viewport_width: int = 1200,
    viewport_height: int = 900,
    timeout_ms: int = 30000,
) -> RenderResult:
    return await _render_url_async(
        url,
        screenshot_path=screenshot_path,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        timeout_ms=timeout_ms,
    )


def render_url(
    url: str,
    *,
    screenshot_path: str | None = None,
    viewport_width: int = 1200,
    viewport_height: int = 900,
    timeout_ms: int = 30000,
) -> RenderResult:
    """
    Synchronous wrapper for GUI/CLI use.
    """
    return asyncio.run(
        _render_url_async(
            url,
            screenshot_path=screenshot_path,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            timeout_ms=timeout_ms,
        )
    )

