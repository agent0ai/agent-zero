"""PDF parser with PyMuPDF primary and Tesseract OCR fallback."""

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
        from langchain_community.document_loaders.pdf import PyMuPDFLoader

        try:
            loader = PyMuPDFLoader(
                file_path,
                mode="single",
                extract_tables="markdown",
                extract_images=True,
                images_inner_format="text",
                images_parser=_on_demand_tesseract_blob_parser(),
                pages_delimiter="\n",
            )
            return "\n".join(e.page_content for e in loader.load())
        except Exception as e:
            logging.error(f"PyMuPDF parsing failed: {e}")
            return ""

    def _parse_with_ocr(self, file_path: str) -> str:
        import pdf2image, pytesseract

        ensure_pdf_ocr_dependencies()
        logging.debug(f"FALLBACK: OCR for {file_path}")
        pages = pdf2image.convert_from_path(file_path)
        return "\n\n".join(pytesseract.image_to_string(p) for p in pages)


def _on_demand_tesseract_blob_parser():
    from langchain_community.document_loaders.parsers.images import TesseractBlobParser

    class OnDemandTesseractBlobParser(TesseractBlobParser):
        def _analyze_image(self, img) -> str:
            ensure_tesseract_dependencies()
            return super()._analyze_image(img)

    return OnDemandTesseractBlobParser()
