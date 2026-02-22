import json
import logging
from python.helpers import files

logger = logging.getLogger(__name__)

SCAN_STATUS_DIR = "usr/skill_scans"

SAFE = "safe"
NEEDS_REVIEW = "needs_review"
BLOCKED = "blocked"


def get_scan_status(skill_name: str) -> dict | None:
    path = f"{SCAN_STATUS_DIR}/{skill_name}.json"
    if not files.exists(path):
        return None
    try:
        raw = files.read_file(path)
        return json.loads(raw)
    except Exception:
        logger.warning("Failed to read scan status for skill '%s'", skill_name)
        return None


def save_scan_status(skill_name: str, status: dict) -> None:
    path = f"{SCAN_STATUS_DIR}/{skill_name}.json"
    files.write_file(path, json.dumps(status, indent=2))