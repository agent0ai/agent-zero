"""
Standalone Browser Agent for natural language web automation.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from pydantic import BaseModel
import nest_asyncio

# Disable browser-use telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "false"

import browser_use
from browser_use import Agent as BrowserUseAgent, BrowserSession, BrowserProfile, Controller
from litellm import completion

from .config import Config
from .helpers import apply_monkeypatch, ensure_playwright_installed, get_playwright_binary


# Apply monkey patches
apply_monkeypatch()

# Allow nested event loops
nest_asyncio.apply()


class TaskResult(BaseModel):
    """Result of a browser automation task."""

    title: str
    response: str
    page_summary: str
    success: bool = True
    final_url: Optional[str] = None
    screenshots: list[str] = []


class BrowserAgent:
    """
    Standalone browser agent for web automation using natural language.

    Example:
        ```python
        from browser_agent import BrowserAgent

        agent = BrowserAgent()
        result = await agent.run("Go to google.com and search for 'Python'")
        print(result.response)
        ```
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the browser agent.

        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or Config.from_env()
        self.browser_session: Optional[BrowserSession] = None
        self._ensure_setup()

    def _ensure_setup(self):
        """Ensure all dependencies are properly installed."""
        ensure_playwright_installed()

    async def _initialize_browser(self) -> BrowserSession:
        """Initialize browser session."""
        if self.browser_session:
            return self.browser_session

        # Get playwright binary if available
        pw_binary = get_playwright_binary()

        # Create browser profile
        profile = BrowserProfile(
            headless=self.config.browser.headless,
            disable_security=self.config.browser.disable_security,
            chromium_sandbox=False,
            accept_downloads=True,
            downloads_path=self.config.browser.downloads_path,
            allowed_domains=["*", "http://*", "https://*"],
            executable_path=pw_binary,
            keep_alive=True,
            minimum_wait_page_load_time=1.0,
            wait_for_network_idle_page_load_time=2.0,
            maximum_wait_page_load_time=10.0,
            window_size={"width": self.config.browser.width, "height": self.config.browser.height},
            screen={"width": self.config.browser.width, "height": self.config.browser.height},
            viewport={"width": self.config.browser.width, "height": self.config.browser.height},
            no_viewport=False,
            args=["--headless=new"] if self.config.browser.headless else [],
            user_data_dir=self.config.browser.user_data_dir,
            extra_http_headers=self.config.browser.extra_http_headers,
        )

        # Create browser session
        self.browser_session = BrowserSession(browser_profile=profile)
        await self.browser_session.start()

        # Force viewport size (browser-use sometimes overrides this)
        try:
            page = await self.browser_session.get_current_page()
            if page:
                await page.set_viewport_size({
                    "width": self.config.browser.width,
                    "height": self.config.browser.height
                })
        except Exception as e:
            print(f"Warning: Could not set viewport size: {e}")

        # Add init script for shadow DOM access
        if self.browser_session and self.browser_session.browser_context:
            js_override_path = Path(__file__).parent / "js" / "init_override.js"
            if js_override_path.exists():
                await self.browser_session.browser_context.add_init_script(
                    path=str(js_override_path)
                )

        return self.browser_session

    def _get_llm_model(self):
        """Get LLM model for browser-use."""
        # Create a simple LLM wrapper for litellm
        class LiteLLMWrapper:
            def __init__(self, config):
                self.config = config

            async def __call__(self, messages, **kwargs):
                """Call LiteLLM completion API."""
                response = await asyncio.to_thread(
                    completion,
                    model=self.config.get_llm_model(),
                    messages=messages,
                    api_key=self.config.llm.api_key,
                    temperature=self.config.llm.temperature,
                    **kwargs
                )
                return response

        return LiteLLMWrapper(self.config)

    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
        if prompt_path.exists():
            return prompt_path.read_text()
        return ""

    async def run(
        self,
        task: str,
        max_steps: Optional[int] = None,
        on_step_start: Optional[Callable] = None,
        on_step_end: Optional[Callable] = None,
    ) -> TaskResult:
        """
        Run a browser automation task.

        Args:
            task: Natural language task description
            max_steps: Maximum number of steps (overrides config)
            on_step_start: Callback called before each step
            on_step_end: Callback called after each step

        Returns:
            TaskResult containing the task outcome

        Example:
            ```python
            result = await agent.run("Go to example.com and get the page title")
            print(result.response)
            ```
        """
        # Initialize browser
        browser_session = await self._initialize_browser()

        # Create done result model
        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        # Create controller with custom completion action
        controller = Controller(output_model=DoneResult)

        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(
                is_done=True,
                success=True,
                extracted_content=params.model_dump_json()
            )
            return result

        # Get LLM model
        llm = self._get_llm_model()

        # Load system prompt
        system_prompt = self._load_system_prompt()

        # Create browser-use agent
        agent = BrowserUseAgent(
            task=task,
            browser_session=browser_session,
            llm=llm,
            use_vision=self.config.llm.use_vision,
            extend_system_message=system_prompt,
            controller=controller,
            enable_memory=self.config.agent.enable_memory,
            llm_timeout=self.config.agent.llm_timeout,
        )

        # Run the agent
        steps = max_steps or self.config.agent.max_steps
        result = await agent.run(
            max_steps=steps,
            on_step_start=on_step_start,
            on_step_end=on_step_end,
        )

        # Parse result
        final_result = self._parse_result(result)

        return final_result

    def _parse_result(self, result) -> TaskResult:
        """Parse browser-use result into TaskResult."""
        import json

        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = json.loads(answer)
                    return TaskResult(
                        title=answer_data.get("title", "Task Completed"),
                        response=answer_data.get("response", "Task completed successfully"),
                        page_summary=answer_data.get("page_summary", ""),
                        success=True,
                        final_url=result.urls()[-1] if result.urls() else None,
                    )
                else:
                    return TaskResult(
                        title="Task Completed",
                        response=str(answer) if answer else "Task completed successfully",
                        page_summary="",
                        success=True,
                        final_url=result.urls()[-1] if result.urls() else None,
                    )
            except Exception as e:
                return TaskResult(
                    title="Task Completed with Warning",
                    response=str(answer) if answer else f"Task completed but failed to parse result: {e}",
                    page_summary="",
                    success=True,
                    final_url=result.urls()[-1] if result.urls() else None,
                )
        else:
            # Task hit max_steps without calling done()
            urls = result.urls() if result else []
            current_url = urls[-1] if urls else "unknown"
            return TaskResult(
                title="Task Incomplete",
                response=f"Task reached step limit without completion. Last page: {current_url}",
                page_summary="",
                success=False,
                final_url=current_url if current_url != "unknown" else None,
            )

    async def screenshot(self, path: str, full_page: bool = False):
        """
        Take a screenshot of the current page.

        Args:
            path: Path to save screenshot
            full_page: Whether to capture full page or just viewport
        """
        if not self.browser_session:
            raise RuntimeError("Browser session not initialized. Run a task first.")

        page = await self.browser_session.get_current_page()
        if page:
            await page.screenshot(path=path, full_page=full_page)

    async def close(self):
        """Close the browser session."""
        if self.browser_session:
            await self.browser_session.close()
            self.browser_session = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
