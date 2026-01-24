from python.helpers.api import ApiHandler
from flask import Request, Response
from agent import AgentContext


class NotificationsHistory(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        # Get the global notification manager
        notification_manager = AgentContext.get_notification_manager()

        # Return all notifications for history modal
        notifications = notification_manager.output_all()
        return {
            "notifications": notifications,
            "guid": notification_manager.guid,
            "count": len(notifications),
        }
