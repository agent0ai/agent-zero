import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, async_playwright


@dataclass
class GoogleVoiceConfig:
    user_data_dir: str
    headless: bool = False


class GoogleVoiceSession:
    def __init__(self, config: GoogleVoiceConfig) -> None:
        self.config = config
        self._lock = asyncio.Lock()
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def ensure(self) -> Page:
        async with self._lock:
            if self._page:
                return self._page
            Path(self.config.user_data_dir).mkdir(parents=True, exist_ok=True)
            self._playwright = await async_playwright().start()
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.user_data_dir,
                headless=self.config.headless,
            )
            pages = self._context.pages
            self._page = pages[0] if pages else await self._context.new_page()
            await self._page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")
            return self._page

    async def close(self) -> None:
        async with self._lock:
            if self._context:
                await self._context.close()
            if self._playwright:
                await self._playwright.stop()
            self._context = None
            self._playwright = None
            self._page = None

    async def send_sms(self, to_number: str, body: str) -> None:
        page = await self.ensure()
        await page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")

        await self._click_first(
            page,
            [
                'button[aria-label="Send a message"]',
                'button[aria-label="New message"]',
                'a[aria-label="Send a message"]',
                'button:has-text("Send a message")',
                'button:has-text("New message")',
            ],
        )

        await self._fill_first(
            page,
            [
                'input[aria-label="To"]',
                'input[aria-label="Recipients"]',
                'input[aria-label="Number"]',
                'input[placeholder="Name or number"]',
            ],
            to_number,
        )

        await page.keyboard.press("Enter")

        await self._fill_first(
            page,
            [
                'textarea[aria-label="Type a message"]',
                'textarea[aria-label="Message"]',
                'textarea[placeholder="Type a message"]',
                'div[role="textbox"]',
            ],
            body,
        )

        await self._click_first(
            page,
            [
                'button[aria-label="Send message"]',
                'button[aria-label="Send SMS"]',
                'button:has-text("Send")',
            ],
        )

    async def fetch_inbox(self, limit: int = 10) -> list[dict[str, object]]:
        page = await self.ensure()
        await page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        items = await page.query_selector_all('div[role="listitem"]')
        results: list[dict[str, object]] = []
        for item in items[:limit]:
            text = (await item.text_content()) or ""
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if not lines:
                continue
            from_number = lines[0]
            body = lines[-1] if len(lines) > 1 else ""
            thread_context = await self._read_thread_context(item, page)
            results.append(
                {
                    "from_number": from_number,
                    "body": body,
                    "thread_context": thread_context,
                }
            )
        return results

    async def _read_thread_context(self, item: object, page: Page) -> str | None:
        try:
            await item.click()
            await page.wait_for_timeout(800)
            selectors = [
                'div[aria-label="Conversation"] div[role="listitem"]',
                'div[role="main"] div[role="listitem"]',
            ]
            for selector in selectors:
                nodes = await page.query_selector_all(selector)
                if not nodes:
                    continue
                messages: list[str] = []
                for node in nodes[-6:]:
                    text = (await node.text_content()) or ""
                    text = " ".join([line.strip() for line in text.splitlines() if line.strip()])
                    if text:
                        messages.append(text)
                if messages:
                    return "\n".join(messages)
        except Exception:
            return None
        return None

    async def _click_first(self, page: Page, selectors: Iterable[str]) -> None:
        last_error = None
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=4000)
                await page.click(selector)
                return
            except PlaywrightTimeoutError as exc:
                last_error = exc
        if last_error:
            raise RuntimeError("Unable to locate Google Voice button; UI may have changed.") from last_error

    async def _fill_first(self, page: Page, selectors: Iterable[str], value: str) -> None:
        last_error = None
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=4000)
                await page.fill(selector, value)
                return
            except PlaywrightTimeoutError as exc:
                last_error = exc
        if last_error:
            raise RuntimeError("Unable to locate Google Voice input field; UI may have changed.") from last_error


_session: GoogleVoiceSession | None = None


def get_google_voice_session(user_data_dir: str, headless: bool = False) -> GoogleVoiceSession:
    global _session
    if _session is None:
        _session = GoogleVoiceSession(GoogleVoiceConfig(user_data_dir=user_data_dir, headless=headless))
    return _session
