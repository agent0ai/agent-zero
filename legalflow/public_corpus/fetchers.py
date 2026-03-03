from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

import ssl


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int | None
    text: str | None
    error: str | None = None


class Fetcher(Protocol):
    def fetch_text(self, url: str) -> FetchResult: ...


class HttpFetcher:
    def __init__(self, *, user_agent: str | None = None, timeout_s: float = 30.0):
        self._timeout_s = timeout_s
        self._user_agent = user_agent or "legalflow-ingest/0.1"
        self._ssl_context = _build_ssl_context()

    def fetch_text(self, url: str) -> FetchResult:
        req = Request(url, headers={"User-Agent": self._user_agent})
        try:
            with urlopen(req, timeout=self._timeout_s, context=self._ssl_context) as resp:  # noqa: S310
                status = getattr(resp, "status", None)
                data = resp.read()
                encoding = resp.headers.get_content_charset() or "utf-8"
                text = data.decode(encoding, "replace")
                return FetchResult(url=url, status=status, text=text)
        except HTTPError as e:
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                body = None
            return FetchResult(url=url, status=e.code, text=body, error=str(e))
        except URLError as e:
            return FetchResult(url=url, status=None, text=None, error=str(e))
        except Exception as e:
            return FetchResult(url=url, status=None, text=None, error=str(e))


class PlaywrightFetcher:
    def __init__(self, *, timeout_ms: int = 45000):
        self._timeout_ms = timeout_ms

    def fetch_text(self, url: str) -> FetchResult:
        try:
            from python.helpers import files
            from python.helpers.playwright import ensure_playwright_binary

            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", files.get_abs_path("tmp/playwright"))
            pw_binary = ensure_playwright_binary()

            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path=str(pw_binary))
                try:
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=self._timeout_ms)
                    time.sleep(0.2)
                    html = page.content()
                    return FetchResult(url=url, status=200, text=html)
                finally:
                    browser.close()
        except Exception as e:
            return FetchResult(url=url, status=None, text=None, error=str(e))


class AutoFetcher:
    def __init__(self):
        self._http = HttpFetcher()
        self._pw = PlaywrightFetcher()

    def fetch_text(self, url: str) -> FetchResult:
        first = self._http.fetch_text(url)
        host = (urlparse(url).hostname or "").lower()
        should_try_playwright = False
        if first.status == 403:
            should_try_playwright = True
        elif host.endswith("stf.jus.br") and (first.status is None or (first.status and first.status >= 400)):
            # STF often blocks/breaks from this environment (403) and can also
            # fail certificate validation depending on the local Python install.
            should_try_playwright = True
        elif first.text is None and first.error:
            if "CERTIFICATE_VERIFY_FAILED" in first.error:
                should_try_playwright = True

        if should_try_playwright:
            second = self._pw.fetch_text(url)
            if second.text:
                return second
        return first


def _build_ssl_context() -> ssl.SSLContext:
    """
    Build an SSL context that uses certifi when available.

    Some environments (notably macOS/Homebrew Python) may not have a usable
    system CA bundle configured, causing CERTIFICATE_VERIFY_FAILED for some sites.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
