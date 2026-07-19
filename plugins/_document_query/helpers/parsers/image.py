"""Image parser — delegates to UnstructuredLoader."""
from plugins._document_query.helpers.fetch import FetchedDocument
from .base import BaseParser
from .unstructured import UnstructuredParser


class ImageParser(BaseParser):
    mimetypes = ["image/"]
    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        return UnstructuredParser()._parse_sync(document, config)
