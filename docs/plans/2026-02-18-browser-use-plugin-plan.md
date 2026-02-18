# Browser-Use Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a browser-use plugin that gives the agent step-by-step and autonomous browser control with a real-time CDP screencast viewer in the WebUI sidebar.

**Architecture:** Plugin follows PR #998 conventions (`plugins/browser_use/`). A shared `SessionManager` manages one Chromium browser per agent context. Two tools (`browser_step`, `browser_auto`) interact through the session. A CDP WebSocket proxy streams screencast frames to a canvas-based viewer modal. The sidebar gets a globe icon button via `x-extension`.

**Tech Stack:** Python (browser-use library, Playwright, asyncio), Flask API handlers, Socket.IO WebSocket, Alpine.js stores, HTML5 Canvas, Chrome DevTools Protocol (CDP)

**Reference files:**
- Design doc: `docs/plans/2026-02-18-browser-use-plugin-design.md`
- Tool base class: `python/helpers/tool.py`
- API handler base: `python/helpers/api.py`
- Extension base: `python/helpers/extension.py`
- WebSocket handler base: `python/helpers/websocket.py`
- Existing browser tool: `python/tools/browser_agent.py`
- Browser-use wrapper: `python/helpers/browser_use.py`
- Plugin conventions: `build_docs/A0-PLUGINS.md`
- Sidebar quick-actions: `webui/components/sidebar/top-section/quick-actions.html`
- Modal system: `webui/js/modals.js`
- Alpine store factory: `webui/js/AlpineStore.js`

---

## Task 1: Create Plugin Directory Scaffold

**Files:**
- Create: `plugins/browser_use/` (directory tree)

**Step 1: Create all plugin directories**

```bash
mkdir -p plugins/browser_use/{api,tools,helpers,extensions/python/agent_init,extensions/webui/sidebar-quick-actions-main-start,webui,prompts}
```

**Step 2: Verify structure matches design**

```bash
find plugins/browser_use -type d | sort
```

Expected:
```
plugins/browser_use
plugins/browser_use/api
plugins/browser_use/extensions
plugins/browser_use/extensions/python
plugins/browser_use/extensions/python/agent_init
plugins/browser_use/extensions/webui
plugins/browser_use/extensions/webui/sidebar-quick-actions-main-start
plugins/browser_use/helpers
plugins/browser_use/prompts
plugins/browser_use/tools
plugins/browser_use/webui
```

**Step 3: Commit**

```bash
git add plugins/browser_use/
git commit -m "scaffold: browser_use plugin directory structure"
```

---

## Task 2: Session Manager

The session manager is the foundation — both tools and the viewer depend on it.

**Files:**
- Create: `plugins/browser_use/helpers/session_manager.py`

**Step 1: Write session manager**

This module manages one browser session per agent context. Key responsibilities:
- Launch Chromium with `--remote-debugging-port=0` and extract the CDP WebSocket URL
- Provide an `asyncio.Lock` so tools and user interactions don't collide
- Store the session in `agent.get_data()` / `agent.set_data()` so it persists across tool calls
- Clean up on close

```python
"""Shared browser session lifecycle manager.

One SessionManager per agent context. Stores itself in agent.get_data('_browser_use_session').
Both tools (browser_step, browser_auto) and the WebUI viewer share this session.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from python.helpers.browser_use import browser_use
from python.helpers import files
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary

if TYPE_CHECKING:
    from agent import Agent

_STORAGE_KEY = "_browser_use_session"


class SessionManager:
    """Manages a single shared browser session for an agent context."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.cdp_ws_url: Optional[str] = None
        self.lock = asyncio.Lock()
        self._closed = False

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

    @property
    def is_alive(self) -> bool:
        return self.browser_session is not None and not self._closed

    @property
    def is_busy(self) -> bool:
        return self.lock.locked()

    async def ensure_started(self) -> None:
        """Start the browser if not already running."""
        if self.browser_session and not self._closed:
            return
        await self._start_browser()

    async def _start_browser(self) -> None:
        """Launch Chromium with CDP enabled and extract the WS URL."""
        pw_binary = ensure_playwright_binary()

        user_data_dir = str(
            Path.home() / ".config" / "browseruse" / "profiles"
            / f"plugin_{self.agent.context.id}"
        )

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=False,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_path=files.get_abs_path("usr/downloads"),
                executable_path=pw_binary,
                keep_alive=True,
                minimum_wait_page_load_time=1.0,
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=10.0,
                window_size={"width": 1024, "height": 768},
                screen={"width": 1024, "height": 768},
                viewport={"width": 1024, "height": 768},
                no_viewport=False,
                user_data_dir=user_data_dir,
                args=[
                    "--remote-debugging-port=0",
                ],
            )
        )

        await self.browser_session.start()

        # Extract CDP WebSocket URL from the browser process
        self.cdp_ws_url = await self._extract_cdp_url()
        self._closed = False

        PrintStyle().print(f"Browser session started. CDP: {self.cdp_ws_url}")

    async def _extract_cdp_url(self) -> Optional[str]:
        """Extract the CDP WebSocket URL from the running browser.

        browser-use / Playwright exposes the CDP endpoint via the browser object.
        We access it through the Playwright browser's internal CDP connection.
        """
        if not self.browser_session:
            return None

        try:
            # Playwright exposes the browser's CDP WebSocket endpoint
            browser = self.browser_session.browser
            if browser and hasattr(browser, '_impl_obj'):
                # The Playwright browser object has a ws_endpoint for CDP
                ws_endpoint = browser._impl_obj._connection._transport._ws_endpoint
                return ws_endpoint
        except Exception as e:
            PrintStyle().warning(f"Could not extract CDP URL via Playwright internals: {e}")

        # Fallback: try to get it from browser context CDP session
        try:
            if self.browser_session.browser_context:
                cdp = await self.browser_session.browser_context.new_cdp_session(
                    await self.browser_session.get_current_page()
                )
                # We have a CDP session — store it for direct use
                self._cdp_session = cdp
                return "direct"  # Signal that we use direct CDP session, not WS URL
        except Exception as e:
            PrintStyle().warning(f"Could not create CDP session: {e}")

        return None

    async def get_page(self):
        """Get the current Playwright page object."""
        if self.browser_session:
            try:
                return await self.browser_session.get_current_page()
            except Exception:
                return None
        return None

    async def get_state(self) -> dict:
        """Get current browser state (URL, title, elements)."""
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
                self.cdp_ws_url = None

        # Clean up user data dir
        user_data_dir = str(
            Path.home() / ".config" / "browseruse" / "profiles"
            / f"plugin_{self.agent.context.id}"
        )
        files.delete_dir(user_data_dir)

        # Remove from agent data
        self.agent.set_data(_STORAGE_KEY, None)

    def __del__(self):
        if self.browser_session and not self._closed:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.close())
                loop.close()
            except Exception:
                pass
```

**Step 2: Commit**

```bash
git add plugins/browser_use/helpers/session_manager.py
git commit -m "feat(browser_use): add session manager for shared browser lifecycle"
```

---

## Task 3: Browser Step Tool

The deterministic step-by-step tool. Each call does exactly one action.

**Files:**
- Create: `plugins/browser_use/tools/browser_step.py`
- Create: `plugins/browser_use/prompts/agent.system.tool.browser_step.md`

**Step 1: Write the tool prompt**

The prompt tells the agent how to use this tool. It's loaded automatically because `get_paths` with `include_plugins=True` searches plugin prompt dirs.

```markdown
## browser_step
Precise, step-by-step browser control. Each call performs one action and returns the result.

**Usage:** Always call with action="state" first to see available elements and their indices.

**Actions:**
- `open` — Navigate to URL. Args: target=URL
- `state` — Get clickable elements with indices. No args needed.
- `click` — Click element. Args: target=element_index
- `type` — Type text into focused element. Args: value=text
- `input` — Click element then type. Args: target=element_index, value=text
- `screenshot` — Take screenshot. No args needed.
- `scroll` — Scroll page. Args: target=up|down, value=pixel_amount (default 500)
- `back` — Go back in history. No args needed.
- `keys` — Send keyboard keys. Args: target=key_combo (e.g. "Enter", "Control+a")
- `select` — Select dropdown option. Args: target=element_index, value=option_value
- `extract` — Extract data using LLM. Args: target=query_string
- `eval` — Execute JavaScript. Args: target=js_expression
- `close` — Close browser session. No args needed.

**Example workflow:**
~~~json
{"tool_name": "browser_step", "tool_args": {"action": "open", "target": "https://example.com"}}
{"tool_name": "browser_step", "tool_args": {"action": "state"}}
{"tool_name": "browser_step", "tool_args": {"action": "click", "target": "5"}}
{"tool_name": "browser_step", "tool_args": {"action": "input", "target": "3", "value": "search query"}}
{"tool_name": "browser_step", "tool_args": {"action": "screenshot"}}
~~~
```

**Step 2: Write the tool implementation**

```python
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

    async def _action_open(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        url = target.strip()
        if not url:
            return Response(message="Error: 'target' (URL) is required for open action.", break_loop=False)

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        title = await page.title()
        return Response(message=f"Navigated to: {page.url}\nTitle: {title}", break_loop=False)

    async def _action_state(self, manager: SessionManager, target: str, value: str) -> Response:
        if not manager.browser_session:
            return Response(message="Error: No browser session.", break_loop=False)

        try:
            state = await manager.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True
            )
            selector_map = await manager.browser_session.get_selector_map()

            page = await manager.get_page()
            url = page.url if page else "unknown"
            title = await page.title() if page else "unknown"

            lines = [f"URL: {url}", f"Title: {title}", "", "Clickable elements:"]
            for idx, selector in selector_map.items():
                lines.append(f"  [{idx}] {selector}")

            return Response(message="\n".join(lines), break_loop=False)
        except Exception as e:
            return Response(message=f"Error getting state: {e}", break_loop=False)

    async def _action_click(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        try:
            index = int(target)
        except (ValueError, TypeError):
            return Response(message=f"Error: 'target' must be an element index (number). Got: '{target}'", break_loop=False)

        try:
            selector_map = await manager.browser_session.get_selector_map()
            if index not in selector_map:
                return Response(message=f"Error: Element index {index} not found. Use action='state' to see available elements.", break_loop=False)

            element = selector_map[index]
            await element.click(timeout=5000)
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            return Response(message=f"Clicked element [{index}]. Page: {page.url}", break_loop=False)
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
            return Response(message="Error: 'value' (text to type) is required for input action.", break_loop=False)

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
            "browser", "screenshots", f"step_{int(time.time())}.png",
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
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        await page.go_back(wait_until="domcontentloaded", timeout=10000)
        return Response(message=f"Went back. Now at: {page.url}", break_loop=False)

    async def _action_keys(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        keys = target.strip()
        if not keys:
            return Response(message="Error: 'target' (key combo) is required. E.g. 'Enter', 'Control+a'", break_loop=False)

        # Support space-separated key sequences like "Tab Tab Enter"
        for key in keys.split():
            await page.keyboard.press(key)
        return Response(message=f"Sent keys: {keys}", break_loop=False)

    async def _action_select(self, manager: SessionManager, target: str, value: str) -> Response:
        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        try:
            index = int(target)
        except (ValueError, TypeError):
            return Response(message=f"Error: 'target' must be an element index. Got: '{target}'", break_loop=False)

        if not value:
            return Response(message="Error: 'value' (option to select) is required.", break_loop=False)

        try:
            selector_map = await manager.browser_session.get_selector_map()
            if index not in selector_map:
                return Response(message=f"Error: Element [{index}] not found.", break_loop=False)
            element = selector_map[index]
            await element.select_option(value)
            return Response(message=f"Selected '{value}' in element [{index}]", break_loop=False)
        except Exception as e:
            return Response(message=f"Error selecting option: {e}", break_loop=False)

    async def _action_extract(self, manager: SessionManager, target: str, value: str) -> Response:
        query = target.strip()
        if not query:
            return Response(message="Error: 'target' (query string) is required for extract.", break_loop=False)

        page = await manager.get_page()
        if not page:
            return Response(message="Error: No browser page available.", break_loop=False)

        try:
            content = await page.content()
            # Use the agent's LLM to extract data from page content
            from python.helpers.browser_use import browser_use
            result = await browser_use.extract_page_content(page, query)
            return Response(message=f"Extracted: {result}", break_loop=False)
        except Exception as e:
            # Fallback: return raw text content
            text = await page.inner_text("body")
            truncated = text[:2000] + "..." if len(text) > 2000 else text
            return Response(message=f"Page text (extraction failed: {e}):\n{truncated}", break_loop=False)

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

    def get_log_object(self):
        action = self.args.get("action", "unknown") if self.args else "unknown"
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Browser Step ({action})",
            content="",
            kvps=self.args,
            _tool_name="browser_step",
        )
```

**Step 3: Commit**

```bash
git add plugins/browser_use/tools/browser_step.py plugins/browser_use/prompts/agent.system.tool.browser_step.md
git commit -m "feat(browser_use): add browser_step tool with 12 deterministic actions"
```

---

## Task 4: Browser Auto Tool

The enhanced autonomous browser agent tool.

**Files:**
- Create: `plugins/browser_use/tools/browser_auto.py`

**Step 1: Write the autonomous tool**

This wraps browser-use's `Agent` class with the shared session and configurable parameters. Pattern follows existing `python/tools/browser_agent.py` but uses `SessionManager`.

```python
"""Enhanced autonomous browser-use Agent tool.

Wraps browser-use's Agent class with configurable parameters and shared
SessionManager for viewer integration. Lock-aware: acquires session lock
for the entire autonomous run.
"""

import asyncio
import time
from typing import Optional, cast

from agent import Agent, InterventionException
from pydantic import BaseModel
from python.helpers.tool import Tool, Response
from python.helpers import files, persist_chat, defer, strings
from python.helpers.browser_use import browser_use
from python.helpers.print_style import PrintStyle
from python.helpers.secrets import get_secrets_manager
from python.helpers.dirty_json import DirtyJson
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from plugins.browser_use.helpers.session_manager import SessionManager


class BrowserAuto(Tool):

    async def execute(self, task="", max_steps="25", vision="auto",
                      flash_mode="false", reset="false", **kwargs) -> Response:
        if not task:
            return Response(message="Error: 'task' argument is required.", break_loop=False)

        # Parse args
        try:
            max_steps_int = int(max_steps)
        except (ValueError, TypeError):
            max_steps_int = 25

        vision_mode = vision.strip().lower() if isinstance(vision, str) else "auto"
        use_vision = True if vision_mode == "true" else (False if vision_mode == "false" else "auto")
        use_flash = str(flash_mode).strip().lower() == "true"
        do_reset = str(reset).strip().lower() == "true"

        self.guid = self.agent.context.generate_id()

        # Get or create session
        manager = SessionManager.get_or_create(self.agent)
        if do_reset:
            await manager.close()
            manager = SessionManager.get_or_create(self.agent)
        await manager.ensure_started()

        # Mask secrets in task
        secrets_mgr = get_secrets_manager(self.agent.context)
        task = secrets_mgr.mask_values(task, placeholder="<secret>{key}</secret>")

        # Run the autonomous agent under the session lock
        async with manager.lock:
            result = await self._run_autonomous(manager, task, max_steps_int, use_vision, use_flash)

        return result

    async def _run_autonomous(self, manager: SessionManager, task: str,
                              max_steps: int, use_vision, flash_mode: bool) -> Response:
        """Run browser-use Agent autonomously."""

        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        controller = browser_use.Controller(output_model=DoneResult)

        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            return browser_use.ActionResult(
                is_done=True, success=True,
                extracted_content=params.model_dump_json()
            )

        model = self.agent.get_browser_model()
        secrets_mgr = get_secrets_manager(self.agent.context)
        secrets_dict = secrets_mgr.load_secrets()

        try:
            use_agent = browser_use.Agent(
                task=task,
                browser_session=manager.browser_session,
                llm=model,
                use_vision=use_vision,
                flash_mode=flash_mode,
                extend_system_message=self.agent.read_prompt(
                    "prompts/browser_agent.system.md"
                ),
                controller=controller,
                enable_memory=False,
                llm_timeout=3000,
                sensitive_data=cast(dict[str, str | dict[str, str]] | None, secrets_dict or {}),
            )
        except Exception as e:
            return Response(
                message=f"Browser agent init failed: {e}",
                break_loop=False,
            )

        iter_no = get_iter_no(self.agent)

        async def step_hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")
            # Update progress with latest step info
            log_lines = self._get_log(agent)
            self._update_progress("\n".join(log_lines))
            # Update screenshot
            await self._update_screenshot(manager)

        # Run with timeout
        timeout_seconds = max_steps * 12  # ~12 seconds per step max
        try:
            result = await asyncio.wait_for(
                use_agent.run(
                    max_steps=max_steps,
                    on_step_start=step_hook,
                    on_step_end=step_hook,
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            return Response(
                message=f"Browser agent timed out after {timeout_seconds}s",
                break_loop=False,
            )
        except InterventionException:
            return Response(message="Browser agent task cancelled.", break_loop=False)
        except Exception as e:
            return Response(message=f"Browser agent error: {e}", break_loop=False)

        # Process result
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)
                else:
                    answer_text = str(answer) if answer else "Task completed."
            except Exception:
                answer_text = str(answer) if answer else "Task completed."
        else:
            urls = result.urls() if result else []
            current_url = urls[-1] if urls else "unknown"
            answer_text = f"Reached step limit ({max_steps}). Last page: {current_url}"

        # Mask secrets in output
        answer_text = get_secrets_manager(self.agent.context).mask_values(answer_text)

        self.log.update(answer=answer_text)

        # Add screenshot reference if available
        if self.log.kvps and "screenshot" in self.log.kvps:
            path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        return Response(message=answer_text, break_loop=False)

    async def _update_screenshot(self, manager: SessionManager):
        """Take a screenshot and update the log."""
        page = await manager.get_page()
        if not page:
            return
        try:
            path = files.get_abs_path(
                persist_chat.get_chat_folder_path(self.agent.context.id),
                "browser", "screenshots", f"{self.guid}.png",
            )
            files.make_dirs(path)
            await page.screenshot(path=path, full_page=False, timeout=3000)
            self.log.update(screenshot=f"img://{path}&t={time.time()}")
        except Exception:
            pass

    def _update_progress(self, text: str):
        text = get_secrets_manager(self.agent.context).mask_values(text)
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        self.log.update(progress=text)
        self.agent.context.log.set_progress(f"Browser: {short}")

    def _get_log(self, use_agent) -> list[str]:
        result = []
        if use_agent:
            for item in (use_agent.history.action_results() or []):
                if item.is_done:
                    result.append("Done" if item.success else f"Error: {item.error}")
                elif item.extracted_content:
                    result.append(item.extracted_content.split("\n", 1)[0][:200])
        return result or ["Working..."]

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Browser Auto",
            content="",
            kvps=self.args,
            _tool_name="browser_auto",
        )
```

**Step 2: Commit**

```bash
git add plugins/browser_use/tools/browser_auto.py
git commit -m "feat(browser_use): add browser_auto autonomous agent tool"
```

---

## Task 5: API Handlers

Backend endpoints for session lifecycle, browser state, and settings.

**Files:**
- Create: `plugins/browser_use/api/browser_use_connect.py`
- Create: `plugins/browser_use/api/browser_use_interact.py`
- Create: `plugins/browser_use/api/browser_use_settings.py`

**Step 1: Write the connect handler (session lifecycle)**

```python
"""Session lifecycle API: start, stop, status."""

from python.helpers.api import ApiHandler
from flask import Request
from agent import AgentContext


class BrowserUseConnect(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "status")
        context_id = input.get("context_id", "")

        context = self.use_context(context_id) if context_id else AgentContext.first()
        if not context:
            return {"error": "No agent context found", "status": "error"}

        agent = context.agent0

        from plugins.browser_use.helpers.session_manager import SessionManager

        if action == "start":
            manager = SessionManager.get_or_create(agent)
            await manager.ensure_started()
            return {
                "status": "connected",
                "cdp_ws_url": manager.cdp_ws_url,
                "context_id": context.id,
            }

        elif action == "stop":
            manager = SessionManager.get_existing(agent)
            if manager:
                await manager.close()
            return {"status": "closed"}

        elif action == "status":
            manager = SessionManager.get_existing(agent)
            if not manager:
                return {"alive": False, "url": "", "title": "", "busy": False}
            state = await manager.get_state()
            return state

        return {"error": f"Unknown action: {action}"}
```

**Step 2: Write the interact handler (HTTP fallback)**

```python
"""HTTP interaction fallback for browser control."""

import time
from python.helpers.api import ApiHandler
from python.helpers import files, persist_chat
from flask import Request
from agent import AgentContext


class BrowserUseInteract(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "")
        context_id = input.get("context_id", "")

        context = self.use_context(context_id) if context_id else AgentContext.first()
        if not context:
            return {"error": "No agent context found"}

        agent = context.agent0

        from plugins.browser_use.helpers.session_manager import SessionManager

        manager = SessionManager.get_existing(agent)
        if not manager or not manager.is_alive:
            return {"error": "No active browser session. Start one first."}

        if action == "navigate":
            url = input.get("url", "")
            if not url:
                return {"error": "'url' is required"}
            async with manager.lock:
                page = await manager.get_page()
                if page:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    return {"url": page.url, "title": await page.title()}
            return {"error": "No page available"}

        elif action == "screenshot":
            page = await manager.get_page()
            if not page:
                return {"error": "No page available"}
            path = files.get_abs_path(
                persist_chat.get_chat_folder_path(context.id),
                "browser", "screenshots", f"interact_{int(time.time())}.png",
            )
            files.make_dirs(path)
            await page.screenshot(path=path, full_page=False)
            return {"path": f"img://{path}&t={time.time()}"}

        elif action == "state":
            state = await manager.get_state()
            return state

        return {"error": f"Unknown action: {action}"}
```

**Step 3: Write the settings handler**

```python
"""Plugin settings CRUD."""

import json
from python.helpers.api import ApiHandler
from python.helpers import files
from flask import Request

SETTINGS_PATH = "usr/plugins/browser_use/settings.json"

DEFAULT_SETTINGS = {
    "browser_mode": "chromium",
    "headless": False,
    "default_max_steps": 25,
    "vision_mode": "auto",
    "flash_mode": False,
    "screencast_quality": 80,
    "window_size": "1024x768",
    "browser_use_api_key": "",
}


class BrowserUseSettings(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict:
        if request.method == "GET":
            return {"settings": self._load_settings()}

        # POST: save settings
        new_settings = input.get("settings", {})
        current = self._load_settings()
        current.update(new_settings)

        settings_path = files.get_abs_path(SETTINGS_PATH)
        files.make_dirs(settings_path)
        with open(settings_path, "w") as f:
            json.dump(current, f, indent=2)

        return {"ok": True}

    def _load_settings(self) -> dict:
        settings_path = files.get_abs_path(SETTINGS_PATH)
        if files.exists(settings_path):
            try:
                with open(settings_path) as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)
```

**Step 4: Commit**

```bash
git add plugins/browser_use/api/
git commit -m "feat(browser_use): add API handlers for connect, interact, and settings"
```

---

## Task 6: CDP Proxy (WebSocket Handler)

WebSocket handler for streaming CDP screencast frames with method whitelisting.

**Files:**
- Create: `plugins/browser_use/helpers/cdp_proxy.py`

**Step 1: Write the CDP proxy**

This uses the Socket.IO `WebSocketHandler` pattern from the codebase. It relays CDP messages between the viewer and the browser with a security whitelist.

```python
"""CDP WebSocket proxy with method whitelisting.

Relays screencast frames from browser to viewer and input events from
viewer to browser. Only whitelisted CDP methods are allowed.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from python.helpers.print_style import PrintStyle

# CDP methods allowed through the proxy
ALLOWED_METHODS = frozenset({
    # Screencast (viewer receives frames)
    "Page.startScreencast",
    "Page.stopScreencast",
    "Page.screencastFrameAck",
    # Input (viewer sends mouse/keyboard)
    "Input.dispatchMouseEvent",
    "Input.dispatchKeyEvent",
    "Input.dispatchTouchEvent",
    # Navigation
    "Page.navigate",
    "Page.reload",
    # Page info
    "Page.getFrameTree",
})

# CDP events forwarded from browser to viewer
ALLOWED_EVENTS = frozenset({
    "Page.screencastFrame",
    "Page.frameNavigated",
    "Page.loadEventFired",
    "Page.domContentEventFired",
})


class CDPProxy:
    """Proxies CDP messages between a WebUI viewer and the browser.

    Uses Playwright's CDPSession rather than raw WebSocket to avoid
    needing to know the browser's CDP port.
    """

    def __init__(self):
        self._cdp_session = None
        self._send_to_viewer = None  # callback to send data to the WebUI client
        self._active = False
        self._msg_id = 1000  # Starting ID for our CDP messages

    async def connect(self, session_manager, send_callback):
        """Connect to the browser's CDP session.

        Args:
            session_manager: The SessionManager with an active browser
            send_callback: async function(data: dict) to send messages to the viewer
        """
        self._send_to_viewer = send_callback

        page = await session_manager.get_page()
        if not page:
            raise RuntimeError("No browser page available for CDP proxy")

        # Create a CDP session via Playwright
        context = session_manager.browser_session.browser_context
        if not context:
            raise RuntimeError("No browser context available")

        self._cdp_session = await context.new_cdp_session(page)
        self._active = True

        # Listen for allowed events
        for event in ALLOWED_EVENTS:
            domain, name = event.split(".")
            self._cdp_session.on(event, lambda params, e=event: asyncio.ensure_future(
                self._on_browser_event(e, params)
            ))

        PrintStyle().print("CDP proxy connected")

    async def _on_browser_event(self, event: str, params: dict):
        """Forward browser CDP events to the viewer."""
        if not self._active or not self._send_to_viewer:
            return
        try:
            await self._send_to_viewer({
                "type": "event",
                "method": event,
                "params": params,
            })
        except Exception as e:
            PrintStyle().warning(f"CDP proxy: Failed to forward event {event}: {e}")

    async def handle_viewer_message(self, data: dict) -> Optional[dict]:
        """Handle a message from the WebUI viewer.

        Returns the CDP response if synchronous, or None for fire-and-forget.
        """
        if not self._active or not self._cdp_session:
            return {"error": "CDP proxy not connected"}

        method = data.get("method", "")
        params = data.get("params", {})

        # Security: only allow whitelisted methods
        if method not in ALLOWED_METHODS:
            return {"error": f"Method '{method}' is not allowed"}

        try:
            result = await self._cdp_session.send(method, params)
            return {"id": data.get("id"), "result": result}
        except Exception as e:
            return {"id": data.get("id"), "error": str(e)}

    async def disconnect(self):
        """Disconnect the CDP proxy."""
        self._active = False
        if self._cdp_session:
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None
        self._send_to_viewer = None
        PrintStyle().print("CDP proxy disconnected")
```

**Step 2: Commit**

```bash
git add plugins/browser_use/helpers/cdp_proxy.py
git commit -m "feat(browser_use): add CDP proxy with method whitelisting"
```

---

## Task 7: Extension — Agent Init Cleanup

Clean up orphaned browser sessions when an agent context resets.

**Files:**
- Create: `plugins/browser_use/extensions/python/agent_init/_10_browser_cleanup.py`

**Step 1: Write the extension**

```python
"""Clean up orphaned browser sessions on agent init/reset."""

from python.helpers.extension import Extension


class BrowserCleanup(Extension):
    async def execute(self, **kwargs):
        from plugins.browser_use.helpers.session_manager import SessionManager

        manager = SessionManager.get_existing(self.agent)
        if manager:
            await manager.close()
```

**Step 2: Commit**

```bash
git add plugins/browser_use/extensions/
git commit -m "feat(browser_use): add agent_init cleanup extension"
```

---

## Task 8: Sidebar Extension Button

Add the globe icon to the sidebar that opens the browser viewer.

**Files:**
- Create: `plugins/browser_use/extensions/webui/sidebar-quick-actions-main-start/browser-entry.html`

**Step 1: Write the sidebar button**

Per `A0-PLUGINS.md` baseline: root `x-data` scope plus one explicit `x-move-*` directive.

```html
<div x-data>
  <button
    x-move-after=".config-button#scheduler"
    class="config-button"
    id="browser-viewer"
    @click="openModal('../plugins/browser_use/webui/browser-viewer.html')"
    title="Browser Viewer">
    <span class="material-symbols-outlined">captive_portal</span>
  </button>
</div>
```

**Step 2: Commit**

```bash
git add plugins/browser_use/extensions/webui/
git commit -m "feat(browser_use): add sidebar browser viewer button"
```

---

## Task 9: Browser Viewer Modal — Store

The Alpine store that manages WebSocket lifecycle, screencast rendering, and input events.

**Files:**
- Create: `plugins/browser_use/webui/browser-viewer-store.js`

**Step 1: Write the viewer store**

```javascript
import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    // State
    connected: false,
    agentBusy: false,
    currentUrl: "",
    currentTitle: "",
    alive: false,
    error: null,

    // Internal (not reactive)
    _ws: null,
    _canvas: null,
    _ctx: null,
    _cdpProxy: null,
    _pollInterval: null,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    // Called when modal opens (via x-create)
    async open(canvasEl) {
        this._canvas = canvasEl;
        this._ctx = canvasEl.getContext("2d");
        this.error = null;

        try {
            // Start browser session
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                action: "start",
                context_id: getCurrentContextId(),
            });

            if (result.error) {
                this.error = result.error;
                return;
            }

            this.connected = true;
            this.currentUrl = result.url || "";

            // Start polling for status and screenshots
            this._startPolling();

        } catch (e) {
            this.error = `Failed to connect: ${e.message}`;
        }
    },

    _startPolling() {
        // Poll for status updates and screenshots
        this._pollInterval = setInterval(async () => {
            try {
                const status = await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                    action: "status",
                    context_id: getCurrentContextId(),
                });
                this.alive = status.alive;
                this.agentBusy = status.busy;
                this.currentUrl = status.url || this.currentUrl;
                this.currentTitle = status.title || this.currentTitle;

                // Get screenshot
                if (this.alive) {
                    const shot = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                        action: "screenshot",
                        context_id: getCurrentContextId(),
                    });
                    if (shot.path) {
                        await this._renderScreenshot(shot.path);
                    }
                }
            } catch (e) {
                // Polling error, ignore
            }
        }, 1000);
    },

    async _renderScreenshot(imgPath) {
        if (!this._canvas || !this._ctx) return;

        // Convert img:// path to actual URL
        const cleanPath = imgPath.replace(/^img:\/\//, "").split("&")[0];
        const url = `/image_get?path=${encodeURIComponent(cleanPath)}&t=${Date.now()}`;

        const img = new Image();
        img.onload = () => {
            this._canvas.width = img.width;
            this._canvas.height = img.height;
            this._ctx.drawImage(img, 0, 0);
        };
        img.src = url;
    },

    async navigate(url) {
        if (!url) return;
        try {
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                action: "navigate",
                url: url,
                context_id: getCurrentContextId(),
            });
            if (result.url) {
                this.currentUrl = result.url;
                this.currentTitle = result.title || "";
            }
        } catch (e) {
            this.error = `Navigation failed: ${e.message}`;
        }
    },

    async takeScreenshot() {
        try {
            const result = await callJsonApi("/api/plugins/browser_use/browser_use_interact", {
                action: "screenshot",
                context_id: getCurrentContextId(),
            });
            if (result.path) {
                await this._renderScreenshot(result.path);
            }
        } catch (e) {
            this.error = `Screenshot failed: ${e.message}`;
        }
    },

    async closeBrowser() {
        try {
            await callJsonApi("/api/plugins/browser_use/browser_use_connect", {
                action: "stop",
                context_id: getCurrentContextId(),
            });
            this.connected = false;
            this.alive = false;
        } catch (e) {
            this.error = `Close failed: ${e.message}`;
        }
    },

    // Called when modal closes (via x-destroy)
    destroy() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
        this._canvas = null;
        this._ctx = null;
        this.connected = false;
        this.error = null;
    },
};

function getCurrentContextId() {
    // Get current context from the chats store or URL
    try {
        return window.Alpine?.store("chats")?.selected || "";
    } catch {
        return "";
    }
}

export const store = createStore("browserViewer", model);
```

**Step 2: Commit**

```bash
git add plugins/browser_use/webui/browser-viewer-store.js
git commit -m "feat(browser_use): add browser viewer Alpine store"
```

---

## Task 10: Browser Viewer Modal — HTML

The modal component with URL bar, canvas, and footer.

**Files:**
- Create: `plugins/browser_use/webui/browser-viewer.html`

**Step 1: Write the viewer modal**

```html
<html>
<head>
    <title>Browser Viewer</title>
    <script type="module">
        import { store } from "/plugins/browser_use/webui/browser-viewer-store.js";
    </script>
</head>

<body>
    <div x-data
         x-create="$nextTick(() => $store.browserViewer.open($refs.screenCanvas))"
         x-destroy="$store.browserViewer.destroy()">
        <template x-if="$store.browserViewer">
            <div class="browser-viewer">

                <!-- Error banner -->
                <div class="bv-error" x-show="$store.browserViewer.error" x-cloak>
                    <span class="material-symbols-outlined">error</span>
                    <span x-text="$store.browserViewer.error"></span>
                </div>

                <!-- URL bar -->
                <div class="bv-url-bar">
                    <span class="material-symbols-outlined bv-status"
                          :class="$store.browserViewer.alive ? 'bv-alive' : 'bv-dead'"
                          x-text="$store.browserViewer.alive ? 'circle' : 'cancel'"></span>
                    <input type="text"
                           class="bv-url-input"
                           :value="$store.browserViewer.currentUrl"
                           @keydown.enter="$store.browserViewer.navigate($event.target.value)"
                           placeholder="Enter URL and press Enter...">
                    <button class="bv-go-btn"
                            @click="$store.browserViewer.navigate($el.previousElementSibling.value)">
                        <span class="material-symbols-outlined">arrow_forward</span>
                    </button>
                </div>

                <!-- Browser canvas -->
                <div class="bv-canvas-wrapper">
                    <canvas x-ref="screenCanvas" class="bv-canvas"></canvas>

                    <!-- Agent busy overlay -->
                    <div class="bv-busy-overlay" x-show="$store.browserViewer.agentBusy" x-cloak>
                        <span class="material-symbols-outlined bv-busy-icon">smart_toy</span>
                        <span>Agent is working...</span>
                    </div>

                    <!-- Not connected placeholder -->
                    <div class="bv-placeholder" x-show="!$store.browserViewer.alive && !$store.browserViewer.error" x-cloak>
                        <span class="material-symbols-outlined" style="font-size: 48px; opacity: 0.3;">captive_portal</span>
                        <p>Starting browser...</p>
                    </div>
                </div>

                <!-- Footer -->
                <div class="modal-footer" data-modal-footer>
                    <div class="bv-footer-info">
                        <span class="bv-title" x-text="$store.browserViewer.currentTitle || 'No page loaded'"></span>
                    </div>
                    <div class="bv-footer-actions">
                        <button class="btn btn-ok" @click="$store.browserViewer.takeScreenshot()">
                            <span class="material-symbols-outlined">photo_camera</span>
                            Screenshot
                        </button>
                        <button class="btn btn-cancel" @click="$store.browserViewer.closeBrowser(); closeModal()">
                            <span class="material-symbols-outlined">close</span>
                            Close Browser
                        </button>
                    </div>
                </div>

            </div>
        </template>
    </div>
</body>

<style>
    .browser-viewer {
        display: flex;
        flex-direction: column;
        gap: 8px;
        height: 100%;
    }

    /* Error banner */
    .bv-error {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: rgba(220, 53, 69, 0.15);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 6px;
        color: #ff6b6b;
        font-size: var(--font-size-small);
    }

    /* URL bar */
    .bv-url-bar {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        background: var(--color-input);
        border: 1px solid var(--color-border);
        border-radius: 6px;
    }

    .bv-status {
        font-size: 14px;
    }
    .bv-alive { color: #4caf50; }
    .bv-dead { color: #f44336; }

    .bv-url-input {
        flex: 1;
        border: none;
        background: transparent;
        color: var(--color-text);
        font-size: var(--font-size-small);
        outline: none;
        font-family: monospace;
    }

    .bv-go-btn {
        background: transparent;
        border: none;
        cursor: pointer;
        color: var(--color-text);
        opacity: 0.6;
        padding: 2px;
    }
    .bv-go-btn:hover { opacity: 1; }

    /* Canvas wrapper */
    .bv-canvas-wrapper {
        position: relative;
        flex: 1;
        min-height: 400px;
        background: #1a1a2e;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .bv-canvas {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    /* Agent busy overlay */
    .bv-busy-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: rgba(0, 0, 0, 0.5);
        color: white;
        font-size: var(--font-size-normal);
        z-index: 10;
    }

    .bv-busy-icon {
        font-size: 32px;
        animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }

    /* Placeholder */
    .bv-placeholder {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        color: var(--color-text);
        opacity: 0.5;
    }

    /* Footer */
    .modal-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .bv-footer-info {
        flex: 1;
        overflow: hidden;
    }

    .bv-title {
        font-size: var(--font-size-small);
        opacity: 0.7;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .bv-footer-actions {
        display: flex;
        gap: 8px;
    }

    .bv-footer-actions .btn {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: var(--font-size-small);
    }

    .bv-footer-actions .material-symbols-outlined {
        font-size: 16px;
    }

    [x-cloak] { display: none !important; }
</style>

</html>
```

**Step 2: Commit**

```bash
git add plugins/browser_use/webui/browser-viewer.html
git commit -m "feat(browser_use): add browser viewer modal with canvas and URL bar"
```

---

## Task 11: Browser Settings UI

Settings tab component for plugin configuration.

**Files:**
- Create: `plugins/browser_use/webui/browser-settings-store.js`
- Create: `plugins/browser_use/webui/browser-settings.html`

**Step 1: Write the settings store**

```javascript
import { createStore } from "/js/AlpineStore.js";
import { callJsonApi, fetchApi } from "/js/api.js";

const model = {
    settings: {
        browser_mode: "chromium",
        headless: false,
        default_max_steps: 25,
        vision_mode: "auto",
        flash_mode: false,
        screencast_quality: 80,
        window_size: "1024x768",
        browser_use_api_key: "",
    },
    loading: false,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    async load() {
        this.loading = true;
        try {
            const response = await fetchApi("/api/plugins/browser_use/browser_use_settings", {
                method: "GET",
            });
            const data = await response.json();
            if (data.settings) {
                Object.assign(this.settings, data.settings);
            }
        } catch (e) {
            console.error("Failed to load browser settings:", e);
        }
        this.loading = false;
    },

    async save() {
        try {
            await callJsonApi("/api/plugins/browser_use/browser_use_settings", {
                settings: this.settings,
            });
        } catch (e) {
            console.error("Failed to save browser settings:", e);
        }
    },
};

export const store = createStore("browserSettings", model);
```

**Step 2: Write the settings HTML**

```html
<html>
<head>
    <title>Browser Settings</title>
    <script type="module">
        import { store } from "/plugins/browser_use/webui/browser-settings-store.js";
    </script>
</head>

<body>
    <div x-data x-create="$store.browserSettings.load()">
        <template x-if="$store.browserSettings">
            <div class="browser-settings">

                <div class="section">
                    <div class="section-title">Browser Configuration</div>

                    <div class="field">
                        <label>Browser Mode</label>
                        <div class="field-control">
                            <select x-model="$store.browserSettings.settings.browser_mode"
                                    @change="$store.browserSettings.save()">
                                <option value="chromium">Chromium (headless capable)</option>
                                <option value="real">Real Chrome (with login sessions)</option>
                                <option value="remote">Remote Cloud Browser</option>
                            </select>
                        </div>
                    </div>

                    <div class="field">
                        <label>Headless Mode</label>
                        <div class="field-control">
                            <input type="checkbox"
                                   x-model="$store.browserSettings.settings.headless"
                                   @change="$store.browserSettings.save()">
                            <span class="section-description">Run without visible window (CDP screencast still works)</span>
                        </div>
                    </div>

                    <div class="field">
                        <label>Window Size</label>
                        <div class="field-control">
                            <select x-model="$store.browserSettings.settings.window_size"
                                    @change="$store.browserSettings.save()">
                                <option value="1024x768">1024 x 768</option>
                                <option value="1280x720">1280 x 720 (HD)</option>
                                <option value="1920x1080">1920 x 1080 (Full HD)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">Agent Defaults</div>

                    <div class="field">
                        <label>Default Max Steps</label>
                        <div class="field-control">
                            <input type="number" min="5" max="100"
                                   x-model.number="$store.browserSettings.settings.default_max_steps"
                                   @change="$store.browserSettings.save()">
                        </div>
                    </div>

                    <div class="field">
                        <label>Vision Mode</label>
                        <div class="field-control">
                            <select x-model="$store.browserSettings.settings.vision_mode"
                                    @change="$store.browserSettings.save()">
                                <option value="auto">Auto (use when needed)</option>
                                <option value="true">Always On</option>
                                <option value="false">Always Off</option>
                            </select>
                        </div>
                    </div>

                    <div class="field">
                        <label>Flash Mode</label>
                        <div class="field-control">
                            <input type="checkbox"
                                   x-model="$store.browserSettings.settings.flash_mode"
                                   @change="$store.browserSettings.save()">
                            <span class="section-description">Fast mode: skips evaluation and thinking</span>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">Viewer</div>

                    <div class="field">
                        <label>Screencast Quality</label>
                        <div class="field-control">
                            <input type="range" min="10" max="100" step="10"
                                   x-model.number="$store.browserSettings.settings.screencast_quality"
                                   @change="$store.browserSettings.save()">
                            <span x-text="$store.browserSettings.settings.screencast_quality + '%'"
                                  style="min-width: 3em; text-align: right;"></span>
                        </div>
                    </div>
                </div>

                <div class="section" x-show="$store.browserSettings.settings.browser_mode === 'remote'">
                    <div class="section-title">Remote Browser</div>

                    <div class="field">
                        <label>Browser Use API Key</label>
                        <div class="field-control">
                            <input type="password"
                                   x-model="$store.browserSettings.settings.browser_use_api_key"
                                   @change="$store.browserSettings.save()"
                                   placeholder="bu_...">
                        </div>
                    </div>
                </div>

            </div>
        </template>
    </div>
</body>

<style>
    .browser-settings {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .browser-settings .field {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px 0;
    }

    .browser-settings .field label {
        min-width: 160px;
        font-size: var(--font-size-small);
        opacity: 0.8;
    }

    .browser-settings .field-control {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .browser-settings .field-control select,
    .browser-settings .field-control input[type="number"],
    .browser-settings .field-control input[type="password"] {
        width: auto;
        max-width: 300px;
    }
</style>

</html>
```

**Step 3: Commit**

```bash
git add plugins/browser_use/webui/browser-settings-store.js plugins/browser_use/webui/browser-settings.html
git commit -m "feat(browser_use): add browser settings UI component"
```

---

## Task 12: Integration Testing

Manual smoke test to verify the plugin works end-to-end.

**Files:** None (testing only)

**Step 1: Verify plugin directory is complete**

```bash
find plugins/browser_use -type f | sort
```

Expected output (all 12 files):
```
plugins/browser_use/api/browser_use_connect.py
plugins/browser_use/api/browser_use_interact.py
plugins/browser_use/api/browser_use_settings.py
plugins/browser_use/extensions/python/agent_init/_10_browser_cleanup.py
plugins/browser_use/extensions/webui/sidebar-quick-actions-main-start/browser-entry.html
plugins/browser_use/helpers/cdp_proxy.py
plugins/browser_use/helpers/session_manager.py
plugins/browser_use/prompts/agent.system.tool.browser_step.md
plugins/browser_use/tools/browser_auto.py
plugins/browser_use/tools/browser_step.py
plugins/browser_use/webui/browser-settings-store.js
plugins/browser_use/webui/browser-settings.html
plugins/browser_use/webui/browser-viewer-store.js
plugins/browser_use/webui/browser-viewer.html
```

**Step 2: Verify Python imports work**

```bash
cd /Users/lazy/agent-zero-dev
python -c "from plugins.browser_use.helpers.session_manager import SessionManager; print('SessionManager OK')"
python -c "from plugins.browser_use.helpers.cdp_proxy import CDPProxy, ALLOWED_METHODS; print(f'CDPProxy OK, {len(ALLOWED_METHODS)} methods whitelisted')"
```

**Step 3: Note integration gaps**

The following require PR #998 infrastructure to fully function:
- Plugin API route registration (`/api/plugins/browser_use/<handler>`) — needs `run_ui.py` plugin handler discovery
- Plugin tool discovery — needs `subagents.get_paths(..., include_plugins=True)`
- Extension point loading — needs plugin extension discovery in `extension.py`
- Sidebar extension injection — needs `extensions.js` and `x-extension` breakpoints
- Plugin static asset serving — needs `GET /plugins/<id>/<path>` route

These are all provided by PR #998. The plugin code is structured to work with that infrastructure out of the box.

**Step 4: Final commit with all files**

```bash
git add plugins/browser_use/
git status
git commit -m "feat: complete browser_use plugin with tools, viewer, and settings

Browser-use plugin for Agent Zero providing:
- browser_step: deterministic step-by-step browser control (12 actions)
- browser_auto: enhanced autonomous browser-use Agent
- CDP screencast viewer modal accessible from sidebar
- Browser settings UI component
- Shared SessionManager for tool/viewer coordination
- CDP proxy with method whitelisting for security
- Agent init cleanup extension"
```

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Directory scaffold | directories only |
| 2 | Session Manager | `helpers/session_manager.py` |
| 3 | Browser Step Tool | `tools/browser_step.py`, `prompts/agent.system.tool.browser_step.md` |
| 4 | Browser Auto Tool | `tools/browser_auto.py` |
| 5 | API Handlers | `api/browser_use_connect.py`, `api/browser_use_interact.py`, `api/browser_use_settings.py` |
| 6 | CDP Proxy | `helpers/cdp_proxy.py` |
| 7 | Cleanup Extension | `extensions/python/agent_init/_10_browser_cleanup.py` |
| 8 | Sidebar Button | `extensions/webui/.../browser-entry.html` |
| 9 | Viewer Store | `webui/browser-viewer-store.js` |
| 10 | Viewer Modal | `webui/browser-viewer.html` |
| 11 | Settings UI | `webui/browser-settings-store.js`, `webui/browser-settings.html` |
| 12 | Integration Test | verification only |

**Total: 14 files across 12 tasks**
