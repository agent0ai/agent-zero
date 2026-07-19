"""Plain text and config document parser."""

from plugins._document_query.helpers.fetch import FetchedDocument
from .base import BaseParser


class TextParser(BaseParser):
    mimetypes = [
        "text/", "application/json", "application/yaml", "application/x-yaml",
        "application/xml", "application/toml", "application/x-toml",
        "application/javascript", "application/typescript",
        "application/x-sh", "application/x-shellscript",
    ]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        return document.text()
