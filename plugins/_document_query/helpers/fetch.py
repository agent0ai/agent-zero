"""Centralized document fetching for the document_query plugin."""

from __future__ import annotations

import asyncio
import mimetypes
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import urlparse

from helpers import files
from helpers.network import fetch_public_http_resource


InterventionCallback = Callable[[], Awaitable[None]]


@dataclass(frozen=True)
class FetchedDocument:
    """Fetched document bytes plus metadata needed by parsers."""

    uri: str
    scheme: str
    mimetype: str
    content: bytes
    encoding: str | None = None
    charset: str | None = None
    local_path: str | None = None
    source_uri: str | None = None

    def text(self) -> str:
        charset = self.charset or "utf-8"
        return self.content.decode(charset, errors="replace")

    def suffix(self) -> str:
        path = self.local_path or urlparse(self.uri).path or self.uri
        suffix = Path(path).suffix
        if suffix:
            return suffix
        guessed = mimetypes.guess_extension(self.mimetype)
        return guessed or ".bin"

    @contextmanager
    def local_file(self):
        """Yield a filesystem path for parsers that cannot consume bytes."""
        if self.local_path and os.path.exists(self.local_path):
            yield self.local_path
            return

        tmp = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=self.suffix()) as f:
                f.write(self.content)
                tmp = f.name
            yield tmp
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)


ProtocolHandler = Callable[
    [str, str, dict, InterventionCallback | None], Awaitable[FetchedDocument]
]

_PROTOCOL_HANDLERS: dict[str, ProtocolHandler] = {}


def register_protocol_handler(scheme: str, handler: ProtocolHandler) -> None:
    """Register or replace a fetch handler for a URI scheme."""
    _PROTOCOL_HANDLERS[scheme.lower()] = handler


async def fetch_public_resource(
    uri: str,
    config: dict | None = None,
    intervention_callback: InterventionCallback | None = None,
) -> FetchedDocument:
    """Fetch local or remote content once, then pass bytes to parsers."""
    config = config or {}
    parsed = urlparse(uri)
    scheme = (parsed.scheme or "file").lower()
    handler = _PROTOCOL_HANDLERS.get(scheme)
    if not handler:
        raise ValueError(f"Unsupported document scheme: {scheme}")
    return await handler(uri, scheme, config, intervention_callback)


async def _fetch_file(
    uri: str,
    scheme: str,
    config: dict,
    intervention_callback: InterventionCallback | None,
) -> FetchedDocument:
    parsed = urlparse(uri)
    raw_path = parsed.path if parsed.scheme == "file" else uri
    if not raw_path:
        raise ValueError(f"Invalid document path: {uri}")

    path = _fix_file_path(raw_path)
    mimetype, encoding = mimetypes.guess_type(path)
    if encoding:
        raise ValueError(f"Compressed documents are unsupported '{encoding}' ({uri})")
    mimetype = mimetype or "application/octet-stream"
    if mimetype == "application/octet-stream":
        raise ValueError(f"Unsupported document mimetype '{mimetype}' ({uri})")

    if intervention_callback:
        await intervention_callback()
    return FetchedDocument(
        uri=path,
        source_uri=uri,
        scheme=scheme,
        mimetype=mimetype,
        encoding=encoding,
        content=files.read_file_bin(path),
        local_path=path,
    )


async def _fetch_http(
    uri: str,
    scheme: str,
    config: dict,
    intervention_callback: InterventionCallback | None,
) -> FetchedDocument:
    timeout = float(config.get("fetch_timeout", 30))
    retries = max(1, int(config.get("fetch_retries", 3)))
    retry_backoff = float(config.get("fetch_retry_backoff", 1.0))
    max_remote_bytes = int(config.get("max_remote_bytes", 50 * 1024 * 1024))
    parsed = urlparse(uri)
    guessed_mimetype, encoding = mimetypes.guess_type(parsed.path or uri)
    if encoding:
        raise ValueError(f"Compressed documents are unsupported '{encoding}' ({uri})")

    last_error = ""
    for attempt in range(retries):
        try:
            if intervention_callback:
                await intervention_callback()
            resource = await asyncio.to_thread(
                fetch_public_http_resource,
                uri,
                max_bytes=max_remote_bytes,
                timeout=(timeout, timeout),
            )
            if intervention_callback:
                await intervention_callback()

            mimetype = (
                resource.content_type
                or guessed_mimetype
                or "application/octet-stream"
            )
            if mimetype == "application/octet-stream":
                raise ValueError(
                    f"Unsupported document mimetype '{mimetype}' ({uri})"
                )

            return FetchedDocument(
                uri=resource.url,
                source_uri=uri,
                scheme=urlparse(resource.url).scheme or scheme,
                mimetype=mimetype,
                encoding=encoding,
                charset=resource.encoding,
                content=resource.content,
            )
        except Exception as e:
            last_error = str(e)
            if attempt < retries - 1:
                await asyncio.sleep(retry_backoff)
                if intervention_callback:
                    await intervention_callback()

    raise ValueError(f"Document fetch error: {uri} ({last_error})")

register_protocol_handler("file", _fetch_file)
register_protocol_handler("http", _fetch_http)
register_protocol_handler("https", _fetch_http)


def _fix_file_path(path: str) -> str:
    if os.path.isabs(path) and os.path.exists(path):
        return path
    return files.fix_dev_path(path)
