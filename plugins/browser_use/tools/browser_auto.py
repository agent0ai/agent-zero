"""Autonomous browser-use Agent tool.

Wraps browser-use's Agent class with configurable parameters and shared
SessionManager. Acquires the session lock for the entire autonomous run.
"""

import asyncio
import time
from typing import cast

from agent import InterventionException
from python.helpers.tool import Tool, Response
from python.helpers import files, persist_chat, strings
from python.helpers.browser_use import browser_use  # type: ignore[attr-defined]
from python.helpers.print_style import PrintStyle
from python.helpers.secrets import get_secrets_manager
from python.helpers.dirty_json import DirtyJson
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from plugins.browser_use.helpers.session_manager import SessionManager
from pydantic import BaseModel


class BrowserAuto(Tool):

    async def execute(
        self,
        task="",
        max_steps="25",
        vision="auto",
        flash_mode="false",
        reset="false",
        **kwargs,
    ) -> Response:
        # Parse arguments
        task = str(task).strip()
        if not task:
            return Response(
                message="Error: 'task' argument is required.",
                break_loop=False,
            )

        try:
            max_steps_int = int(max_steps)
        except (ValueError, TypeError):
            max_steps_int = 25

        # Vision: "auto" uses config, "true"/"false" overrides
        vision_str = str(vision).strip().lower()
        if vision_str == "true":
            use_vision = True
        elif vision_str == "false":
            use_vision = False
        else:
            # "auto" — use the config setting
            use_vision = self.agent.config.browser_model.vision

        flash_mode_bool = str(flash_mode).strip().lower() == "true"
        reset_bool = str(reset).strip().lower() == "true"

        # Get or create SessionManager, optionally reset
        if reset_bool:
            existing = SessionManager.get_existing(self.agent)
            if existing:
                await existing.close()

        manager = SessionManager.get_or_create(self.agent)
        await manager.ensure_started()

        # Mask secrets in the task text
        secrets_manager = get_secrets_manager(self.agent.context)
        task = secrets_manager.mask_values(
            task, placeholder="<secret>{key}</secret>"
        )

        # Generate a unique ID for screenshots
        guid = self.agent.context.generate_id()

        # Acquire lock for the entire autonomous run
        async with manager.lock:
            return await self._run_autonomous(
                manager=manager,
                task=task,
                max_steps=max_steps_int,
                use_vision=use_vision,
                flash_mode=flash_mode_bool,
                guid=guid,
                secrets_manager=secrets_manager,
            )

    async def _run_autonomous(
        self,
        manager: SessionManager,
        task: str,
        max_steps: int,
        use_vision: bool,
        flash_mode: bool,
        guid: str,
        secrets_manager,
    ) -> Response:
        """Run the browser-use Agent with the shared session."""

        # Define the done result model
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
                is_done=True,
                success=True,
                extracted_content=params.model_dump_json(),
            )
            return result

        model = self.agent.get_browser_model()

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
                llm_timeout=120,
                sensitive_data=cast(
                    dict[str, str | dict[str, str]] | None,
                    secrets_manager.load_secrets() or {},
                ),
            )
        except Exception as e:
            raise Exception(
                f"Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}"
            ) from e

        # Track iteration number for cancellation detection
        iter_no = get_iter_no(self.agent)

        # Step hooks for pause/resume and cancellation
        async def on_step_start(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")

        async def on_step_end(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")

            # Update progress and screenshot
            try:
                log_lines = _get_use_agent_log(use_agent)
                self._update_progress("\n".join(log_lines))

                page = await manager.get_page()
                if page:
                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(self.agent.context.id),
                        "browser",
                        "screenshots",
                        f"{guid}.png",
                    )
                    files.make_dirs(path)
                    await page.screenshot(
                        path=path, full_page=False, timeout=3000
                    )
                    self.log.update(
                        screenshot=f"img://{path}&t={str(time.time())}"
                    )
            except Exception as e:
                PrintStyle().warning(
                    self._mask(f"Error updating progress/screenshot: {e}")
                )

        # Run the agent with timeout
        timeout_seconds = 300  # 5 minute timeout

        try:
            result = await asyncio.wait_for(
                use_agent.run(
                    max_steps=max_steps,
                    on_step_start=on_step_start,
                    on_step_end=on_step_end,
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            answer_text = self._mask(
                f"Browser agent task timed out after {timeout_seconds} seconds."
            )
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)
        except InterventionException:
            answer_text = self._mask("Browser agent task was cancelled.")
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)
        except Exception as e:
            answer_text = self._mask(
                f"Browser agent task failed: {str(e)}"
            )
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)

        # Final progress update
        log_final = _get_use_agent_log(use_agent)
        self._update_progress("\n".join(log_final))

        # Process result
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

        # Mask secrets in output
        answer_text = self._mask(answer_text)

        # Update log
        self.log.update(answer=answer_text)

        # Add screenshot to the answer if we have it
        if (
            self.log.kvps
            and "screenshot" in self.log.kvps
            and self.log.kvps["screenshot"]
        ):
            path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        return Response(message=answer_text, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Browser Auto",
            content="",
            kvps=self.args,
            _tool_name="browser_auto",
        )

    def _update_progress(self, text: str):
        text = self._mask(text)
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        progress = f"Browser: {short}"

        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) -> str:
        try:
            return get_secrets_manager(self.agent.context).mask_values(text or "")
        except Exception:
            return text or ""


def _get_use_agent_log(use_agent: browser_use.Agent | None) -> list[str]:
    """Extract a short activity log from the browser-use agent's history."""
    result = ["Starting task"]
    if use_agent:
        action_results = use_agent.history.action_results() or []
        short_log = []
        for item in action_results:
            if item.is_done:
                if item.success:
                    short_log.append("Done")
                else:
                    short_log.append(
                        f"Error: {item.error or item.extracted_content or 'Unknown error'}"
                    )
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split("\n", 1)[0][:200]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
