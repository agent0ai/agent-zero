"""PDF parser with PyMuPDF primary and Tesseract OCR fallback."""

import os

from helpers.print_style import PrintStyle
from plugins._document_query.helpers.fetch import FetchedDocument

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
                    raise ValueError("PyMuPDF returned no content and OCR fallback is disabled")
                contents = self._parse_with_ocr(file_path)
            return contents

    def _parse_with_pymupdf(self, file_path: str) -> str:
        from langchain_community.document_loaders.pdf import PyMuPDFLoader
        from langchain_community.document_loaders.parsers.images import TesseractBlobParser

        try:
            loader = PyMuPDFLoader(
                file_path, mode="single", extract_tables="markdown",
                extract_images=True, images_inner_format="text",
                images_parser=TesseractBlobParser(), pages_delimiter="\n",
            )
            return "\n".join(e.page_content for e in loader.load())
        except Exception as e:
            PrintStyle.error(f"PyMuPDF parsing failed: {e}")
            return ""

    def _parse_with_ocr(self, file_path: str) -> str:
        import pdf2image, pytesseract
        PrintStyle.debug(f"FALLBACK: OCR for {file_path}")
        pages = pdf2image.convert_from_path(file_path)
        return "\n\n".join(pytesseract.image_to_string(p) for p in pages)
