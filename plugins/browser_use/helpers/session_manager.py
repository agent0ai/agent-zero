"""Shared browser session lifecycle manager.

One SessionManager per agent context. Stores itself in agent.get_data('_browser_use_session').
Both tools (browser_step, browser_auto) and the WebUI viewer share this session.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from python.helpers.browser_use import browser_use
from python.helpers import files
from python.helpers.print_style import PrintStyle

if TYPE_CHECKING:
    from agent import Agent

_STORAGE_KEY = "_browser_use_session"


class SessionManager:
    """Manages a single shared browser session for an agent context."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.lock = asyncio.Lock()
        self._closed = False

    # -- Factory / retrieval ------------------------------------------------

    @staticmethod
    def get_or_create(agent: Agent) -> SessionManager:
        """Retrieve existing session or create a new one for this agent context."""
        existing = agent.get_data(_STORAGE_KEY)
        if existing and isinstance(existing, SessionManager) and not existing._closed:
            return existing
        manager = SessionManager(agent)
        agent.set_data(_STORAGE_KEY, manager)
        return manager

    @staticmethod
    def get_existing(agent: Agent) -> Optional[SessionManager]:
        """Retrieve existing session without creating. Returns None if no session."""
        existing = agent.get_data(_STORAGE_KEY)
        if existing and isinstance(existing, SessionManager) and not existing._closed:
            return existing
        return None

    # -- Properties ---------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        return self.browser_session is not None and not self._closed

    @property
    def is_busy(self) -> bool:
        return self.lock.locked()

    @property
    def cdp_ws_url(self) -> Optional[str]:
        """CDP URL of the running browser, available after start."""
        if self.browser_session:
            return self.browser_session.cdp_url
        return None

    # -- Lifecycle ----------------------------------------------------------

    async def ensure_started(self) -> None:
        """Start the browser if not already running (double-checked locking)."""
        if self.browser_session and not self._closed:
            return
        async with self.lock:
            if self.browser_session and not self._closed:
                return
            await self._start_browser()

    async def _start_browser(self) -> None:
        """Launch Chromium via browser-use and let it handle CDP setup."""
        user_data_dir = self._get_user_data_dir()

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=False,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_path=files.get_abs_path("usr/downloads"),
                keep_alive=True,
                minimum_wait_page_load_time=1.0,
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=10.0,
                window_size={"width": 1024, "height": 768},
                screen={"width": 1024, "height": 768},
                viewport={"width": 1024, "height": 768},
                no_viewport=False,
                user_data_dir=user_data_dir,
                # Note: executable_path intentionally omitted for headed mode.
                # browser-use discovers system Chromium via Playwright defaults.
                # The headless_shell from ensure_playwright_binary() cannot run headed.
            )
        )

        await self.browser_session.start()
        self._closed = False

        PrintStyle().print(f"Browser session started. CDP: {self.cdp_ws_url}")

    # -- Page access --------------------------------------------------------

    async def get_page(self):
        """Get the current Playwright page object."""
        if self.browser_session:
            try:
                return await self.browser_session.get_current_page()
            except Exception:
                return None
        return None

    async def get_state(self) -> dict:
        """Get current browser state (URL, title, busy flag)."""
        page = await self.get_page()
        if not page:
            return {"alive": False, "url": "", "title": "", "busy": self.is_busy}

        try:
            return {
                "alive": True,
                "url": page.url,
                "title": await page.title(),
                "busy": self.is_busy,
            }
        except Exception:
            return {"alive": True, "url": "", "title": "", "busy": self.is_busy}

    # -- Cleanup ------------------------------------------------------------

    async def close(self) -> None:
        """Close the browser session and clean up."""
        self._closed = True
        if self.browser_session:
            try:
                await self.browser_session.close()
            except Exception as e:
                PrintStyle().warning(f"Error closing browser session: {e}")
            finally:
                self.browser_session = None

        # Clean up user data dir
        user_data_dir = self._get_user_data_dir()
        if Path(user_data_dir).exists():
            shutil.rmtree(user_data_dir, ignore_errors=True)

        # Remove from agent data
        self.agent.set_data(_STORAGE_KEY, None)

    # -- Internal helpers ---------------------------------------------------

    def _get_user_data_dir(self) -> str:
        return str(
            Path.home()
            / ".config"
            / "browseruse"
            / "profiles"
            / f"plugin_{self.agent.context.id}"
        )

    # No __del__: cleanup is handled by the agent_init extension
    # and explicit close() calls. Creating a new event loop in __del__
    # can replace the running application loop and corrupt async state.
