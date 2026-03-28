"""
Read attachment files from execution runtime.

No agent/tool dependencies.
"""

import base64
import os
from typing import TypedDict


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

class AttachmentData(TypedDict):
    name: str
    content_b64: str
    error: str


# ------------------------------------------------------------------
# File reader
# ------------------------------------------------------------------

def read_attachment(path: str) -> AttachmentData:
    try:
        if not os.path.isfile(path):
            return AttachmentData(
                name="", content_b64="", error=f"file not found: {path}")
        name = os.path.basename(path)
        with open(path, "rb") as f:
            content = f.read()
        return AttachmentData(
            name=name,
            content_b64=base64.b64encode(content).decode(),
            error="",
        )
    except Exception as e:
        return AttachmentData(name="", content_b64="", error=str(e))
