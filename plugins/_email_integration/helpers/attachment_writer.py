"""
Write attachment files into execution runtime. 

No agent/tool dependencies.
"""

import base64
import os
from typing import TypedDict


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

class WriteResult(TypedDict):
    path: str
    error: str


# ------------------------------------------------------------------
# File writer
# ------------------------------------------------------------------

def write_attachment(rel_path: str, content_b64: str) -> WriteResult:
    try:
        from helpers import files
        abs_path = files.get_abs_path(rel_path)
        files.make_dirs(abs_path)
        
        content = base64.b64decode(content_b64)
        files.write_file_bin(abs_path, content)
        
        return WriteResult(path=abs_path, error="")
    except Exception as e:
        return WriteResult(path="", error=str(e))