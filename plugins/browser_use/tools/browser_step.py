"""Step-by-step browser control tool.

Each call performs exactly one action and returns the result.
Uses the shared SessionManager so the user can watch in the viewer.
"""

import time
from python.helpers.tool import Tool, Response
from python.helpers import files, persist_chat
from plugins.browser_use.helpers.session_manager import SessionManager


class BrowserStep(Tool):

    async def execute(self, action="", target="", value="", **kwargs) -> Response:
        action = action.strip().lower()
        if not action:
            return Response(
                message="Error: 'action' argument is required. Use action='state' to see available elements.",
                break_loop=False,
            )

        manager = SessionManager.get_or_create(self.agent)
        await manager.ensure_started()

        async with manager.lock:
            handler = getattr(self, f"_action_{action}", None)
            if not handler:
                return Response(
                    message=f"Error: Unknown action '{action}'. Valid actions: open, state, click, type, input, screenshot, scroll, back, keys, select, extract, eval, close",
                    break_loop=False,
                )
            return await handler(manager, target, value)

    # -- Actions ---------------------------------------------------------------

    async def _action_open(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        url = target.strip()
        if not url:
            return Response(message="Error: 'target' (URL) is required for open action.", break_loop=False)

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            page = await manager.browser_session.navigate(url)
            title = await page.title()
            return Response(message=f"Navigated to: {page.url}\nTitle: {title}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error navigating to {url}: {e}", break_loop=False)

    async def _action_state(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        try:
            state = await manager.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True,
                include_screenshot=False,
            )

            url = state.url
            title = state.title

            # Use browser-use's built-in element tree formatter
            elements_text = state.element_tree.clickable_elements_to_string()

            lines = [f"URL: {url}", f"Title: {title}", "", "Clickable elements:", elements_text]
            return Response(message="\n".join(lines), break_loop=False)
        except Exception as e:
            return Response(message=f"Error getting state: {e}", break_loop=False)

    async def _action_click(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        try:
            index = int(target)
        except (ValueError, TypeError):
            return Response(
                message=f"Error: 'target' must be an element index (number). Got: '{target}'",
                break_loop=False,
            )

        try:
            # Refresh state to ensure selector map is current
            await manager.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True,
                include_screenshot=False,
            )
            selector_map = await manager.browser_session.get_selector_map()
            if index not in selector_map:
                available = list(selector_map.keys())[:20]
                return Response(
                    message=f"Error: Element index {index} not found. Available indices: {available}. Use action='state' to see all elements.",
                    break_loop=False,
                )

            # get_element_by_index returns a Playwright ElementHandle
            element_handle = await manager.browser_session.get_element_by_index(index)
            if not element_handle:
                return Response(
                    message=f"Error: Could not locate element [{index}] on page. It may have changed. Use action='state' to refresh.",
                    break_loop=False,
                )

            await element_handle.click(timeout=5000)

            page = await manager.get_page()
            current_url = page.url if page else "unknown"
            return Response(message=f"Clicked element [{index}]. Page: {current_url}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error clicking element [{index}]: {e}", break_loop=False)

    async def _action_type(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        text = value or target  # Allow text in either arg
        if not text:
            return Response(message="Error: 'value' (text to type) is required.", break_loop=False)

        await page.keyboard.type(text)
        return Response(message=f"Typed: {text}", break_loop=False)

    async def _action_input(self, manager: SessionManager, target: str, value: str) -> Response:
        """Click an element then type text into it."""
        click_result = await self._action_click(manager, target, "")
        if "Error" in click_result.message:
            return click_result

        if not value:
            return Response(
                message="Error: 'value' (text to type) is required for input action.",
                break_loop=False,
            )

        page = await manager.get_page()
        if page:
            # Select all existing text and replace
            await page.keyboard.press("Control+a")
            await page.keyboard.type(value)
        return Response(message=f"Input into element [{target}]: {value}", break_loop=False)

    async def _action_screenshot(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        path = files.get_abs_path(
            persist_chat.get_chat_folder_path(self.agent.context.id),
            "browser",
            "screenshots",
            f"step_{int(time.time())}.png",
        )
        files.make_dirs(path)
        await page.screenshot(path=path, full_page=False)
        screenshot_ref = f"img://{path}&t={time.time()}"
        self.log.update(screenshot=screenshot_ref)
        return Response(message=f"Screenshot saved: {path}", break_loop=False)

    async def _action_scroll(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        direction = target.strip().lower() or "down"
        try:
            amount = int(value) if value else 500
        except ValueError:
            amount = 500

        delta = amount if direction == "down" else -amount
        await page.mouse.wheel(0, delta)
        return Response(message=f"Scrolled {direction} by {amount}px", break_loop=False)

    async def _action_back(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        try:
            await manager.browser_session.go_back()
            page = await manager.get_page()
            current_url = page.url if page else "unknown"
            return Response(message=f"Went back. Now at: {current_url}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error going back: {e}", break_loop=False)

    async def _action_keys(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        keys = target.strip()
        if not keys:
            return Response(
                message="Error: 'target' (key combo) is required. E.g. 'Enter', 'Control+a'",
                break_loop=False,
            )

        # Support space-separated key sequences like "Tab Tab Enter"
        for key in keys.split():
            await page.keyboard.press(key)
        return Response(message=f"Sent keys: {keys}", break_loop=False)

    async def _action_select(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        try:
            index = int(target)
        except (ValueError, TypeError):
            return Response(
                message=f"Error: 'target' must be an element index. Got: '{target}'",
                break_loop=False,
            )

        if not value:
            return Response(message="Error: 'value' (option to select) is required.", break_loop=False)

        try:
            # Refresh state to ensure selector map is current
            await manager.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True,
                include_screenshot=False,
            )
            selector_map = await manager.browser_session.get_selector_map()
            if index not in selector_map:
                return Response(
                    message=f"Error: Element [{index}] not found. Use action='state' to see available elements.",
                    break_loop=False,
                )

            # get_element_by_index returns a Playwright ElementHandle
            element_handle = await manager.browser_session.get_element_by_index(index)
            if not element_handle:
                return Response(
                    message=f"Error: Could not locate element [{index}] on page.",
                    break_loop=False,
                )

            await element_handle.select_option(value)
            return Response(message=f"Selected '{value}' in element [{index}]", break_loop=False)
        except Exception as e:
            return Response(message=f"Error selecting option: {e}", break_loop=False)

    async def _action_extract(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        try:
            text = await page.inner_text("body")
            if not text.strip():
                text = "(Page has no visible text content)"

            # If a query/filter was provided, include it in the output header
            query = target.strip() if target else None
            header = f"Page text (query: {query}):" if query else "Page text:"

            # Truncate very long text to avoid overwhelming the agent
            max_chars = 5000
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... (truncated, {len(text)} total chars)"

            return Response(message=f"{header}\n{text}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error extracting text: {e}", break_loop=False)

    async def _action_eval(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        expression = target.strip()
        if not expression:
            return Response(message="Error: 'target' (JS expression) is required.", break_loop=False)

        try:
            result = await page.evaluate(expression)
            return Response(message=f"Result: {result}", break_loop=False)
        except Exception as e:
            return Response(message=f"JS evaluation error: {e}", break_loop=False)

    async def _action_close(self, manager: SessionManager, target: str, value: str) -> Response:
        await manager.close()
        return Response(message="Browser session closed.", break_loop=False)

    # -- Logging ---------------------------------------------------------------

    def get_log_object(self):
        action = self.args.get("action", "unknown") if self.args else "unknown"
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Browser Step ({action})",
            content="",
            kvps=self.args,
            _tool_name="browser_step",
        )
