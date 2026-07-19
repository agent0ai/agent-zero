"""Compatibility shim for the document_query plugin extraction."""

from plugins._document_query.helpers.document_query import (
    DEFAULT_SEARCH_THRESHOLD,
    DocumentQueryHelper,
    DocumentQueryStore,
)

__all__ = [
    "DEFAULT_SEARCH_THRESHOLD",
    "DocumentQueryHelper",
    "DocumentQueryStore",
]
