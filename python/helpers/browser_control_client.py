"""
Browser Control Client - Playwright interface for browser automation.

This module provides the PlaywrightClient for browser automation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import base64


class ActionType(str, Enum):
    """Supported action types for interface automation."""

    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    NAVIGATE = "navigate"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    PRESS = "press"
    HOVER = "hover"
    PAUSE_FOR_USER = "pause_for_user"


@dataclass
class Action:
    """Represents an action to be executed on an interface."""
    
    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ActionResult:
    """Result of executing an action on an interface."""
    
    success: bool
    description: str
    error: Optional[str] = None
    screenshot: Optional[bytes] = None
    task_complete: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InterfaceState:
    """Represents the current state of an interface."""
    
    url: Optional[str] = None
    title: Optional[str] = None
    content: str = ""
    interactive_elements: List[Dict[str, Any]] = None
    screenshot: Optional[bytes] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.interactive_elements is None:
            self.interactive_elements = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BrowserControlState:
    """State management for browser control tool."""
    
    playwright: Optional[Any] = None
    browser: Optional[Any] = None
    context: Optional[Any] = None
    page: Optional[Any] = None
    client: Optional['PlaywrightClient'] = None
    initialized: bool = False
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.initialized and self.client:
            try:
                import asyncio
                # Try to close synchronously
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.client.close())
                    else:
                        asyncio.run(self.client.close())
                except RuntimeError:
                    pass
            except Exception:
                # Silently fail - destructor shouldn't raise
                pass


class PlaywrightClient:
    """
    Web interface automation using Playwright.
    
    Provides browser automation capabilities for web applications.
    """
    
    def __init__(
        self,
        start_url: str = "https://www.google.com",
        headless: bool = True,
        playwright_binary: Optional[str] = None,
        cdp_url: Optional[str] = None,
        use_vnc: bool = False,
        vnc_display: Optional[str] = None
    ):
        """
        Initialize Playwright web client.

        Args:
            start_url: Initial URL to navigate to
            headless: Whether to run browser in headless mode
            playwright_binary: Path to Playwright binary (optional)
            cdp_url: Chrome DevTools Protocol URL to connect to existing browser (optional)
                    e.g., "http://localhost:9222" or "http://host.docker.internal:9222"
            use_vnc: Whether to use VNC display for browser visibility
            vnc_display: VNC display number (e.g., ":99"). If None, read from VNC_DISPLAY env var
        """
        self.start_url = start_url
        self.headless = headless
        self.playwright_binary = playwright_binary
        self.cdp_url = cdp_url
        self.use_vnc = use_vnc
        self.vnc_display = vnc_display
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.action_history = []
    
    async def initialize(self) -> None:
        """Initialize Playwright browser session."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. Install with: pip install playwright"
            )

        # Configure VNC display if enabled
        if self.use_vnc:
            import os
            # Get VNC display from instance variable or environment
            vnc_display = self.vnc_display or os.environ.get('VNC_DISPLAY', ':99')
            # Set DISPLAY environment variable for Playwright to use VNC
            original_display = os.environ.get('DISPLAY')
            os.environ['DISPLAY'] = vnc_display
            print(f"Using VNC display: {vnc_display}")
            # Store original display to restore if needed
            self._original_display = original_display

        self.playwright = await async_playwright().start()

        # Connect via CDP if URL provided (native browser mode)
        if self.cdp_url:
            print(f"Connecting to browser via CDP: {self.cdp_url}")

            # Handle host.docker.internal Host header issue
            # Convert HTTP endpoint to WebSocket to bypass Chrome's Host header validation
            endpoint_url = self.cdp_url
            if endpoint_url.startswith("http://") and "host.docker.internal" in endpoint_url:
                import re
                port_match = re.search(r':(\d+)', endpoint_url)
                if port_match:
                    port = port_match.group(1)
                    # Use WebSocket format - less strict Host header checking
                    endpoint_url = f"ws://host.docker.internal:{port}"
                    print(f"  → Converted to WebSocket: {endpoint_url}")

            self.browser = await self.playwright.chromium.connect_over_cdp(
                endpoint_url=endpoint_url,
                timeout=30000  # 30 seconds
            )
            # Use the default context from the connected browser
            self.context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context(
                viewport={"width": 800, "height": 1600}
            )
            # Use existing page or create new one
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            # Navigate to start URL
            await self.page.goto(self.start_url)
        else:
            # Launch browser with optional binary path (embedded browser mode)
            launch_options = {
                "headless": self.headless,
                "args": ["--headless=new"] if self.headless else []
            }
            if self.playwright_binary:
                launch_options["executable_path"] = self.playwright_binary

            self.browser = await self.playwright.chromium.launch(**launch_options)

            # Create context with viewport size matching browser_agent
            self.context = await self.browser.new_context(
                viewport={"width": 800, "height": 1600}
            )
            self.page = await self.context.new_page()
            await self.page.goto(self.start_url)
    
    async def get_state(self, format: str = "hybrid") -> InterfaceState:
        """Get current state of the web page."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        state = InterfaceState(url=self.page.url, title=await self.page.title())
        
        if format in ["text", "hybrid"]:
            # Get text content
            state.content = await self.page.content()
            
            # Get interactive elements
            elements = await self._get_interactive_elements()
            state.interactive_elements = elements
        
        if format in ["visual", "hybrid"]:
            # Get screenshot
            state.screenshot = await self.get_screenshot()
        
        return state
    
    async def _get_interactive_elements(self) -> List[Dict[str, Any]]:
        """Extract interactive elements from the page."""
        if not self.page:
            return []
        
        try:
            elements = await self.page.evaluate(
                """
                () => {
                    const interactiveSelectors = [
                        'button', 'a', 'input', 'select', 'textarea',
                        '[role="button"]', '[role="link"]', '[onclick]'
                    ];
                    
                    const elements = [];
                    interactiveSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el.offsetParent !== null) {  // Is visible
                                elements.push({
                                    tag: el.tagName.toLowerCase(),
                                    text: el.innerText || el.value || '',
                                    type: el.type || '',
                                    placeholder: el.placeholder || '',
                                    href: el.href || '',
                                    selector: el.id ? `#${el.id}` :
                                             el.className ? `.${el.className.split(' ')[0]}` :
                                             el.tagName.toLowerCase()
                                });
                            }
                        });
                    });
                    return elements;
                }
                """
            )
            return elements
        except Exception:
            return []
    
    async def execute_action(self, action: Action) -> ActionResult:
        """Execute an action on the web page."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        try:
            if action.action_type == ActionType.NAVIGATE:
                if not action.value:
                    raise ValueError("Navigate action requires a URL value")
                
                # Try navigation with robust fallback strategy
                try:
                    # First attempt: wait for networkidle (ideal but may timeout on slow sites)
                    await self.page.goto(
                        action.value, wait_until="networkidle", timeout=5000
                    )
                    result = ActionResult(
                        success=True, description=f"Navigated to {action.value}"
                    )
                except Exception as e:
                    # Fallback: if networkidle times out, check if page loaded at all
                    current_url = self.page.url
                    if current_url and (
                        action.value in current_url or current_url != "about:blank"
                    ):
                        # Page loaded even if not fully idle - consider it a success
                        try:
                            # Wait a bit for DOM to be ready
                            await self.page.wait_for_load_state(
                                "domcontentloaded", timeout=5000
                            )
                        except:
                            pass
                        result = ActionResult(
                            success=True,
                            description=f"Navigated to {action.value} (page loaded but not fully idle)",
                        )
                    else:
                        # Navigation truly failed
                        raise e
            
            elif action.action_type == ActionType.CLICK:
                if not action.selector:
                    raise ValueError("Click action requires a selector")

                # Try different selector strategies with detailed error tracking
                clicked = False
                selector = action.selector
                attempted_selectors = []
                last_error = None

                # Strategy 1: Direct CSS selector (wait for visibility first)
                try:
                    # Wait for element to be visible before clicking
                    await self.page.wait_for_selector(selector, state="visible", timeout=3000)
                    await self.page.click(selector, timeout=2000)
                    clicked = True
                except Exception as e:
                    attempted_selectors.append(f"CSS:{selector}")
                    last_error = str(e)

                    # Strategy 2: If selector contains :contains(), extract and try text-based
                    if ":contains(" in selector and not clicked:
                        import re
                        match = re.search(r":contains\(['\"]?(.*?)['\"]?\)", selector)
                        if match:
                            text = match.group(1)

                            # Try exact text match
                            try:
                                await self.page.wait_for_selector(f"text={text}", state="visible", timeout=2000)
                                await self.page.click(f"text={text}", timeout=2000)
                                clicked = True
                                selector = f"text={text}"
                            except Exception as e2:
                                attempted_selectors.append(f"text={text}")
                                last_error = str(e2)

                                # Try partial text match
                                try:
                                    await self.page.click(f"text=/.*{text}.*/i", timeout=2000)
                                    clicked = True
                                    selector = f"text=/.*{text}.*/i"
                                except Exception as e3:
                                    attempted_selectors.append(f"text=/.*{text}.*/i")
                                    last_error = str(e3)

                                    # Try href match for links
                                    try:
                                        link_selector = f"a[href*='{text.lower()}']"
                                        await self.page.click(link_selector, timeout=2000)
                                        clicked = True
                                        selector = link_selector
                                    except Exception as e4:
                                        attempted_selectors.append(link_selector)
                                        last_error = str(e4)

                    # Strategy 3: If plain text (not CSS), try as text selector
                    if (
                        not clicked
                        and not selector.startswith("#")
                        and not selector.startswith(".")
                        and not selector.startswith("[")
                    ):
                        # Try exact text
                        try:
                            await self.page.click(f"text={selector}", timeout=2000)
                            clicked = True
                            selector = f"text={selector}"
                        except Exception as e5:
                            attempted_selectors.append(f"text={selector}")
                            last_error = str(e5)

                            # Try partial text match (case-insensitive)
                            try:
                                await self.page.click(f"text=/.*{selector}.*/i", timeout=2000)
                                clicked = True
                                selector = f"text=/.*{selector}.*/i"
                            except Exception as e6:
                                attempted_selectors.append(f"text=/.*{selector}.*/i")
                                last_error = str(e6)

                    # Strategy 4: Force click if element is covered (e.g., by ads)
                    if not clicked:
                        try:
                            original_selector = action.selector
                            # Try to locate the element and force click
                            await self.page.click(original_selector, force=True, timeout=2000)
                            clicked = True
                            selector = f"{original_selector} (forced)"
                        except Exception as e7:
                            attempted_selectors.append(f"force:{original_selector}")
                            last_error = str(e7)

                    if not clicked:
                        # Provide helpful error message with all attempted strategies
                        error_msg = f"Failed to click element. Attempted selectors: {', '.join(attempted_selectors)}. Last error: {last_error}"
                        raise Exception(error_msg)

                result = ActionResult(
                    success=True, description=f"Clicked on {selector}"
                )
            
            elif action.action_type == ActionType.TYPE:
                if not action.selector or not action.value:
                    raise ValueError("Type action requires both selector and value")
                # Wait for input to be visible before typing
                await self.page.wait_for_selector(action.selector, state="visible", timeout=3000)
                await self.page.fill(action.selector, action.value)
                result = ActionResult(
                    success=True,
                    description=f"Typed '{action.value}' into {action.selector}",
                )
            
            elif action.action_type == ActionType.SELECT:
                if not action.selector or not action.value:
                    raise ValueError("Select action requires both selector and value")
                # Wait for select element to be visible
                await self.page.wait_for_selector(action.selector, state="visible", timeout=3000)
                await self.page.select_option(action.selector, action.value)
                result = ActionResult(
                    success=True,
                    description=f"Selected '{action.value}' in {action.selector}",
                )

            elif action.action_type == ActionType.PRESS:
                if not action.selector or not action.value:
                    raise ValueError("Press action requires both selector and value")
                # Wait for element to be visible before pressing key
                await self.page.wait_for_selector(action.selector, state="visible", timeout=3000)
                await self.page.press(action.selector, action.value)
                result = ActionResult(
                    success=True,
                    description=f"Pressed '{action.value}' on {action.selector}",
                )
            
            elif action.action_type == ActionType.SCROLL:
                # Map direction to scroll values
                direction = action.value or "down"
                scroll_x, scroll_y = 0, 0
                
                if direction == "down":
                    scroll_y = 500
                elif direction == "up":
                    scroll_y = -500
                elif direction == "right":
                    scroll_x = 500
                elif direction == "left":
                    scroll_x = -500
                else:
                    # If it's a number, use it directly for vertical scrolling
                    try:
                        scroll_y = int(direction)
                    except ValueError:
                        scroll_y = 500  # Default to scrolling down
                
                await self.page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")
                result = ActionResult(
                    success=True,
                    description=f"Scrolled {direction} by {abs(scroll_y or scroll_x)} pixels",
                )
            
            elif action.action_type == ActionType.HOVER:
                if not action.selector:
                    raise ValueError("Hover action requires a selector")
                # Wait for element to be visible before hovering
                await self.page.wait_for_selector(action.selector, state="visible", timeout=3000)
                await self.page.hover(action.selector)
                result = ActionResult(
                    success=True, description=f"Hovered over {action.selector}"
                )

            elif action.action_type == ActionType.PAUSE_FOR_USER:
                # Pause execution and wait for user interaction
                # This is useful for CAPTCHAs, manual login, or other user interventions
                wait_time = int(action.value) if action.value else 60
                message = action.metadata.get("message", "Pausing for user interaction...")

                # Check if VNC is available for user interaction
                vnc_url = self.get_vnc_url(host="localhost", port=56080)

                if not vnc_url and self.headless:
                    # No VNC and headless - user has no way to interact
                    result = ActionResult(
                        success=False,
                        description="",
                        error="Cannot pause for user: browser is in headless mode and VNC is not available. Set headless=False or enable VNC when initializing the browser."
                    )
                else:
                    # VNC is available or browser is visible - user can interact
                    # Return immediately without blocking - let the agent handle the pause
                    print(f"\n{'='*60}")
                    print(f"BROWSER READY FOR USER INTERACTION: {message}")
                    print(f"Current URL: {self.page.url}")
                    if vnc_url:
                        print(f"VNC URL: {vnc_url}")
                        print(f"Browser control panel will open automatically in web UI")
                    else:
                        print(f"Browser window should be visible on your display")
                    print(f"Agent will wait up to {wait_time} seconds")
                    print(f"{'='*60}\n")

                    result = ActionResult(
                        success=True,
                        description=f"Browser ready for user interaction. Agent will pause for up to {wait_time} seconds. Current page: {self.page.url}"
                    )

            else:
                result = ActionResult(
                    success=False,
                    description="",
                    error=f"Unsupported action type: {action.action_type}",
                )
            
            # Record action in history
            self.action_history.append(action)
            
            # Add screenshot if requested
            if action.metadata.get("capture_screenshot", False):
                result.screenshot = await self.get_screenshot()
            
            return result
        
        except Exception as e:
            return ActionResult(success=False, description="", error=str(e))
    
    async def get_screenshot(self) -> bytes:
        """Get screenshot of current page as PNG bytes."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        return await self.page.screenshot(type="png", full_page=False)
    
    async def get_screenshot_base64(self) -> str:
        """Get screenshot of current page as base64 string for LLM context."""
        screenshot_bytes = await self.get_screenshot()
        return base64.b64encode(screenshot_bytes).decode('utf-8')

    def get_vnc_url(self, host: str = "localhost", port: int = 6080) -> Optional[str]:
        """
        Get the noVNC URL for manual browser control.

        Args:
            host: Host where noVNC is accessible (default: localhost)
            port: Port where noVNC is accessible (default: 6080)

        Returns:
            noVNC URL if VNC is enabled, None otherwise
        """
        if not self.use_vnc:
            return None

        import os
        # Check if VNC is ready
        vnc_status_file = '/tmp/vnc/status'
        if not os.path.exists(vnc_status_file):
            return None

        try:
            with open(vnc_status_file, 'r') as f:
                status_lines = f.readlines()
                status_dict = {}
                for line in status_lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        status_dict[key] = value

                vnc_ready = status_dict.get('READY', 'false') == 'true'
                if not vnc_ready:
                    return None

                novnc_port = status_dict.get('NOVNC_PORT', str(port))
                return f"http://{host}:{novnc_port}/vnc.html?autoconnect=true&resize=none"
        except Exception:
            return None

    async def close(self) -> None:
        """Close browser and clean up."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

