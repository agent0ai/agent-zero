"""HTML parser using Markdownify transformer."""

from plugins._document_query.helpers.fetch import FetchedDocument
from .base import BaseParser


class HtmlParser(BaseParser):
    mimetypes = ["text/html"]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        from langchain_community.document_transformers import MarkdownifyTransformer
        from langchain_core.documents import Document

        parts = [
            Document(
                page_content=document.text(),
                metadata={"source": document.source_uri or document.uri},
            )
        ]
        return "\n".join(e.page_content for e in MarkdownifyTransformer().transform_documents(parts))
