"""Exercise real CDP on an isolated profile using an installed Chromium."""
from contextlib import asynccontextmanager
import os
import shutil

import pytest

from plugins._browser.sandbox.cdp import CDPContext


@asynccontextmanager
async def chromium(profile, proxy=None, *, restore_session=False):
    candidates = ("a0-chromium", "chromium", "google-chrome", "chromium-browser")
    executable = os.environ.get("CHROMIUM_BINARY") or next(
        (path for name in candidates if (path := shutil.which(name))), None
    )
    if not executable:
        pytest.skip("Set CHROMIUM_BINARY to run the native Chromium tests")
    args = [
        "--headless", "--no-sandbox", "--no-first-run", "--disable-background-networking",
        "--no-default-browser-check", "--disable-dev-shm-usage", "--disable-sync",
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1",
        f"--user-data-dir={profile}", "--restore-last-session" if restore_session else "about:blank",
    ]
    context = await CDPContext.launch(executable, args, proxy=proxy)
    try:
        yield context
    finally:
        await context.close()


@pytest.fixture
async def native_page(tmp_path):
    async with chromium(tmp_path / 'profile') as browser:
        page = browser.pages[0]
        html = tmp_path / 'index.html'
        html.write_text('<!doctype html><title>Browser fixture</title><body></body>', encoding='utf-8')
        await page.goto(html.as_uri())
        yield page
