import asyncio
import contextlib
import os
import shutil
import threading
import time

from werkzeug.utils import secure_filename

import models
from agent import AgentContext, UserMessage
from python.helpers import extension, files, perf_metrics, settings
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.defer import DeferredTask
from python.helpers.print_style import PrintStyle
from python.helpers.strings import redact_sensitive_tokens


class Message(ApiHandler):
    @staticmethod
    def _provider_requires_api_key(provider: str) -> bool:
        # Local providers generally do not require cloud API keys.
        return provider.lower() not in {"ollama", "huggingface", "local", "lmstudio"}

    @staticmethod
    def _is_missing_key(value: str | None) -> bool:
        token = (value or "").strip()
        return token in {"", "None", "NA"}

    async def _return_text(self, text: str) -> str:
        return text

    def _resolve_external_executable(self, backend: str) -> str:
        """Resolve CLI executable for external chat backends."""
        candidates: list[str] = []
        if backend == "claude_code":
            env_path = os.getenv("CLAUDE_CLI_PATH", "").strip()
            if env_path:
                candidates.append(env_path)
            candidates.extend(
                [
                    "claude",
                    "claude-code",
                    os.path.expanduser("~/dev/tools/claude-code/bin/claude"),
                ]
            )
        elif backend == "codex":
            env_path = os.getenv("CODEX_CLI_PATH", "").strip()
            if env_path:
                candidates.append(env_path)
            candidates.extend(
                [
                    "codex",
                    "codex-cli",
                    os.path.expanduser("~/dev/tools/claude-code/bin/codex"),
                ]
            )
        else:
            raise RuntimeError(f"Unsupported external backend: {backend}")

        for candidate in candidates:
            if os.path.isabs(candidate) and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        hint_var = "CLAUDE_CLI_PATH" if backend == "claude_code" else "CODEX_CLI_PATH"
        raise RuntimeError(
            f"{backend} CLI is not installed or not in PATH. " f"Install it, or set {hint_var} to the executable path."
        )

    async def process(self, input: dict, request: Request) -> dict | Response:
        started = time.perf_counter()
        status = "success"
        perf_metrics.increment("runtime.message.requests")
        try:
            task, context, timeout, dispatch = await self.communicate(input=input, request=request)
            if dispatch.get("queued"):
                return {
                    "message": "Message queued.",
                    "context": context.id,
                    "accepted": bool(dispatch.get("accepted", True)),
                    "queued": True,
                    "queue_position": int(dispatch.get("queue_position", 0) or 0),
                    "queue_depth": int(dispatch.get("queue_depth", 0) or 0),
                    "state": str(dispatch.get("state", "running")),
                }
            if dispatch.get("accepted") is False:
                return {
                    "message": "Queue is full. Message rejected by policy.",
                    "context": context.id,
                    "accepted": False,
                    "queued": False,
                    "queue_position": 0,
                    "queue_depth": int(dispatch.get("queue_depth", 0) or 0),
                    "state": str(dispatch.get("state", "running")),
                }
            cfg = settings.get_settings()
            wait_timeout = int(cfg.get("chat_response_wait_timeout_seconds", max(timeout, 90)) or max(timeout, 90))
            return await self.respond(task, context, wait_timeout)
        except Exception:
            status = "error"
            perf_metrics.increment("runtime.message.errors")
            raise
        finally:
            perf_metrics.observe_ms(
                "runtime.message.duration_ms",
                (time.perf_counter() - started) * 1000.0,
                status=status,
            )

    async def respond(self, task: DeferredTask, context: AgentContext, timeout_seconds: int):
        try:
            result = await task.result(timeout=max(1, timeout_seconds))  # type: ignore
            return {
                "message": result,
                "context": context.id,
            }
        except TimeoutError:
            with contextlib.suppress(Exception):
                context.kill_process()
            warning = (
                f"Request timed out after {timeout_seconds}s while waiting for model response. "
                "Please retry, switch to a faster/local model, or reduce enabled tools."
            )
            context.log.log(
                type="warning",
                heading="chat timeout",
                content=warning,
            )
            return {
                "message": warning,
                "context": context.id,
                "timed_out": True,
            }
        except Exception as e:
            error_text = f"Chat execution failed: {e}"
            context.log.log(
                type="error",
                heading="chat execution failed",
                content=error_text,
            )
            return {
                "message": error_text,
                "context": context.id,
                "error": True,
            }

    def _schedule_background_timeout_watchdog(self, task: DeferredTask, context: AgentContext, timeout_seconds: int):
        if timeout_seconds <= 0:
            return

        context_id = context.id
        scheduled_future = getattr(task, "_future", None)

        def _enforce_timeout():
            try:
                # DeferredTask instances are reused across requests.
                # Ensure this watchdog only applies to the exact scheduled future.
                current_future = getattr(task, "_future", None)
                if current_future is None or current_future is not scheduled_future:
                    return
                if current_future.done():
                    return
                task.kill()
                ctx = AgentContext.get(context_id)
                if ctx:
                    msg = f"Background chat task exceeded {timeout_seconds}s and was terminated to keep the system responsive."
                    ctx.log.log(
                        type="warning",
                        heading="chat background timeout",
                        content=msg,
                        temp=True,
                    )
            except Exception:
                # Fail-open: watchdog must never crash runtime.
                pass

        timer = threading.Timer(timeout_seconds, _enforce_timeout)
        timer.daemon = True
        timer.start()

    async def communicate(self, input: dict, request: Request):
        comm_started = time.perf_counter()
        comm_status = "success"
        try:
            # Handle both JSON and multipart/form-data
            if request.content_type.startswith("multipart/form-data"):
                text = request.form.get("text", "")
                ctxid = request.form.get("context", "")
                message_id = request.form.get("message_id", None)
                attachments = request.files.getlist("attachments")
                attachment_paths = []

                upload_folder_int = "/a0/tmp/uploads"
                upload_folder_ext = files.get_abs_path("tmp/uploads")  # for development environment

                if attachments:
                    os.makedirs(upload_folder_ext, exist_ok=True)
                    for attachment in attachments:
                        if attachment.filename is None:
                            continue
                        filename = secure_filename(attachment.filename)
                        save_path = files.get_abs_path(upload_folder_ext, filename)
                        attachment.save(save_path)
                        attachment_paths.append(os.path.join(upload_folder_int, filename))
            else:
                # Handle JSON request as before
                input_data = request.get_json()
                text = input_data.get("text", "")
                ctxid = input_data.get("context", "")
                message_id = input_data.get("message_id", None)
                attachment_paths = []

            # Now process the message
            message = text

            # Obtain agent context
            context = self.use_context(ctxid)

            # call extension point, alow it to modify data
            data = {"message": message, "attachment_paths": attachment_paths}
            await extension.call_extensions("user_message_ui", agent=context.get_agent(), data=data)
            message = data.get("message", "")
            attachment_paths = data.get("attachment_paths", [])

            # Prepare attachment filenames for logging
            attachment_filenames = [os.path.basename(path) for path in attachment_paths] if attachment_paths else []

            # Print to console and log
            safe_console_message = redact_sensitive_tokens(message)
            PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print("User message:")
            PrintStyle(font_color="white", padding=False).print(f"> {safe_console_message}")
            if attachment_filenames:
                PrintStyle(font_color="white", padding=False).print("Attachments:")
                for filename in attachment_filenames:
                    PrintStyle(font_color="white", padding=False).print(f"- {filename}")

            # Log the message with message_id and attachments.
            # Temporary fail-open path: disable synchronous log writes when requested
            # to prevent chat stalls in constrained environments.
            if os.getenv("A0_DISABLE_CHAT_LOG", "1").strip().lower() not in {"1", "true", "yes", "on"}:
                context.log.log(
                    type="user",
                    heading="User message",
                    content=message,
                    kvps={"attachments": attachment_filenames},
                    id=message_id,
                )
            cfg = settings.get_settings()
            backend = str(cfg.get("chat_execution_backend", "native") or "native").strip().lower()
            timeout = int(cfg.get("chat_execution_timeout_seconds", 120) or 120)
            stale_intervention_seconds = int(cfg.get("chat_stale_intervention_seconds", 45) or 45)
            user_msg = UserMessage(message, attachment_paths)
            chat_provider = str(cfg.get("chat_model_provider", "") or "").strip().lower()

            # Fail fast when configured cloud provider has no API key.
            if self._provider_requires_api_key(chat_provider):
                provider_key = ""
                api_keys = cfg.get("api_keys", {}) or {}
                if isinstance(api_keys, dict):
                    provider_key = str(api_keys.get(chat_provider, "") or "").strip()
                resolved_key = provider_key or str(models.get_api_key(chat_provider) or "").strip()
                if self._is_missing_key(resolved_key):
                    guidance = (
                        f"Chat provider '{chat_provider}' has no API key configured. "
                        "Open Settings > API Keys and set the key, or switch chat model provider "
                        "to a local option like Ollama."
                    )
                    context.log.log(
                        type="warning",
                        heading="chat configuration missing API key",
                        content=guidance,
                    )
                    raise RuntimeError(guidance)

            if backend in {"claude_code", "codex"}:
                task = context.run_task(
                    self._external_chat_with_fallback,
                    context,
                    user_msg,
                    backend,
                    timeout,
                )
                self._schedule_background_timeout_watchdog(task, context, max(timeout + 5, 35))
                return (
                    task,
                    context,
                    timeout,
                    {
                        "accepted": True,
                        "queued": False,
                        "queue_position": 0,
                        "queue_depth": 0,
                        "state": "running",
                    },
                )

            # Native runtime can still stall in constrained environments.
            # Reuse chat_execution_timeout_seconds as an upper bound for synchronous API response.
            active_task = getattr(context, "task", None)
            new_message_policy = (
                str(cfg.get("chat_new_message_policy", "queue_strict") or "queue_strict").strip().lower()
            )
            if active_task and active_task.is_alive() and new_message_policy != "queue_strict":
                age = 0.0
                if hasattr(active_task, "age_seconds"):
                    with contextlib.suppress(Exception):
                        age = float(active_task.age_seconds())
                if age >= float(stale_intervention_seconds):
                    with contextlib.suppress(Exception):
                        active_task.kill()
                    context.log.log(
                        type="warning",
                        heading="stale chat task reset",
                        content=(
                            f"Previous chat run was active for {int(age)}s. " "Resetting it so the new message can run."
                        ),
                        temp=True,
                    )

            pause_behavior = str(cfg.get("chat_pause_behavior", "buffer_context") or "buffer_context").strip().lower()
            queue_max_depth = int(cfg.get("chat_queue_max_depth", 10) or 10)
            queue_drop_policy = str(cfg.get("chat_queue_drop_policy", "reject_new") or "reject_new").strip().lower()
            effective_policy = new_message_policy
            if context.paused and pause_behavior == "interrupt":
                effective_policy = "interrupt"

            task = context.communicate_with_policy(
                user_msg,
                policy=effective_policy,
                queue_max_depth=max(0, queue_max_depth),
                queue_drop_policy=queue_drop_policy,
            )
            dispatch = context.get_dispatch_status()

            if dispatch.get("queued"):
                context.log.log(
                    type="info",
                    heading="message queued",
                    content=(
                        f"Message queued at position {dispatch.get('queue_position', 0)} "
                        f"(depth={dispatch.get('queue_depth', 0)})."
                    ),
                    temp=True,
                )
            bg_timeout = int(
                cfg.get("chat_background_timeout_seconds", max(timeout * 10, 300)) or max(timeout * 10, 300)
            )
            self._schedule_background_timeout_watchdog(task, context, bg_timeout)
            return task, context, timeout, dispatch
        except Exception:
            comm_status = "error"
            raise
        finally:
            perf_metrics.observe_ms(
                "runtime.message.communicate_ms",
                (time.perf_counter() - comm_started) * 1000.0,
                status=comm_status,
            )

    async def _external_chat_with_fallback(
        self,
        context: AgentContext,
        user_msg: UserMessage,
        backend: str,
        timeout_seconds: int,
    ):
        try:
            output = await self._run_external_chat(user_msg, backend, timeout_seconds)
            agent = context.get_agent()
            agent.hist_add_user_message(user_msg)
            agent.hist_add_ai_response(output)
            context.log.log(
                type="response",
                heading=f"{backend} response",
                content=output,
                kvps={"backend": backend, "finished": True},
            )
            return output
        except Exception as e:
            cfg = settings.get_settings()
            cloud_fallback_enabled = bool(cfg.get("llm_cloud_fallback_enabled", False))
            if not cloud_fallback_enabled:
                message = f"{backend} failed and cloud fallback is disabled. " f"Error: {e}"
                context.log.log(
                    type="error",
                    heading=f"{backend} failed",
                    content=message,
                )
                return message

            context.log.log(
                type="warning",
                heading=f"{backend} failed, falling back",
                content=str(e),
            )
            # Optional fallback to native Agent Jumbo runtime.
            return await context._process_chain(context.get_agent(), user_msg, True)

    async def _run_external_chat(
        self,
        user_msg: UserMessage,
        backend: str,
        timeout_seconds: int,
    ) -> str:
        started = time.perf_counter()
        status = "success"
        prompt_started = time.perf_counter()
        prompt = user_msg.message or ""
        if user_msg.attachments:
            prompt += (
                "\n\nAttachments were provided in UI, but external CLI backends do not "
                "automatically ingest them. Continue without direct attachment access."
            )
        perf_metrics.observe_ms("runtime.prompt_build.duration_ms", (time.perf_counter() - prompt_started) * 1000.0)

        executable = self._resolve_external_executable(backend)
        if backend == "claude_code":
            cmd = [executable, "-p", prompt, "--output-format", "text"]
        elif backend == "codex":
            cmd = [
                executable,
                "exec",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--color",
                "never",
                prompt,
            ]
        else:
            raise RuntimeError(f"Unsupported external backend: {backend}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                f"{backend} executable not found ({e.filename}). "
                "Switch backend to Native, or configure the CLI path."
            ) from e
        try:
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                raise RuntimeError(f"{backend} timed out after {timeout_seconds}s")

            out = (stdout or b"").decode(errors="replace").strip()
            err = (stderr or b"").decode(errors="replace").strip()
            if process.returncode != 0:
                raise RuntimeError(err or out or f"{backend} exited with code {process.returncode}")
            if not out:
                raise RuntimeError(f"{backend} returned empty output")
            return out
        except Exception:
            status = "error"
            raise
        finally:
            perf_metrics.observe_ms(
                "runtime.external_chat.duration_ms",
                (time.perf_counter() - started) * 1000.0,
                status=status,
            )
