"""Shared storage paths for the WhatsApp bridge."""

from helpers import files


def get_bridge_session_dir() -> str:
    return files.get_abs_path(files.TEMP_DIR, "whatsapp", "session")


def get_bridge_media_dir() -> str:
    return files.get_abs_path(files.TEMP_DIR, "whatsapp", "media")
