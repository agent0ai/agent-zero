from __future__ import annotations
import mimetypes
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

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

