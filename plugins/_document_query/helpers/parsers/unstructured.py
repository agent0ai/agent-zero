"""Catch-all parser using UnstructuredLoader."""

import os

from plugins._document_query.helpers.fetch import FetchedDocument
from .base import BaseParser

os.environ.setdefault("USER_AGENT", "@mixedbread-ai/unstructured")


class UnstructuredParser(BaseParser):
    mimetypes = ["*"]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        from langchain_unstructured import UnstructuredLoader

        with document.local_file() as file_path:
            loader = UnstructuredLoader(
                file_path=file_path,
                mode="single",
                partition_via_api=False,
                strategy="hi_res",
            )
            elements = loader.load()
        return "\n".join(e.page_content for e in elements)
