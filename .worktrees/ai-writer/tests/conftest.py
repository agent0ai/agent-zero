"""
Pytest configuration and fixtures for AI Agent tests
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path():
    """Create temporary database path for AI Agent tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "ai_agent.db"


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "async: Async tests")
    config.addinivalue_line("markers", "performance: Performance tests")
