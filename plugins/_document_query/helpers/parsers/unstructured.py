"""Catch-all parser using Unstructured's local partitioner."""

import os
from pathlib import Path

from plugins._document_query.helpers.document import FetchedDocument
from plugins._document_query.helpers.ocr_dependencies import (
    ensure_pdf_ocr_dependencies,
    ensure_tesseract_dependencies,
)
from .base import BaseParser

os.environ.setdefault("USER_AGENT", "@mixedbread-ai/unstructured")


def _partition_file(file_path: str):
    from unstructured.partition.auto import partition

    return partition(filename=file_path, strategy="hi_res")


class UnstructuredParser(BaseParser):
    mimetypes = ["*"]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        with document.local_file() as file_path:
            _ensure_ocr_dependencies(document.mimetype, str(file_path))
            elements = _partition_file(str(file_path))
        return "\n".join(str(element) for element in elements)


def _ensure_ocr_dependencies(mimetype: str, file_path: str) -> None:
    suffix = Path(file_path).suffix.lower()
    if mimetype == "application/pdf" or suffix == ".pdf":
        ensure_pdf_ocr_dependencies()
    elif mimetype.startswith("image/") or suffix in {
        ".bmp",
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }:
        ensure_tesseract_dependencies()
