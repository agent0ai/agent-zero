"""
Browser Control Tool - Granular browser control with individual actions.

This tool provides precise browser automation through individual action methods
(navigate, click, type, scroll, observe_page, etc.) following Agent Zero's
tool-based architecture.
"""

import asyncio
import time
from typing import Optional
from dataclasses import dataclass
from agent import Agent, InterventionException
from pathlib import Path

from python.helpers.tool import Tool, Response
from python.helpers import files, persist_chat
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary
from python.helpers.browser_control_client import (
    PlaywrightClient,
    BrowserControlState,
    Action,
    ActionType,
    ActionResult,
)


class BrowserControl(Tool):
    """
    Browser Control tool for granular browser control.

    Provides individual action methods for precise web automation.
    """
    
    async def execute(self, **kwargs) -> Response:
        """
        Execute browser control action based on method name.
        
        Routes to specific methods like navigate, click, type, etc.
        """
        await self.agent.handle_intervention()
        
        # Generate unique GUID for screenshot naming
        self.guid = self.agent.context.generate_id()
        
        method = self.method or "observe_page"
        reset = str(kwargs.get("reset", "false")).lower() == "true"
        
        # Initialize/retrieve state
        await self.prepare_state(reset=reset)
        
        # Route to specific method
        result = None
        try:
            if method == "navigate":
                result = await self._navigate(kwargs.get("url"))
            elif method == "click":
                result = await self._click(kwargs.get("selector"))
            elif method == "type":
                result = await self._type(kwargs.get("selector"), kwargs.get("text"))
            elif method == "scroll":
                result = await self._scroll(kwargs.get("direction", "down"))
            elif method == "observe_page":
                result = await self._observe_page()
            elif method == "select":
                result = await self._select(kwargs.get("selector"), kwargs.get("value"))
            elif method == "press":
                result = await self._press(kwargs.get("selector"), kwargs.get("key"))
            elif method == "hover":
                result = await self._hover(kwargs.get("selector"))
            elif method == "pause_for_user":
                result = await self._pause_for_user(
                    kwargs.get("wait_seconds", 60),
                    kwargs.get("message", "Pausing for user interaction...")
                )
            elif method == "get_browser_info":
                result = await self._get_browser_info()
            else:
                result = f"Unknown method: {method}. Available methods: navigate, click, type, scroll, observe_page, select, press, hover, pause_for_user, get_browser_info"
            
            # Capture screenshot after action (UI display)
            await self._capture_screenshot(method)
            
        except Exception as e:
            result = f"Error executing {method}: {str(e)}"
            PrintStyle().error(result)
        
        if not result:
            result = f"Method {method} completed but returned no output"
        
        return Response(message=result, break_loop=False)
    
    async def prepare_state(self, reset: bool = False):
        """
        Initialize or retrieve Playwright state.
        
        Follows pattern from code_execution_tool state management.
        """
        self.state: Optional[BrowserControlState] = self.agent.get_data("_browser_control_state")

        if reset and self.state and self.state.client:
            # Close existing session
            try:
                await self.state.client.close()
            except Exception as e:
                PrintStyle().warning(f"Error closing existing session: {e}")
            self.state = None
        
        if not self.state or not self.state.initialized:
            # Create new Playwright session
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                raise ImportError(
                    "Playwright is not installed. Install with: pip install playwright"
                )
            
            # Get Playwright binary path (only needed if not using CDP)
            cdp_url = self.agent.config.browser_control_cdp_url
            pw_binary = None if cdp_url else ensure_playwright_binary()

            # Check if VNC is available and enabled
            import os
            use_vnc = os.path.exists('/tmp/vnc/status') and not cdp_url
            vnc_display = os.environ.get('VNC_DISPLAY', ':99') if use_vnc else None

            # Create client
            client = PlaywrightClient(
                start_url=self.agent.config.browser_control_start_url,
                headless=self.agent.config.browser_control_headless,
                playwright_binary=str(pw_binary) if pw_binary else None,
                cdp_url=cdp_url if cdp_url else None,
                use_vnc=use_vnc,
                vnc_display=vnc_display
            )
            
            # Initialize browser
            await client.initialize()
            
            # Create state
            self.state = BrowserControlState(
                playwright=client.playwright,
                browser=client.browser,
                context=client.context,
                page=client.page,
                client=client,
                initialized=True
            )
            
            self.agent.set_data("_browser_control_state", self.state)

        return self.state

    async def _get_state(self) -> Optional[BrowserControlState]:
        """Helper to get current state."""
        return self.agent.get_data("_browser_control_state")
    
    async def _navigate(self, url: Optional[str]) -> str:
        """Navigate to a URL with fallback handling."""
        if not url:
            return "Error: URL is required for navigate action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.NAVIGATE, value=url)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Navigation failed: {result.error}"
    
    async def _click(self, selector: Optional[str]) -> str:
        """Click element with selector strategies and text fallback."""
        if not selector:
            return "Error: Selector is required for click action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.CLICK, selector=selector)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Click failed: {result.error}. Try a different selector or text content."
    
    async def _type(self, selector: Optional[str], text: Optional[str]) -> str:
        """Type text into input field."""
        if not selector:
            return "Error: Selector is required for type action"
        if not text:
            return "Error: Text is required for type action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.TYPE, selector=selector, value=text)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Type failed: {result.error}"
    
    async def _scroll(self, direction: str = "down") -> str:
        """Scroll page up/down/left/right."""
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.SCROLL, value=direction)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Scroll failed: {result.error}"
    
    async def _select(self, selector: Optional[str], value: Optional[str]) -> str:
        """Select option from dropdown."""
        if not selector:
            return "Error: Selector is required for select action"
        if not value:
            return "Error: Value is required for select action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.SELECT, selector=selector, value=value)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Select failed: {result.error}"
    
    async def _press(self, selector: Optional[str], key: Optional[str]) -> str:
        """Press keyboard key on element."""
        if not selector:
            return "Error: Selector is required for press action"
        if not key:
            return "Error: Key is required for press action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.PRESS, selector=selector, value=key)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Press failed: {result.error}"
    
    async def _hover(self, selector: Optional[str]) -> str:
        """Hover over element."""
        if not selector:
            return "Error: Selector is required for hover action"
        
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"
        
        action = Action(action_type=ActionType.HOVER, selector=selector)
        result = await state.client.execute_action(action)
        
        if result.success:
            return result.description
        else:
            return f"Hover failed: {result.error}"
    
    async def _observe_page(self) -> str:
        """
        Extract page content and add screenshot to LLM context.
        
        This method provides semantic content extraction and adds
        screenshot to agent history for vision model analysis.
        """
        state = await self._get_state()
        if not state or not state.client or not state.client.page:
            return "Error: Browser not initialized"
        
        page = state.client.page
        
        # Build description of the page
        try:
            description = f"URL: {page.url}\n"
            description += f"Title: {await page.title()}\n\n"
            
            # Extract semantic content (headings, articles, main content)
            content_data = await page.evaluate(
                """
                () => {
                    // Extract headings
                    const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
                        .slice(0, 10)
                        .map(h => `${h.tagName}: ${h.innerText.trim()}`)
                        .filter(h => h.length > 5);
                    
                    // Extract article content or main content
                    let mainText = '';
                    const article = document.querySelector('article, main, [role="main"]');
                    if (article) {
                        mainText = article.innerText.substring(0, 5000);
                    } else {
                        mainText = document.body.innerText.substring(0, 5000);
                    }
                    
                    return {
                        headings: headings,
                        text: mainText
                    };
                }
                """
            )
            
            # Format the content
            if content_data.get("headings"):
                description += "Key headings:\n"
                for heading in content_data["headings"][:8]:
                    description += f"  {heading}\n"
                description += "\n"
            
            if content_data.get("text"):
                description += f"Page content:\n{content_data['text']}\n\n"
            
            # Get interactive elements
            interface_state = await state.client.get_state("text")
            if interface_state.interactive_elements:
                description += f"Interactive elements: {len(interface_state.interactive_elements)} found\n"
                description += "Key elements:\n"
                # Filter for meaningful elements
                meaningful_elements = [
                    elem
                    for elem in interface_state.interactive_elements[:15]
                    if elem.get("text", "").strip()
                    and len(elem.get("text", "").strip()) > 2
                ]
                for elem in meaningful_elements[:10]:
                    text = elem.get("text", "").strip()[:50]
                    tag = elem.get("tag", "")
                    if text:
                        description += f"  - {tag}: {text}\n"
            
            # Add screenshot to agent history for vision model analysis
            if self.agent.config.chat_model.vision:
                try:
                    screenshot_b64 = await state.client.get_screenshot_base64()
                    # Add to history as multimodal content
                    self.agent.hist_add_message(
                        False,  # Not user message
                        content={
                            "role": "user",
                            "type": "image",
                            "image": screenshot_b64,
                            "description": f"Screenshot of current page: {page.url}"
                        }
                    )
                except Exception as e:
                    PrintStyle().warning(f"Could not add screenshot to context: {e}")
            
            return description

        except Exception as e:
            return f"Error extracting page content: {str(e)}"

    async def _pause_for_user(self, wait_seconds: int = 60, message: str = "Pausing for user interaction...") -> str:
        """
        Pause execution to allow user to manually interact with the browser.

        This is useful for:
        - Solving CAPTCHAs
        - Manual login when automation is blocked
        - Accepting cookies/terms manually
        - Any other manual intervention needed

        Args:
            wait_seconds: How long to wait for user interaction (default 60 seconds)
            message: Custom message to display to user

        Note: If VNC is enabled, a URL will be provided for browser access.
        """
        state = await self._get_state()
        if not state or not state.client:
            return "Error: Browser not initialized"

        # Check for VNC URL first
        vnc_url = state.client.get_vnc_url(host="localhost", port=56080)

        # Build initial message with VNC URL
        initial_message = f"⏸️  **Browser Pause Requested**\n\n{message}\n\n"

        if vnc_url:
            initial_message += f"🌐 **Control Browser**: {vnc_url}\n\n"
            initial_message += "Click the link above to access the browser and complete the manual task.\n"
            initial_message += f"⏱️  Waiting up to {wait_seconds} seconds for you to complete the task...\n\n"
            initial_message += "The browser control panel should open automatically in the web interface."
        else:
            initial_message += "⚠️  VNC is not available. Browser should be visible on your display.\n"
            initial_message += f"⏱️  Waiting up to {wait_seconds} seconds..."

        # Update log with initial message so frontend can show browser panel
        self.log.update(message=initial_message)

        # Call the client to mark the pause (returns immediately now)
        action = Action(
            action_type=ActionType.PAUSE_FOR_USER,
            value=str(wait_seconds),
            metadata={"message": message}
        )
        result = await state.client.execute_action(action)

        if not result.success:
            return f"Pause failed: {result.error}"

        # Now actually pause/wait at the Agent level
        import asyncio
        PrintStyle().info(f"Browser paused for user interaction. Waiting {wait_seconds} seconds...")

        try:
            await asyncio.sleep(wait_seconds)
            completion_message = f"✅ Browser pause completed. Resuming agent execution.\n\nCurrent page: {state.client.page.url}"
        except asyncio.CancelledError:
            completion_message = "Browser pause interrupted. Resuming agent execution."

        return completion_message

    async def _get_browser_info(self) -> str:
        """
        Get diagnostic information about the browser configuration.

        Returns current browser state including visibility mode,
        configuration settings, and helpful troubleshooting info.
        """
        state = await self._get_state()

        info = []
        info.append("=== Browser Configuration ===")
        info.append(f"Config headless mode: {self.agent.config.browser_control_headless}")
        info.append(f"Config start URL: {self.agent.config.browser_control_start_url}")
        info.append(f"Config timeout: {self.agent.config.browser_control_timeout}ms")
        info.append("")

        if state and state.client:
            info.append("=== Browser State ===")
            info.append(f"Browser initialized: Yes")
            info.append(f"Browser headless mode: {state.client.headless}")
            if state.client.page:
                info.append(f"Current URL: {state.client.page.url}")
                info.append(f"Page title: {await state.client.page.title()}")
            info.append("")

            # Provide helpful tips
            info.append("=== Visibility Status ===")
            if state.client.headless:
                info.append("⚠️  Browser is running in HEADLESS mode (invisible)")
                info.append("")
                info.append("To see the browser window:")
                info.append("1. Close current browser session with reset=true")
                info.append("2. Set browser_control_headless=False in agent.py")
                info.append("3. Restart the agent")
                info.append("4. Or use: browser_control:navigate with reset='true'")
            else:
                info.append("✓ Browser is running in VISIBLE mode")
                info.append("  A browser window should be visible on your screen")
                info.append("")
                info.append("If you don't see the window:")
                info.append("- Check if it opened on another desktop/display")
                info.append("- Look for Chrome in your taskbar/dock")
                info.append("- Try alt-tabbing (Windows) or Command-Tab (Mac)")
                info.append("- The window may be minimized or behind other windows")
        else:
            info.append("=== Browser State ===")
            info.append("Browser not initialized yet")
            info.append("First use of browser_control will initialize the browser")

        return "\n".join(info)

    async def _capture_screenshot(self, method: str):
        """
        Capture screenshot after action for UI display.
        
        """
        try:
            state = await self._get_state()
            if not state or not state.client or not state.client.page:
                return
            
            # Create screenshot directory
            screenshot_path = files.get_abs_path(
                persist_chat.get_chat_folder_path(self.agent.context.id),
                "browser_control",
                "screenshots",
                f"{self.guid}.png"
            )
            files.make_dirs(screenshot_path)
            
            # Save screenshot to file (viewport only, not full page)
            await state.client.page.screenshot(
                path=screenshot_path,
                full_page=False,
                timeout=self.agent.config.browser_control_timeout
            )
            
            # Update log with img:// protocol for UI display
            screenshot_url = f"img://{screenshot_path}&t={str(time.time())}"
            self.log.update(screenshot=screenshot_url)
            
        except Exception as e:
            # Don't fail the tool execution if screenshot capture fails
            PrintStyle().warning(f"Could not capture screenshot: {e}")
    
    def get_log_object(self):
        """Override logging method to provide custom heading."""
        if self.method:
            heading = f"icon://web {self.agent.agent_name}: Using browser_control:{self.method}"
        else:
            heading = f"icon://web {self.agent.agent_name}: Using browser_control"
        return self.agent.context.log.log(
            type="tool", 
            heading=heading, 
            content="", 
            kvps=self.args
        )

