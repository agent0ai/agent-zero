from helpers.api import ApiHandler, Request, Response

from helpers import runtime
from helpers import self_update


class SelfUpdateSchedule(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not runtime.is_dockerized():
            return {
                "success": False,
                "error": "Self-update is only available in dockerized installations.",
            }

        try:
            pending = self_update.schedule_update(
                branch=str(input.get("branch", "")),
                tag=str(input.get("tag", "")),
                backup_usr=bool(input.get("backup_usr", True)),
                backup_path=str(input.get("backup_path", "")),
                backup_name=str(input.get("backup_name", "")),
                backup_conflict_policy=str(input.get("backup_conflict_policy", "rename")),
            )
            return {
                "success": True,
                "pending": pending,
                "message": (
                    "Self-update was scheduled. Restart Agent Zero to apply the requested branch/tag."
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
