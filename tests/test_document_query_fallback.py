from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.document_query import DocumentQueryHelper


class FakeStore:
    @staticmethod
    def normalize_uri(uri: str) -> str:
        return uri

    async def search_documents(self, **_kwargs):
        return []


class FakeAgent:
    def __init__(self):
        self.chat_messages = None

    async def handle_intervention(self):
        return None

    def parse_prompt(self, name: str) -> str:
        return name

    async def call_utility_model(self, **_kwargs) -> str:
        return "codename"

    async def call_chat_model(self, messages, explicit_caching=False):
        self.chat_messages = messages
        return "The project codename is Atlas.", None


def test_document_qa_uses_small_document_content_when_search_finds_no_chunks():
    agent = FakeAgent()
    progress = []
    helper = object.__new__(DocumentQueryHelper)
    helper.agent = agent
    helper.store = FakeStore()
    helper.progress_callback = progress.append

    async def document_get_content(uri, add_to_db=False):
        assert uri == "/tmp/project.md"
        assert add_to_db is True
        return "# Project\n\nCodename: Atlas\n"

    helper.document_get_content = document_get_content

    ok, content = asyncio.run(
        helper.document_qa(["/tmp/project.md"], ["What is the codename?"])
    )

    assert ok is True
    assert content == "The project codename is Atlas."
    assert "No matching chunks found" in "\n".join(progress)
    assert agent.chat_messages is not None
    assert "Codename: Atlas" in agent.chat_messages[1].content


def test_small_document_fallback_refuses_large_content():
    content = DocumentQueryHelper._small_document_fallback_content(
        ["/tmp/large.md"], ["x" * 12_001]
    )

    assert content == ""
