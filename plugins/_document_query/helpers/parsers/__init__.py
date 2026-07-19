"""Document parser registry."""
from .base import BaseParser
from .liteparse import LiteParseParser
from .pdf import PdfParser
from .html import HtmlParser
from .text import TextParser
from .image import ImageParser
from .unstructured import UnstructuredParser

_PARSERS = [
    LiteParseParser(),
    PdfParser(),
    HtmlParser(),
    TextParser(),
    ImageParser(),
    UnstructuredParser(),
]

def get_parsers_for_mimetype(mimetype: str, config: dict | None = None) -> list[BaseParser]:
    config = config or {}
    parsers = []
    for parser in _PARSERS:
        if parser.enabled(config) and parser.can_handle(mimetype):
            parsers.append(parser)
    return parsers

def get_parser_for_mimetype(mimetype: str, config: dict | None = None) -> BaseParser | None:
    parsers = get_parsers_for_mimetype(mimetype, config)
    if parsers:
        return parsers[0]
    return None

__all__ = [
    "BaseParser",
    "LiteParseParser",
    "PdfParser",
    "HtmlParser",
    "TextParser",
    "ImageParser",
    "UnstructuredParser",
    "get_parser_for_mimetype",
    "get_parsers_for_mimetype",
]
