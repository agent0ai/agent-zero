from helpers.api import ApiHandler, Request, session
from helpers import login


class ApiLogout(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        login.clear_session(session)
        if login.team_mode_enabled():
            from helpers.state_monitor_integration import mark_dirty_all

            mark_dirty_all(reason="team logout")
        return {"ok": True}
