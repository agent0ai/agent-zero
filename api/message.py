from agent import AgentContext, UserMessage
from helpers.api import ApiHandler, Request, Response

from helpers import files, extension, message_queue as mq, persist_chat, projects, skills, team_access, team_projects, team_runs
from helpers.file_browser import FileBrowser
from helpers.file_transfers import copy_stream
import os
import re
from uuid import uuid4
from helpers.security import safe_filename
from helpers.defer import DeferredTask
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_store import ActiveRunConflict, get_store as team_store


class Message(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = request.form.get("context") if request.mimetype == "multipart/form-data" else input.get("context")
        context = AgentContext.get(context_id) if isinstance(context_id, str) and context_id else None
        if team_access.request_scope() is not None or team_access.is_team_chat(context):
            return await self._process_team(input, request, context)
        try:
            task, context = await self.communicate(input=input, request=request)
        except PermissionError:
            return Response("Retry sending through the project chat.", 409)
        return await self.respond(task, context)

    async def _process_team(self, input: dict, request: Request, context: AgentContext | None):
        multipart = request.mimetype == "multipart/form-data"
        if multipart:
            input = request.form.to_dict()
        elif not request.is_json or not isinstance(input, dict):
            return Response("Send a message as JSON or with project attachments.", 415)
        text = input.get("text", "")
        message_id = input.get("message_id")
        uploads = request.files.getlist("attachments") if multipart else []
        if not isinstance(text, str) or not (text.strip() or uploads):
            return Response("Send text or attach a file.", 400)
        if message_id is not None and (not isinstance(message_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", message_id)):
            return Response("Invalid message ID.", 400)
        scope = team_access.request_chat_scope(context) if context else None
        if context is None or scope is None or not team_access.can_send(scope, context):
            return Response("Chat access denied.", 403)

        upload_items = []
        fingerprints = []
        remaining = FileBrowser.max_file_bytes() if uploads else 0
        try:
            for storage in uploads:
                parts = team_projects.file_parts(storage.filename)
                if any(parts == item[0] for item in upload_items):
                    raise ValueError("Attachment paths must be unique.")
                receipt = copy_stream(storage.stream, None, remaining)
                remaining -= receipt["size"]
                storage.stream.seek(0)
                upload_items.append((parts, storage))
                fingerprints.append((parts, receipt["sha256"]))
        except (ValueError, OSError) as error:
            return Response(str(error), 400)
        data = await self._prepare_message(context, text, [])
        if data.get("model_not_configured"):
            return await self.respond(None, context)

        message_id = message_id or uuid4().hex
        with self.thread_lock:
            current_scope = team_access.request_chat_scope(context)
            if AgentContext.get(context.id) is not context or current_scope is None or not team_access.can_send(current_scope, context):
                return Response("Chat access denied.", 403)
            try:
                fingerprint = repr((text, fingerprints)) if fingerprints else text
                run, created = team_runs.reserve(context, current_scope.account_id, message_id, fingerprint)
            except ActiveRunConflict as error:
                return Response(str(error), 409)
            except PermissionError:
                return Response("Chat access denied.", 403)
            except ValueError as error:
                return Response(str(error), 409)
            if not created:
                return {"context": context.id, "run_id": run.id, "actor": run.username, "state": run.state, "replayed": True}

            if context.is_running():
                team_store().finish_run(run, "failed")
                return Response("The previous run is still finishing.", 409)
            try:
                if upload_items:
                    name = projects.get_context_project_name(context)
                    with team_projects.project_lock(name, current_scope):
                        data["project_attachments"] = team_projects.save_chat_attachments(name, run.id, upload_items)
                    data["attachment_paths"] = [
                        files.normalize_a0_path(files.get_abs_path(projects.get_project_folder(name), item["path"]))
                        for item in data["project_attachments"]
                    ]
                with team_runs.authorized_dispatch(run):
                    task = self._dispatch_message(context, data, message_id, author=run.username)
            except PermissionError:
                team_store().finish_run(run, "failed")
                return Response("Project file access denied.", 403)
            except OSError as error:
                team_store().finish_run(run, "failed")
                message, status = team_projects.safe_file_error(error)
                return Response(message, status)
            except BaseException:
                team_store().finish_run(run, "failed")
                raise

        mark_dirty_all(reason="team run accepted")
        response = await self.respond(task, context)
        return {**response, "run_id": run.id, "actor": run.username}

    async def respond(self, task: DeferredTask, context: AgentContext):
        if task is None:
            return {
                "message": "Model not configured.",
                "model_not_configured": True,
                "context": context.id,
            }
        result = await task.result()  # type: ignore
        return {
            "message": result,
            "context": context.id,
        }

    async def communicate(self, input: dict, request: Request):
        # Handle both JSON and multipart/form-data
        if request.content_type.startswith("multipart/form-data"):
            text = request.form.get("text", "")
            ctxid = request.form.get("context", "")
            message_id = request.form.get("message_id", None)
            attachments = request.files.getlist("attachments")
            attachment_paths = []

            upload_folder_int = "/a0/usr/uploads"
            upload_folder_ext = files.get_abs_path("usr/uploads") # for development environment

            if attachments:
                os.makedirs(upload_folder_ext, exist_ok=True)
                for attachment in attachments:
                    if attachment.filename is None:
                        continue
                    filename = safe_filename(attachment.filename)
                    if not filename:
                        continue
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

        # Obtain agent context
        context = self.use_context(ctxid)
        data = await self._prepare_message(context, text, attachment_paths)
        with self.thread_lock:
            if team_access.is_team_chat(context):
                raise PermissionError("Shared chat requires a member session.")
            return self._dispatch_message(context, data, message_id), context

    async def _prepare_message(self, context, message, attachment_paths):
        data = {"message": message, "attachment_paths": attachment_paths}
        await extension.call_extensions_async("user_message_ui", agent=context.get_agent(), data=data)
        return data

    def _dispatch_message(self, context, data, message_id, *, author=""):
        if data.get("model_not_configured"):
            return None
        message = data.get("message", "")
        attachment_paths = data.get("attachment_paths", [])
        if author:
            goal_command = re.fullmatch(r"\s*/goal\s+(\S[\s\S]*)", message)
            if goal_command:
                from plugins._goal.tools.goal import create_goal

                message = goal_command.group(1).strip()
                if message.lower() == "auto":
                    message = "Create and manage a goal for my current request if one is present."
                else:
                    create_goal(context.id, message, created_by="user")
            if "@[skill/" in message:
                skills.load_project_reference_skills(context.agent0, message)
            mq.log_user_message(context, message, attachment_paths, message_id, author=author,
                                project_attachments=data.get("project_attachments"))
            context.data.pop(team_access.CHAT_DRAFT_AT, None)
            context.set_data(team_access.CHAT_STARTED, True)
            persist_chat.save_tmp_chat(context)
        else:
            mq.log_user_message(context, message, attachment_paths, message_id)
        return context.communicate(UserMessage(message=message, attachments=attachment_paths, id=message_id or ""))
