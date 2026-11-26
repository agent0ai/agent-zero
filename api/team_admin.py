from dataclasses import asdict

from helpers import dotenv, login, projects, team_access
from helpers.api import ApiHandler, Request, Response, session
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_store import get_store, normalize_username


def _string(input: dict, name: str) -> str:
    value = input.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} is required.")
    return value


def _boolean(input: dict, name: str) -> bool:
    value = input.get(name)
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false.")
    return value


class TeamAdmin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not login.team_mode_enabled() or not login.is_admin_session(session):
            return Response("Team administration is forbidden.", 403)
        if not isinstance(input, dict):
            return Response("Expected a JSON object.", 400)

        action = input.get("action")
        store = get_store()
        if action == "list":
            accounts = [
                {
                    **asdict(account),
                    "projects": sorted(team_access.assigned_projects(account.id, include_disabled=True)),
                }
                for account in store.list_accounts()
            ]
            return {"ok": True, "accounts": accounts, "projects": projects.get_active_projects_list()}
        try:
            if action == "create":
                username = normalize_username(_string(input, "username"))
                admin_username = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN)
                if username == admin_username.strip().lower():
                    raise ValueError("That username is reserved for the administrator.")
                account = store.create_account(username, _string(input, "password"), actor_id="admin")
                return {"ok": True, "account": asdict(account)}
            if action == "set_enabled":
                store.set_account_enabled(_string(input, "account_id"), _boolean(input, "enabled"), actor_id="admin")
            elif action == "reset_password":
                store.reset_password(_string(input, "account_id"), _string(input, "password"), actor_id="admin")
            elif action == "set_membership":
                with self.thread_lock:
                    team_access.set_project_membership(
                        _string(input, "account_id"), _string(input, "project"), _boolean(input, "granted"), actor_id="admin",
                    )
            else:
                raise ValueError("Unknown team administration action.")
        except ValueError as error:
            return Response(str(error), 400)

        mark_dirty_all(reason="team authorization changed")
        return {"ok": True}
