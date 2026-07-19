from helpers import notification
from helpers.extension import Extension
from agent import LoopData
from helpers import files, settings, update_check
import datetime
import json


# check for newer versions of A0 available and send notification
# check after user message is sent from UI, not API, MCP etc. (user is active and can see the notification)
# do not check too often, use cooldown
# do not notify too often

last_check = datetime.datetime.fromtimestamp(0)
check_cooldown_seconds = 60
last_notification_id = None
last_notification_time = datetime.datetime.fromtimestamp(0)
notification_cooldown_seconds = 60 * 60 * 24
notification_state_file = "usr/update-check-state.json"


def _load_notification_state() -> dict:
    try:
        return json.loads(files.read_file(notification_state_file))
    except Exception:
        return {}


def _parse_timestamp(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo:
        return parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return parsed


def _remember_notification(notif: dict, now: datetime.datetime):
    state = {
        "last_notification_at": now.replace(tzinfo=datetime.timezone.utc).isoformat(),
        "last_notification_id": notif.get("id") or "",
        "last_notification_group": notif.get("group", "update_check"),
    }
    files.write_file(notification_state_file, json.dumps(state, indent=2))


class UpdateCheck(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), text: str = "", **kwargs):
        if not self.agent:
            return

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
                now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                stored_state = _load_notification_state()
                stored_notification_time = _parse_timestamp(stored_state.get("last_notification_at"))
                effective_notification_time = stored_notification_time or last_notification_time

                if (now - effective_notification_time).total_seconds() > notification_cooldown_seconds:
                    last_notification_id = notif.get("id")
                    last_notification_time = now
                    try:
                        _remember_notification(notif, now)
                    except Exception:
                        pass
                    self.send_notification(notif)
        except Exception as e:
            pass # no need to log if the update server is inaccessible


    def send_notification(self, notif):
        if not self.agent:
            return

        notifs = self.agent.context.get_notification_manager()
        notifs.send_notification(
            title=notif.get("title", "Newer version available"),
            message=notif.get("message", "A newer version of Agent Zero is available. Please update to the latest version."),
            type=notif.get("type", "info"),
            detail=notif.get("detail", ""),
            display_time=notif.get("display_time", 10),
            group=notif.get("group", "update_check"),
            priority=notif.get("priority", notification.NotificationPriority.NORMAL),
            id=notif.get("id", "update_check_available"),
        )
