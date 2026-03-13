import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call
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
    # Mock insert_documents since we only test the hook behavior
    mem.insert_documents = AsyncMock(return_value=["doc-123"])
    return mem


@pytest.mark.asyncio
async def test_memory_save_before_called_with_object(mock_memory):
    """memory_save_before receives a mutable {object} dict."""
    text = "Hello world"
    metadata = {"source": "test"}

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        doc_id = await mock_memory.insert_text(text, metadata=metadata)

        assert doc_id == "doc-123"
        # memory_save_before is the first call
        before_call = mock_call_ext.call_args_list[0]
        assert before_call == call(
            "memory_save_before",
            agent=mock_memory.agent,
            object={"text": text, "metadata": metadata, "memory_subdir": "test_subdir"},
        )


@pytest.mark.asyncio
async def test_memory_save_after_called_with_doc_id(mock_memory):
    """memory_save_after receives the object with doc_id after persist."""
    text = "Hello world"
    metadata = {"source": "test"}

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        doc_id = await mock_memory.insert_text(text, metadata=metadata)

        assert doc_id == "doc-123"
        # memory_save_after is the second call
        after_call = mock_call_ext.call_args_list[1]
        assert after_call == call(
            "memory_save_after",
            agent=mock_memory.agent,
            object={
                "text": text,
                "metadata": metadata,
                "memory_subdir": "test_subdir",
                "doc_id": "doc-123",
            },
        )


@pytest.mark.asyncio
async def test_memory_save_skipped_when_text_none(mock_memory):
    """Save is skipped when memory_save_before sets object['text'] to None."""
    text = "Hello world"
    metadata = {"source": "test"}

    async def nullify_text(*args, **kwargs):
        # Simulate an extension setting text to None
        obj = kwargs.get("object")
        if obj is not None:
            obj["text"] = None

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        mock_call_ext.side_effect = nullify_text
        doc_id = await mock_memory.insert_text(text, metadata=metadata)

        # Save was skipped
        assert doc_id is None
        # insert_documents was never called
        mock_memory.insert_documents.assert_not_called()
        # Only memory_save_before was called (no after)
        assert mock_call_ext.call_count == 1


@pytest.mark.asyncio
async def test_memory_save_before_can_modify_text(mock_memory):
    """Extensions can modify the text via memory_save_before."""
    text = "Original"
    metadata = {"source": "test"}

    async def modify_text(*args, **kwargs):
        obj = kwargs.get("object")
        if obj is not None and obj.get("text") == "Original":
            obj["text"] = "Modified by extension"

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        mock_call_ext.side_effect = modify_text
        doc_id = await mock_memory.insert_text(text, metadata=metadata)

        assert doc_id == "doc-123"
        # Verify insert_documents was called with the modified text
        call_args = mock_memory.insert_documents.call_args
        doc = call_args[0][0][0]
        assert doc.page_content == "Modified by extension"


@pytest.mark.asyncio
async def test_extension_exceptions_propagate(mock_memory):
    """No try/catch — extension errors propagate to the caller."""
    text = "Hello world"
    metadata = {"source": "test"}

    with patch("python.helpers.extension.call_extensions", new_callable=AsyncMock) as mock_call_ext:
        mock_call_ext.side_effect = RuntimeError("Extension crashed")

        with pytest.raises(RuntimeError, match="Extension crashed"):
            await mock_memory.insert_text(text, metadata=metadata)
