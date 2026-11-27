"""PDF parser with PyMuPDF primary and Tesseract OCR fallback."""

import io
import os

import logging
from plugins._document_query.helpers.document import FetchedDocument
from plugins._document_query.helpers.ocr_dependencies import (
    ensure_pdf_ocr_dependencies,
    ensure_tesseract_dependencies,
)

from .base import BaseParser


class PdfParser(BaseParser):
    mimetypes = ["application/pdf"]

    def _parse_sync(self, document: FetchedDocument, config: dict) -> str:
        with document.local_file() as file_path:
            if not os.path.exists(file_path):
                raise ValueError(f"Temporary file not found: {file_path}")
            contents = self._parse_with_pymupdf(file_path)
            if not contents:
                if not config.get("pdf_ocr_fallback", True):
                    raise ValueError(
                        "PyMuPDF returned no content and OCR fallback is disabled"
                    )
                contents = self._parse_with_ocr(file_path)
            return contents

    def _parse_with_pymupdf(self, file_path: str) -> str:
        import pymupdf

        try:
            parts = []
            with pymupdf.open(file_path) as pdf:
                for page in pdf:
                    parts.append(page.get_text())
                    parts.extend(table.to_markdown() for table in page.find_tables().tables)
                    for image in page.get_images():
                        data = pdf.extract_image(image[0])
                        if data and data.get("image"):
                            parts.append(_image_text(data["image"]))
            return "\n".join(parts).strip()
        except Exception as e:
            logging.error(f"PyMuPDF parsing failed: {e}")
            return ""

    def _parse_with_ocr(self, file_path: str) -> str:
        import pdf2image, pytesseract

        ensure_pdf_ocr_dependencies()
        logging.debug(f"FALLBACK: OCR for {file_path}")
        pages = pdf2image.convert_from_path(file_path)
        return "\n\n".join(pytesseract.image_to_string(p) for p in pages)


def _image_text(data):
    from PIL import Image
    import pytesseract

    ensure_tesseract_dependencies()
    with Image.open(io.BytesIO(data)) as image:
        return pytesseract.image_to_string(image, lang="eng")
