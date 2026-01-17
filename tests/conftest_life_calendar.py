"""
Pytest configuration and fixtures for Life Calendar tests
Shared fixtures for calendar integration testing
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "calendar_hub.db")


@pytest.fixture
def sample_event():
    """Sample calendar event"""
    return {
        "title": "Team Standup",
        "description": "Daily team synchronization",
        "start": "2026-01-20T09:00:00Z",
        "end": "2026-01-20T09:30:00Z",
        "location": "Conference Room A",
        "attendees": ["alice@example.com", "bob@example.com"],
        "recurrence": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR",
    }


@pytest.fixture
def sample_calendar_account():
    """Sample calendar account"""
    return {
        "provider": "google",
        "name": "Work Calendar",
        "email": "user@example.com",
        "timezone": "America/Los_Angeles",
    }


@pytest.fixture
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "async: Async tests")
    config.addinivalue_line("markers", "performance: Performance tests")
