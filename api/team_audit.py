from agent import AgentContext
from helpers import login, projects, team_access
from helpers.api import ApiHandler, Request, Response, session
from helpers.team_store import get_store


def _filters(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Expected audit filters.")
    filters = {}
    for name in ("account_id", "project_id", "context_id", "action"):
        if name not in data or data[name] == "":
            continue
        value = data[name]
        if not isinstance(value, str) or not 1 <= len(value) <= 128:
            raise ValueError("Invalid audit filter.")
        filters[name] = value
    for name in ("from", "until", "before_id"):
        if name not in data:
            continue
        value = data[name]
        if type(value) is not int or not 0 <= value < 2**63:
            raise ValueError("Invalid audit date or cursor.")
        filters[name] = value
    if filters.get("from", 0) > filters.get("until", 2**63):
        raise ValueError("The start time must come before the end time.")
    return filters


class TeamAudit(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not login.team_mode_enabled():
            return Response("Audit access denied.", 403)
        scope = team_access.request_scope()
        admin = scope is None and login.is_admin_session(session)
        actor_id = "admin" if admin else scope.account_id if scope else ""
        if not actor_id:
            return Response("Audit access denied.", 403)
        if not isinstance(input, dict):
            return Response("Expected audit parameters.", 400)
        store = get_store()
        action = input.get("action")
        try:
            if action == "grant":
                if not admin:
                    return Response("Audit access denied.", 403)
                name, recipient = input.get("project"), input.get("recipient")
                project_id = team_access.bound_project_id(name) if isinstance(name, str) else None
                if not project_id or not isinstance(recipient, str):
                    return Response("Choose a managed project and an account.", 400)
                store.set_audit_grant(recipient, project_id, input.get("permission"))
                return {"ok": True}
            if action == "transcript":
                return self.transcript(actor_id, scope, input)
            grants = store.audit_grants(None if admin else actor_id)
            if scope is not None:
                grants = [grant for grant in grants if scope.project_ids.get(grant["name"]) == grant["project_id"]]
            if action == "options":
                project_rows = store.audit_projects() if admin else [
                    {"id": grant["project_id"], "name": grant["name"], "retired": False} for grant in grants
                ]
                account_rows = store.list_accounts() if admin else store.audit_project_accounts([row["id"] for row in project_rows])
                accounts = [{"id": account.id, "username": account.username} for account in account_rows]
                return {"ok": True, "projects": project_rows, "accounts": accounts, "grants": grants, "admin": admin}
            if action == "events":
                project_ids = None if admin else [grant["project_id"] for grant in grants]
                if project_ids == []:
                    return Response("Audit access denied.", 403)
                return {"ok": True, **store.audit_events(actor_id, _filters(input.get("filters", {})), project_ids)}
        except ValueError as error:
            return Response(str(error), 400)
        return Response("Unknown audit action.", 400)

    def transcript(self, actor_id: str, scope: team_access.MemberScope | None, input: dict) -> dict | Response:
        context_id = input.get("context")
        context = AgentContext.get(context_id) if isinstance(context_id, str) else None
        if context is None or not team_access.is_team_chat(context) or (scope is not None and not scope.permits_chat(context)):
            return Response("Transcript access denied.", 403)
        name = projects.get_context_project_name(context)
        project_id = context.get_data(team_access.CHAT_PROJECT_ID)
        if not name or team_access.bound_project_id(name) != project_id:
            return Response("Transcript access denied.", 403)
        end = input.get("before_no", 2**63 - 1)
        if type(end) is not int or not 0 <= end < 2**63:
            return Response("Invalid transcript cursor.", 400)
        if not get_store().authorize_transcript(actor_id, project_id, context.id):
            return Response("Transcript access denied.", 403)
        rows = sorted(
            (entry for entry in context.log.output().items if entry["type"] in ("user", "response") and entry["no"] < end),
            key=lambda entry: entry["no"],
        )
        messages = [
            {field: entry[field] for field in ("no", "type", "heading", "content", "timestamp")}
            for entry in rows[-30:]
        ]
        return {"ok": True, "context": context.id, "project": name, "messages": messages,
                "before_no": messages[0]["no"] if len(rows) > 30 else None}
