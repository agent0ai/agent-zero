import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from types import SimpleNamespace

# Catch-all mock importer to avoid heavy Agent Zero dependencies locally
from importlib.machinery import ModuleSpec

class MockLoader:
    def create_module(self, spec):
        if spec.name in sys.modules:
            return sys.modules[spec.name]
        mock = MagicMock()
        # Ensure submodules can be accessed via attributes
        mock.__path__ = []
        sys.modules[spec.name] = mock
        return mock
        
    def exec_module(self, module):
        pass

class MockImporter:
    def find_spec(self, fullname, path, target=None):
        catch_prefixes = [
            'langchain', 'faiss', 'simpleeval', 'webcolors', 'litellm', 
            'openai', 'cryptography', 'nest_asyncio', 'whisper', 'git', 
            'tiktoken', 'browser_use', 'docker', 'duckduckgo_search', 'bs4',
            'html2text', 'yaml', 'aiohttp', 'jinja2', 'markdown', 'requests',
            'sentence_transformers', 'regex', 'pydantic', 'rich', 'pymupdf',
            'playwright', 'pathspec', 'tenacity', 'dotenv'
        ]
        if any(fullname.startswith(p) for p in catch_prefixes):
            return ModuleSpec(fullname, MockLoader(), is_package=True)
        return None

sys.meta_path.insert(0, MockImporter())

@pytest.fixture
def mock_memory():
    from plugins.memory.helpers.memory import Memory
    # Create a dummy Memory object bypassing init to avoid Faiss overhead
    mem = Memory.__new__(Memory)
    mem.memory_subdir = "test_subdir"
    mem.agent = SimpleNamespace(name="TestAgent")
    # Mock insert_documents since we only test the post-save hook behavior
    mem.insert_documents = AsyncMock(return_value=["doc-123"])
    return mem

@pytest.mark.asyncio
async def test_memory_saved_after_hook_called(mock_memory):
    text = "Hello world"
    metadata = {"source": "test"}

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        doc_id = await mock_memory.insert_text(text, metadata=metadata)
        
        assert doc_id == "doc-123"
        mock_call_ext.assert_called_once_with(
            "memory_saved_after",
            agent=mock_memory.agent,
            text=text,
            metadata=metadata,
            doc_id="doc-123",
            memory_subdir="test_subdir"
        )

@pytest.mark.asyncio
async def test_memory_saved_after_hook_failure_isolation(mock_memory):
    text = "Hello world"
    metadata = {"source": "test"}

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        # Simulate a crash in an extension
        mock_call_ext.side_effect = Exception("Extension crashed")
        
        # Patch PrintStyle.warning to ensure it logs the error without raising
        with patch("python.helpers.print_style.PrintStyle.warning") as mock_print:
            doc_id = await mock_memory.insert_text(text, metadata=metadata)
            
            # Memory save succeeds despite extension crash
            assert doc_id == "doc-123"
            
            # Warning was emitted
            mock_print.assert_called_once()
            args, _ = mock_print.call_args
            assert "memory_saved_after hook failed: Exception" in args[0]

