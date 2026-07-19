from __future__ import annotations

from helpers.api import ApiHandler, Request, Response

from plugins._commands.helpers import commands as commands_helper


class Commands(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "") or "").strip()

        if action == "list_effective":
            return self._list_effective(input)
        if action == "list_scope":
            return self._list_scope(input)
        if action == "get":
            return self._get(input)
        if action == "save":
            return self._save(input)
        if action == "delete":
            return self._delete(input)
        if action == "duplicate":
            return self._duplicate(input)
        if action == "scope_info":
            return self._scope_info(input)
        if action == "resolve":
            return await self._resolve(input)

        return Response(status=400, response=f"Unknown action: {action}")

    def _list_effective(self, input: dict) -> dict | Response:
        context_scope = commands_helper.get_context_scope(str(input.get("context_id", "") or ""))
        commands, scope = commands_helper.list_effective_commands(
            project_name=context_scope["project_name"],
        )
        commands = [
            command
            for command in commands
            if not command.get("frontmatter_extra", {}).get("webui_hidden")
        ]
        return {
            "ok": True,
            "commands": commands,
            "scope": scope,
        }

    def _list_scope(self, input: dict) -> dict | Response:
        commands, scope = commands_helper.list_scope_commands(
            project_name=str(input.get("project_name", "") or ""),
        )
        return {
            "ok": True,
            "commands": commands,
            "builtin_commands": commands_helper.list_builtin_commands(),
            "scope": scope,
        }

    def _get(self, input: dict) -> dict | Response:
        path = str(input.get("path", "") or "")
        if not path:
            return Response(status=400, response="Missing path")

        try:
            command = commands_helper.get_command(
                path,
                project_name=str(input.get("project_name", "") or ""),
            )
        except FileNotFoundError:
            return Response(status=404, response="Command not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return {"ok": True, "command": command}

    def _save(self, input: dict) -> dict | Response:
        try:
            command = commands_helper.save_command(
                project_name=str(input.get("project_name", "") or ""),
                existing_path=str(input.get("existing_path", "") or ""),
                name=str(input.get("name", "") or ""),
                description=str(input.get("description", "") or ""),
                argument_hint=str(input.get("argument_hint", "") or ""),
                command_type=str(input.get("command_type", "text") or "text"),
                body=str(input.get("body", "") or ""),
                include_history=bool(input.get("include_history", False)),
                extra_frontmatter=input.get("extra_frontmatter", {}) or {},
            )
        except FileExistsError as error:
            return Response(status=409, response=str(error))
        except ValueError as error:
            return Response(status=400, response=str(error))

        return {"ok": True, "command": command}

    def _delete(self, input: dict) -> dict | Response:
        path = str(input.get("path", "") or "")
        if not path:
            return Response(status=400, response="Missing path")

        try:
            commands_helper.delete_command(
                path,
                project_name=str(input.get("project_name", "") or ""),
            )
        except FileNotFoundError:
            return Response(status=404, response="Command not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return {"ok": True}

    def _duplicate(self, input: dict) -> dict | Response:
        path = str(input.get("path", "") or "")
        if not path:
            return Response(status=400, response="Missing path")

        try:
            command = commands_helper.duplicate_command(
                path,
                project_name=str(input.get("project_name", "") or ""),
            )
        except FileNotFoundError:
            return Response(status=404, response="Command not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return {"ok": True, "command": command}

    def _scope_info(self, input: dict) -> dict | Response:
        explicit_project = str(input.get("project_name", "") or "")
        context_scope = commands_helper.get_context_scope(str(input.get("context_id", "") or ""))

        project_name = explicit_project if "project_name" in input else context_scope["project_name"]

        scope = commands_helper.get_scope_payload(
            project_name=project_name,
            ensure_directory=bool(input.get("ensure_directory", False)),
        )
        return {
            "ok": True,
            "scope": commands_helper.strip_private_scope(scope),
            "context_scope": context_scope,
        }

    async def _resolve(self, input: dict) -> dict | Response:
        path = str(input.get("path", "") or "")
        if not path:
            return Response(status=400, response="Missing path")

        slash_text = str(input.get("slash_text", "") or "")
        if not slash_text:
            return Response(status=400, response="Missing slash_text")

        try:
            resolution = await commands_helper.resolve_command_invocation(
                path=path,
                slash_text=slash_text,
                project_name=str(input.get("project_name", "") or ""),
                context_id=str(input.get("context_id", "") or ""),
            )
        except FileNotFoundError:
            return Response(status=404, response="Command not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return {"ok": True, "resolution": resolution}
