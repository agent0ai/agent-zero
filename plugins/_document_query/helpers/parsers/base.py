"""Base parser with built-in thread offload and timeout."""

import asyncio
from abc import ABC, abstractmethod

from helpers.print_style import PrintStyle
from plugins._document_query.helpers.fetch import FetchedDocument


class BaseParser(ABC):
    """Abstract base for document parsers.

    Every parser runs synchronously but is automatically offloaded to a
    thread pool and bounded by a configurable timeout when called through
    parse(). This prevents any single parser from blocking the asyncio
    event loop.
    """

    mimetypes: list[str] = []

    def enabled(self, config: dict) -> bool:
        return True

    def can_handle(self, mimetype: str) -> bool:
        """Return True if this parser supports *mimetype*."""
        for pattern in self.mimetypes:
            if pattern == "*":
                return True
            if pattern.endswith("/"):
                if mimetype.startswith(pattern):
                    return True
            elif mimetype == pattern:
                return True
        return False

    async def parse(
        self,
        document: FetchedDocument,
        config: dict,
        timeout: float = 60.0,
        thread_offload: bool = True,
    ) -> str:
        try:
            if thread_offload:
                return await asyncio.wait_for(
                    asyncio.to_thread(self._parse_sync, document, config),
                    timeout=timeout,
                )
            else:
                return await asyncio.wait_for(
                    self._parse_async(document, config),
                    timeout=timeout,
                )
        except asyncio.TimeoutError:
            PrintStyle.error(
                f"Parser {self.__class__.__name__} timed out after {timeout}s on {document.uri}"
            )
            raise ValueError(f"Document parsing timed out after {timeout}s: {document.uri}")

    async def _parse_async(self, document: FetchedDocument, config: dict) -> str:
        return self._parse_sync(document, config)

    @abstractmethod
    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        ...
