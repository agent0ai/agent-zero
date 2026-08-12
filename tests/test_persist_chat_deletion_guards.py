from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import persist_chat


@pytest.mark.parametrize("ctxid", [None, "", "   "])
def test_chat_deletion_rejects_empty_context_ids(ctxid) -> None:
    with pytest.raises(ValueError, match="context id must not be empty"):
        persist_chat.remove_chat(ctxid)
    with pytest.raises(ValueError, match="context id must not be empty"):
        persist_chat.remove_msg_files(ctxid)
