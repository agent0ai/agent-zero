"""Progress reporting framework for deployment operations."""

import logging
from collections.abc import AsyncGenerator
from typing import Optional


class StreamingProgressReporter:
    """Yields progress messages for streaming output."""

    async def report(self, message: str, percent: Optional[int] = None) -> AsyncGenerator[dict, None]:
        """
        Yield progress update.

        Args:
            message: Progress message
            percent: Optional completion percentage

        Yields:
            dict with type="progress", message, and optional percent
        """
        yield {"type": "progress", "message": message, "percent": percent}


class LoggingProgressReporter:
    """Logs progress messages (for testing/debugging)."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def report(self, message: str, percent: Optional[int] = None):
        """
        Log progress message.

        Args:
            message: Progress message
            percent: Optional completion percentage
        """
        if percent is not None:
            self.logger.info(f"[{percent}%] {message}")
        else:
            self.logger.info(message)
