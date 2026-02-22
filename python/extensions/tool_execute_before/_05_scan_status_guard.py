import logging
from python.helpers.extension import Extension
from python.helpers import guard_utils

logger = logging.getLogger(__name__)


class ScanStatusGuard(Extension):

    async def execute(self, tool_name: str = "", _event: dict | None = None, **kwargs):
        if not tool_name or _event is None:
            return

        status = guard_utils.get_scan_status(tool_name)
        if status is None:
            return

        verdict = status.get("status", "")

        if verdict == guard_utils.BLOCKED:
            _event["blocked"] = True
            _event["block_reason"] = "Skill flagged as unsafe by security scanner"

        elif verdict == guard_utils.NEEDS_REVIEW:
            logger.warning("Skill '%s' needs review but is allowed to execute", tool_name)