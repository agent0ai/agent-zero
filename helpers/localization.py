from datetime import datetime, timezone as dt_timezone
import os
import time
import pytz  # type: ignore

from helpers.print_style import PrintStyle
from helpers.dotenv import get_dotenv_value, save_dotenv_value



class Localization:
    """
    Localization class for handling timezone conversions around the user's IANA
    timezone. UTC is still used when an external protocol requires an absolute
    instant, but user-facing timestamps are formatted in the configured timezone.
    """

    # singleton
    _instance = None

    @classmethod
    def get(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, timezone: str | None = None):
        self.timezone: str = "UTC"
        self._offset_minutes: int = 0
        self._last_timezone_change: datetime | None = None
        # Load persisted values if available.
        persisted_tz = str(get_dotenv_value("DEFAULT_USER_TIMEZONE", os.environ.get("TZ") or "UTC"))
        persisted_offset = get_dotenv_value("DEFAULT_USER_UTC_OFFSET_MINUTES", None)
        if timezone is not None:
            # Explicit override
            self.set_timezone(timezone)
        else:
            # Initialize from persisted values
            try:
                pytz.timezone(persisted_tz)
                self.timezone = persisted_tz
            except pytz.exceptions.UnknownTimeZoneError:
                self.timezone = "UTC"
            current_offset = self._compute_offset_minutes(self.timezone)
            try:
                persisted_offset_minutes = int(str(persisted_offset)) if persisted_offset is not None else None
            except Exception:
                persisted_offset_minutes = None
            self._offset_minutes = current_offset
            if persisted_offset_minutes != current_offset:
                save_dotenv_value("DEFAULT_USER_UTC_OFFSET_MINUTES", str(self._offset_minutes))
            self.apply_process_timezone()

    def get_timezone(self) -> str:
        return self.timezone

    def get_tzinfo(self):
        try:
            return pytz.timezone(self.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return pytz.timezone("UTC")

    def _compute_offset_minutes(self, timezone_name: str) -> int:
        tzinfo = pytz.timezone(timezone_name)
        now_in_tz = datetime.now(tzinfo)
        offset = now_in_tz.utcoffset()
        return int(offset.total_seconds() // 60) if offset else 0

    def get_offset_minutes(self) -> int:
        return self._offset_minutes

    def apply_process_timezone(self) -> None:
        """Apply the configured timezone to this process and child processes."""
        os.environ["TZ"] = self.timezone
        if hasattr(time, "tzset"):
            try:
                time.tzset()
            except Exception as e:
                PrintStyle.error(f"Error applying timezone {self.timezone}: {e}")

    def now(self) -> datetime:
        """Return the current datetime in the user's configured timezone."""
        return datetime.now(self.get_tzinfo())

    def now_iso(self, sep: str = "T", timespec: str = "auto") -> str:
        return self.now().isoformat(sep=sep, timespec=timespec)

    def localize_naive_datetime(self, dt: datetime) -> datetime:
        """Treat a naive datetime as user-local and make it timezone-aware."""
        if dt.tzinfo is not None:
            return dt
        tzinfo = self.get_tzinfo()
        try:
            return tzinfo.localize(dt, is_dst=None)
        except pytz.exceptions.AmbiguousTimeError:
            return tzinfo.localize(dt, is_dst=False)
        except pytz.exceptions.NonExistentTimeError:
            return tzinfo.localize(dt, is_dst=True)

    def set_timezone(self, timezone: str) -> None:
        """Set the user's IANA timezone and propagate it to child processes."""
        try:
            # Validate timezone and compute its current offset
            _ = pytz.timezone(timezone)
            new_offset = self._compute_offset_minutes(timezone)
            if timezone == self.timezone and new_offset == self._offset_minutes:
                self.apply_process_timezone()
                return

            prev_tz = getattr(self, "timezone", "None")
            prev_off = getattr(self, "_offset_minutes", None)
            PrintStyle.debug(
                f"Changing timezone from {prev_tz} (offset {prev_off}) to {timezone} (offset {new_offset})"
            )
            self._offset_minutes = new_offset
            self.timezone = timezone
            save_dotenv_value("DEFAULT_USER_TIMEZONE", timezone)
            save_dotenv_value("DEFAULT_USER_UTC_OFFSET_MINUTES", str(self._offset_minutes))
            self.apply_process_timezone()
            self._last_timezone_change = datetime.now()
        except pytz.exceptions.UnknownTimeZoneError:
            fallback_timezone = self.timezone
            try:
                pytz.timezone(fallback_timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                fallback_timezone = "UTC"

            PrintStyle.error(f"Unknown timezone: {timezone}, keeping {fallback_timezone}")
            self.timezone = fallback_timezone
            self._offset_minutes = self._compute_offset_minutes(fallback_timezone)
            self.apply_process_timezone()

    def localtime_str_to_utc_dt(self, localtime_str: str | None) -> datetime | None:
        """
        Convert a local time ISO string to a UTC datetime object.
        Returns None if input is None or invalid.
        When input lacks tzinfo, assume the configured user timezone.
        """
        if not localtime_str:
            return None

        try:
            localtime_str = localtime_str.strip().replace("Z", "+00:00")
            # Handle both with and without timezone info
            try:
                # Try parsing with timezone info first
                local_datetime_obj = datetime.fromisoformat(localtime_str)
                if local_datetime_obj.tzinfo is None:
                    # If no timezone info, assume the configured user timezone.
                    local_datetime_obj = self.localize_naive_datetime(local_datetime_obj)
            except ValueError:
                # If timezone parsing fails, try a few common local formats.
                cleaned = localtime_str.replace("T", " ")
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        local_datetime_obj = datetime.strptime(cleaned, fmt)
                        local_datetime_obj = self.localize_naive_datetime(local_datetime_obj)
                        break
                    except ValueError:
                        continue
                else:
                    raise

            # Convert to UTC
            return local_datetime_obj.astimezone(dt_timezone.utc)
        except Exception as e:
            PrintStyle.error(f"Error converting localtime string to UTC: {e}")
            return None

    def utc_dt_to_localtime_str(self, utc_dt: datetime | None, sep: str = "T", timespec: str = "auto") -> str | None:
        """
        Convert a UTC datetime object to a local time ISO string using the user's timezone.
        Returns None if input is None.
        """
        if utc_dt is None:
            return None

        # At this point, utc_dt is definitely not None
        assert utc_dt is not None

        try:
            # Ensure datetime is timezone aware in UTC
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=dt_timezone.utc)
            else:
                utc_dt = utc_dt.astimezone(dt_timezone.utc)

            # Convert to local time using the user's timezone.
            local_datetime_obj = utc_dt.astimezone(self.get_tzinfo())
            return local_datetime_obj.isoformat(sep=sep, timespec=timespec)
        except Exception as e:
            PrintStyle.error(f"Error converting UTC datetime to localtime string: {e}")
            return None

    def serialize_datetime(self, dt: datetime | None) -> str | None:
        """
        Serialize a datetime object to ISO format string using the user's timezone.
        This ensures the frontend receives dates with the correct offset for display.
        """
        if dt is None:
            return None

        # At this point, dt is definitely not None
        assert dt is not None

        try:
            # Ensure datetime is timezone aware (if not, assume the user's timezone)
            if dt.tzinfo is None:
                dt = self.localize_naive_datetime(dt)

            local_dt = dt.astimezone(self.get_tzinfo())
            return local_dt.isoformat()
        except Exception as e:
            PrintStyle.error(f"Error serializing datetime: {e}")
            return None
