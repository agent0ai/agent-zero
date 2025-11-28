from python.helpers.api import ApiHandler, Request, Response
from python.helpers import dotenv
from python.helpers.print_style import PrintStyle


class InitTimezone(ApiHandler):
    """
    Initialize timezone in .env if not already set.
    This should only be called once when the user first connects.
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        timezone = input.get("timezone", "UTC")
        offset_minutes = input.get("offset_minutes", 0)

        # Check if timezone is already set in .env
        existing_timezone = dotenv.get_dotenv_value("DEFAULT_USER_TIMEZONE")

        if existing_timezone is None or existing_timezone == "":
            # Save timezone to .env
            dotenv.save_dotenv_value("DEFAULT_USER_TIMEZONE", timezone)
            dotenv.save_dotenv_value(
                "DEFAULT_USER_UTC_OFFSET_MINUTES", str(offset_minutes)
            )

            PrintStyle.hint(
                f"Initialized timezone to {timezone} (UTC{offset_minutes/60:+.1f})"
            )

            return {
                "success": True,
                "message": "Timezone initialized",
                "timezone": timezone,
                "offset_minutes": offset_minutes,
            }
        else:
            # Timezone already set, don't override
            PrintStyle.debug(
                f"Timezone already set to {existing_timezone}, skipping initialization"
            )

            existing_offset = dotenv.get_dotenv_value(
                "DEFAULT_USER_UTC_OFFSET_MINUTES", "0"
            )
            try:
                existing_offset_int = int(existing_offset)
            except (ValueError, TypeError):
                existing_offset_int = 0

            return {
                "success": False,
                "message": "Timezone already set",
                "timezone": existing_timezone,
                "offset_minutes": existing_offset_int,
            }
