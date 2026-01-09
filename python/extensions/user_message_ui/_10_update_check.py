from python.helpers import notification
from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import settings, update_check
import datetime


# check for newer versions of A0 available and send notification
# check after user message is sent from UI, not API, MCP etc. (user is active and can see the notification)
# do not check too often, use cooldown
# do not notify too often unless there's a different notification

last_check = datetime.datetime.fromtimestamp(0)
check_cooldown_seconds = 60
last_notification_id = ""
last_notification_time = datetime.datetime.fromtimestamp(0)
notification_cooldown_seconds = 60 * 60 * 24

class UpdateCheck(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), text: str = "", **kwargs):
        try:
            global last_check, last_notification_id, last_notification_time
            
            # first check if update check is enabled
            current_settings = settings.get_settings()
            if not current_settings["update_check_enabled"]:
                return
            
            # check if cooldown has passed
            if (datetime.datetime.now() - last_check).total_seconds() < check_cooldown_seconds:
                return
            last_check = datetime.datetime.now()
            
            # check for updates
            version = await update_check.check_version()

            # if the user should update, send notification
            if notif := version.get("notification"):
                if notif.get("id") != last_notification_id or (datetime.datetime.now() - last_notification_time).total_seconds() > notification_cooldown_seconds:
                    last_notification_id = notif.get("id")
                    last_notification_time = datetime.datetime.now()
                    self.send_notification(notif)
        except Exception as e:
            pass # no need to log if the update server is inaccessible


    def send_notification(self, notif):
        notifs = self.agent.context.get_notification_manager()
        notifs.send_notification(
            title=notif.get("title", "Newer version available"),
            message=notif.get("message", "A newer version of Agent Zero is available. Please update to the latest version."),
            type=notif.get("type", "info"),
            detail=notif.get("detail", ""),
            display_time=notif.get("display_time", 10),
            group=notif.get("group", "update_check"),
            priority=notif.get("priority", notification.NotificationPriority.NORMAL),
        )
