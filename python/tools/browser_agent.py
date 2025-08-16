import asyncio
import time
import json
from typing import Optional, cast
from agent import Agent, InterventionException
from pathlib import Path

from python.helpers.tool import Tool, Response
from python.helpers import files, defer, persist_chat, strings
from python.helpers.browser_use import browser_use  # type: ignore[attr-defined]
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary
from python.helpers.secrets import SecretsManager
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from pydantic import BaseModel
import uuid
from python.helpers.dirty_json import DirtyJson


class State:
    @staticmethod
    async def create(agent: Agent):
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.secrets_dict: Optional[dict[str, str]] = None
        self.iter_no = 0
        self.using_external_browser = False

    def __del__(self):
        self.kill_task()

    async def _initialize(self):
        if self.browser_session:
            return

        # Check if we should use external browser for manual control
        use_external = False
        external_cdp_url = None
        
        try:
            from python.services.browser_session_manager import get_browser_session_manager
            from python.helpers import settings
            
            config = settings.get_settings()
            if config.get("browser_manual_control_enabled", False):
                # Try to connect to existing browser session
                manager = get_browser_session_manager()
                if manager.is_running:
                    connection_info = manager.get_connection_info()
                    if connection_info.get("cdp_url"):
                        external_cdp_url = connection_info["cdp_url"]
                        use_external = True
                        PrintStyle().info(f"Using external browser session: {external_cdp_url}")
        except Exception as e:
            PrintStyle().warning(f"Could not check for external browser: {e}")

        if use_external and external_cdp_url:
            # Connect to external browser via CDP
            self.browser_session = browser_use.BrowserSession(
                cdp_url=external_cdp_url,
                browser_profile=browser_use.BrowserProfile(
                    keep_alive=True,
                    minimum_wait_page_load_time=1.0,
                    wait_for_network_idle_page_load_time=2.0,
                    maximum_wait_page_load_time=10.0,
                    screen={"width": 1920, "height": 1080},
                    viewport={"width": 1920, "height": 1080},
                )
            )
            self.using_external_browser = True
        else:
            # Use standard headless browser
            # for some reason we need to provide exact path to headless shell, otherwise it looks for headed browser
            pw_binary = ensure_playwright_binary()

            self.browser_session = browser_use.BrowserSession(
                browser_profile=browser_use.BrowserProfile(
                    headless=True,
                    disable_security=True,
                    chromium_sandbox=False,
                    accept_downloads=True,
                    downloads_dir=files.get_abs_path("tmp/downloads"),
                    downloads_path=files.get_abs_path("tmp/downloads"),
                    executable_path=pw_binary,
                    keep_alive=True,
                    minimum_wait_page_load_time=1.0,
                    wait_for_network_idle_page_load_time=2.0,
                    maximum_wait_page_load_time=10.0,
                    screen={"width": 1024, "height": 2048},
                    viewport={"width": 1024, "height": 2048},
                    args=["--headless=new"],
                    # Use a unique user data directory to avoid conflicts
                    user_data_dir=str(
                        Path.home()
                        / ".config"
                        / "browseruse"
                        / "profiles"
                        / f"agent_{self.agent.context.id}"
                    ),
                )
            )
            self.using_external_browser = False

        await self.browser_session.start() if self.browser_session else None
        # self.override_hooks()

        # Add init script to the browser session
        if self.browser_session and self.browser_session.browser_context:
            js_override = files.get_abs_path("lib/browser/init_override.js")
            await self.browser_session.browser_context.add_init_script(path=js_override) if self.browser_session else None

    def start_task(self, task: str):
        if self.task and self.task.is_alive():
            self.kill_task()

        self.task = defer.DeferredTask(
            thread_name="BrowserAgent" + self.agent.context.id
        )
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task, terminate_thread=True)
        self.task.start_task(self._run_task, task) if self.task else None
        return self.task

    def kill_task(self):
        if self.task:
            self.task.kill(terminate_thread=True)
            self.task = None
        if self.browser_session:
            # Don't close external browser sessions - they're managed separately
            if not self.using_external_browser:
                try:
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.browser_session.close()) if self.browser_session else None
                    loop.close()
                except Exception as e:
                    PrintStyle().error(f"Error closing browser session: {e}")
            self.browser_session = None
        self.use_agent = None
        self.iter_no = 0

    async def _run_task(self, task: str):
        await self._initialize()

        # Check if manual control is enabled and we should offer it as a fallback
        try:
            from python.helpers import settings
            config = settings.get_settings()
            manual_control_enabled = config.get('browser_manual_control_enabled', False)
        except:
            manual_control_enabled = False

        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        # Initialize controller
        controller = browser_use.Controller(output_model=DoneResult)

        # Register custom completion action with proper ActionResult fields
        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(
                is_done=True, success=True, extracted_content=params.model_dump_json()
            )
            return result

        # Try to get the model, but handle failures gracefully
        try:
            model = self.agent.get_browser_model()
        except Exception as model_error:
            PrintStyle().error(f"Failed to get browser model: {model_error}")
            
            # If manual control is enabled and we have external browser, offer manual control
            if manual_control_enabled and hasattr(self, 'using_external_browser') and self.using_external_browser:
                PrintStyle().info("Offering manual control due to model failure")
                return type('MockResult', (), {
                    'is_done': lambda: True,
                    'success': lambda: True,
                    'final_result': lambda: json.dumps({
                        "title": "Manual Control Required",
                        "response": f"Browser model failed to initialize ({str(model_error)}). Manual browser control is available - click the 'Manual Control' button to control the browser directly using Chrome DevTools.",
                        "page_summary": "Browser session is ready for manual control via DevTools interface."
                    })
                })()
            else:
                raise Exception(f"Failed to get browser model: {model_error}")

        # If we got here, we have a model, so continue with LLM test

        try:
            # Test LLM connection before initializing browser agent
            try:
                # Try a simple call to test the model
                test_response = model.invoke("test")
                PrintStyle().info("LLM connection test successful")
            except Exception as llm_error:
                PrintStyle().warning(f"LLM connection failed: {llm_error}")
                
                # If using external browser, we can still provide manual control
                if self.using_external_browser:
                    PrintStyle().info("External browser available for manual control despite LLM issues")
                    # Return a response suggesting manual control
                    return {
                        "is_done": lambda: True,
                        "success": lambda: True,
                        "final_result": lambda: json.dumps({
                            "title": "Manual Control Available",
                            "response": "LLM connection failed, but manual browser control is available. Click the 'Manual Control' button to control the browser manually.",
                            "page_summary": "Browser session is running and ready for manual control."
                        })
                    }
                else:
                    raise Exception(f"Failed to connect to LLM. Please check your API key and network connection. Error: {llm_error}")

            secrets_manager = SecretsManager.get_instance()
            secrets_dict = secrets_manager.load_secrets()

            self.use_agent = browser_use.Agent(
                task=task,
                browser_session=self.browser_session,
                llm=model,
                use_vision=self.agent.config.browser_model.vision,
                extend_system_message=self.agent.read_prompt(
                    "prompts/browser_agent.system.md"
                ),
                controller=controller,
                enable_memory=False,  # Disable memory to avoid state conflicts
                sensitive_data=cast(dict[str, str | dict[str, str]] | None, secrets_dict or {}),  # Pass secrets
            )
        except Exception as e:
            # If we have an external browser available, suggest manual control
            if hasattr(self, 'using_external_browser') and self.using_external_browser:
                PrintStyle().warning(f"Browser agent initialization failed, but manual control is available: {e}")
                return {
                    "is_done": lambda: True,
                    "success": lambda: True,
                    "final_result": lambda: json.dumps({
                        "title": "Manual Control Available",
                        "response": f"Browser agent initialization failed ({str(e)}), but manual browser control is available. Click the 'Manual Control' button to control the browser manually.",
                        "page_summary": "Browser session is running and ready for manual control."
                    })
                }
            else:
                raise Exception(
                    f"Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}"
                ) from e

        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")

        # try:
        result = None
        if self.use_agent:
            result = await self.use_agent.run(
                max_steps=50, on_step_start=hook, on_step_end=hook
            )
        return result

    async def get_page(self):
        if self.use_agent and self.browser_session:
            try:
                return await self.use_agent.browser_session.get_current_page() if self.use_agent.browser_session else None
            except Exception:
                # Browser session might be closed or invalid
                return None
        return None

    async def get_selector_map(self):
        """Get the selector map for the current page state."""
        if self.use_agent:
            await self.use_agent.browser_session.get_state_summary(cache_clickable_elements_hashes=True) if self.use_agent.browser_session else None
            return await self.use_agent.browser_session.get_selector_map() if self.use_agent.browser_session else None
            await self.use_agent.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True
            )
            return await self.use_agent.browser_session.get_selector_map()
        return {}


class BrowserAgent(Tool):

    async def execute(self, message="", reset="", **kwargs):
        self.guid = str(uuid.uuid4())
        reset = str(reset).lower().strip() == "true"
        await self.prepare_state(reset=reset)
        
        # Check if manual control is enabled for fallback scenarios
        try:
            from python.helpers import settings
            config = settings.get_settings()
            manual_control_enabled = config.get('browser_manual_control_enabled', False)
        except:
            manual_control_enabled = False
        
        try:
            task = self.state.start_task(message) if self.state else None
        except Exception as task_error:
            PrintStyle().error(f"Failed to start browser task: {task_error}")
            
            # If manual control is enabled, try to at least start the browser session
            if manual_control_enabled:
                try:
                    # Ensure we have a browser session for manual control
                    if self.state and hasattr(self.state, 'using_external_browser') and self.state.using_external_browser:
                        # External browser should already be running
                        manual_message = f"Browser agent failed to start ({str(task_error)}), but manual browser control is available. Click the 'Manual Control' button to control the browser using Chrome DevTools."
                    else:
                        # Try to start browser session for manual control
                        from python.services.browser_session_manager import get_browser_session_manager
                        browser_manager = get_browser_session_manager()
                        browser_info = browser_manager.start_browser_session(headless=False)
                        if browser_info.get('is_running'):
                            manual_message = f"Browser agent failed to start ({str(task_error)}), but manual browser control has been started. Click the 'Manual Control' button to control the browser using Chrome DevTools."
                        else:
                            raise Exception("Could not start browser for manual control")
                    
                    # Return a response suggesting manual control
                    self.log.update(answer=self._mask(manual_message))
                    return Response(message=self._mask(manual_message), break_loop=False)
                    
                except Exception as manual_error:
                    PrintStyle().error(f"Manual control fallback also failed: {manual_error}")
            
            # If we get here, both automated and manual control failed
            error_message = f"Browser agent failed to start: {str(task_error)}"
            if not manual_control_enabled:
                error_message += "\n\nTip: Enable 'Manual Browser Control' in settings for a fallback option when LLM issues occur."
            
            self.log.update(answer=self._mask(error_message))
            return Response(message=self._mask(error_message), break_loop=False)

        # wait for browser agent to finish and update progress with timeout
        timeout_seconds = 300  # 5 minute timeout
        start_time = time.time()

        fail_counter = 0
        while not task.is_ready() if task else False:
            # Check for timeout to prevent infinite waiting
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(
                    self._mask(f"Browser agent task timeout after {timeout_seconds} seconds, forcing completion")
                )
                break

            await self.agent.handle_intervention()
            await asyncio.sleep(1)
            try:
                if task and task.is_ready():  # otherwise get_update hangs
                    break
                try:
                    update = await asyncio.wait_for(self.get_update(), timeout=10)
                    fail_counter = 0  # reset on success
                except asyncio.TimeoutError:
                    fail_counter += 1
                    PrintStyle().warning(
                        self._mask(f"browser_agent.get_update timed out ({fail_counter}/3)")
                    )
                    if fail_counter >= 3:
                        PrintStyle().warning(
                            self._mask("3 consecutive browser_agent.get_update timeouts, breaking loop")
                        )
                        break
                    continue
                update_log = update.get("log", get_use_agent_log(None))
                self.update_progress("\n".join(update_log))
                screenshot = update.get("screenshot", None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(self._mask(f"Error getting update: {str(e)}"))

        if task and not task.is_ready():
            PrintStyle().warning(self._mask("browser_agent.get_update timed out, killing the task"))
            self.state.kill_task() if self.state else None
            return Response(
                message=self._mask("Browser agent task timed out, not output provided."),
                break_loop=False,
            )

        # final progress update
        if self.state and self.state.use_agent:
            log_final = get_use_agent_log(self.state.use_agent)
            self.update_progress("\n".join(log_final))

        # collect result with error handling
        try:
            result = await task.result() if task else None
        except Exception as e:
            PrintStyle().error(self._mask(f"Error getting browser agent task result: {str(e)}"))
            # Return a timeout response if task.result() fails
            answer_text = self._mask(f"Browser agent task failed to return result: {str(e)}")
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)
        # finally:
        #     # Stop any further browser access after task completion
        #     # self.state.kill_task()
        #     pass

        # Check if task completed successfully
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)  # type: ignore
                else:
                    answer_text = (
                        str(answer) if answer else "Task completed successfully"
                    )
            except Exception as e:
                answer_text = (
                    str(answer)
                    if answer
                    else f"Task completed with parse error: {str(e)}"
                )
        else:
            # Task hit max_steps without calling done()
            urls = result.urls() if result else []
            current_url = urls[-1] if urls else "unknown"
            answer_text = (
                f"Task reached step limit without completion. Last page: {current_url}. "
                f"The browser agent may need clearer instructions on when to finish."
            )

        # Mask answer for logs and response
        answer_text = self._mask(answer_text)

        # update the log (without screenshot path here, user can click)
        self.log.update(answer=answer_text)

        # add screenshot to the answer if we have it
        if (
            self.log.kvps
            and "screenshot" in self.log.kvps
            and self.log.kvps["screenshot"]
        ):
            path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        # respond (with screenshot path)
        return Response(message=answer_text, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Calling Browser Agent",
            content="",
            kvps=self.args,
        )

    async def get_update(self):
        await self.prepare_state()

        result = {}
        agent = self.agent
        ua = self.state.use_agent if self.state else None
        page = await self.state.get_page() if self.state else None

        if ua and page:
            try:

                async def _get_update():

                    # await agent.wait_if_paused() # no need here

                    # Build short activity log
                    result["log"] = get_use_agent_log(ua)

                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(agent.context.id),
                        "browser",
                        "screenshots",
                        f"{self.guid}.png",
                    )
                    files.make_dirs(path)
                    await page.screenshot(path=path, full_page=False, timeout=3000)
                    result["screenshot"] = f"img://{path}&t={str(time.time())}"

                if self.state and self.state.task and not self.state.task.is_ready():
                    await self.state.task.execute_inside(_get_update)

            except Exception:
                pass

        return result

    async def prepare_state(self, reset=False):
        self.state = self.agent.get_data("_browser_agent_state")
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data("_browser_agent_state", self.state)

    def update_progress(self, text):
        text = self._mask(text)
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        progress = f"Browser: {short}"

        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) -> str:
        try:
            return SecretsManager.get_instance().mask_values(text or "")
        except Exception as e:
            return text or ""

    # def __del__(self):
    #     if self.state:
    #         self.state.kill_task()


def get_use_agent_log(use_agent: browser_use.Agent | None):
    result = ["🚦 Starting task"]
    if use_agent:
        action_results = use_agent.state.history.action_results()
        short_log = []
        for item in action_results:
            # final results
            if item.is_done:
                if item.success:
                    short_log.append("✅ Done")
                else:
                    short_log.append(
                        f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}"
                    )

            # progress messages
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split("\n", 1)[0][:200]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
