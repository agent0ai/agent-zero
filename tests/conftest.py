import pytest
import sys
import os
import threading
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.config = MagicMock()
    agent.config.chat_model = "openrouter/test-model"
    agent.config.embeddings_model = "openai/text-embedding-3-small"
    agent.context = MagicMock()
    agent.context.id = "test-ctx-001"
    agent.context.log = MagicMock()
    agent.context.communicate = AsyncMock()
    agent.context.streaming_agent = None
    agent.context.paused = False
    agent.number = 0
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    agent.hist_add_tool_result = MagicMock()
    agent.read_prompt = MagicMock(return_value="test prompt")
    agent.history = []
    return agent


@pytest.fixture
def mock_loop_data(mock_agent):
    ld = MagicMock()
    ld.message = "test user message"
    ld.extras_temporary = ""
    ld.extras_persistent = ""
    ld.agent = mock_agent
    ld.iteration = 1
    return ld


@pytest.fixture
def default_settings():
    return {
        "chat_model": "openrouter/test-model",
        "embeddings_model": "openai/text-embedding-3-small",
        "cognee_search_type": "CHUNKS",
        "cognee_chunk_size": 1024,
        "cognee_chunk_overlap": 128,
        "cognee_temporal_enabled": False,
        "cognee_search_system_prompt": "",
    }


@pytest.fixture
def mock_settings(default_settings):
    settings = MagicMock()
    settings.get = MagicMock(
        side_effect=lambda key, default=None: default_settings.get(key, default)
    )
    return settings


@pytest.fixture
def patch_settings(mock_settings):
    with patch("python.helpers.settings.get_settings", return_value=mock_settings):
        yield mock_settings


@pytest.fixture
def mock_cognee():
    cognee = MagicMock()
    cognee.add = AsyncMock()
    cognee.search = AsyncMock(return_value=[])
    cognee.setup = AsyncMock()
    cognee.cognify = AsyncMock()
    cognee.memify = AsyncMock()
    cognee.config = MagicMock()
    cognee.datasets = MagicMock()
    cognee.datasets.list_datasets = AsyncMock(return_value=[])
    cognee.datasets.list_data = AsyncMock(return_value=[])
    cognee.datasets.delete_data = AsyncMock()
    return cognee


@pytest.fixture
def tmp_workdir(tmp_path):
    for d in ["knowledge", "chats", "memory", "logs", "projects", "work_dir", "usr"]:
        (tmp_path / d).mkdir()
    return tmp_path


@pytest.fixture
def mock_files(tmp_workdir):
    files_mock = MagicMock()
    files_mock.get_abs_path = MagicMock(
        side_effect=lambda *args: str(tmp_workdir / "/".join(str(a) for a in args))
    )
    files_mock.get_base_dir = MagicMock(return_value=str(tmp_workdir))
    return files_mock


@pytest.fixture
def mock_app():
    from flask import Flask
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    lock = threading.Lock()
    return app, lock


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires real external services")
    config.addinivalue_line("markers", "slow: tests that take >5s")
