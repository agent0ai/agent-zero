"""HTML parser using Markdownify transformer."""

import re

from plugins._document_query.helpers.document import FetchedDocument
from .base import BaseParser


class HtmlParser(BaseParser):
    mimetypes = ["text/html"]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        from markdownify import markdownify

        text = markdownify(document.text(), heading_style="ATX").replace("\xa0", " ").strip()
        return re.sub(r"\n\s*\n", "\n\n", text)
