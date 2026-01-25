import pytest

from python.helpers.deployment_progress import LoggingProgressReporter, StreamingProgressReporter


@pytest.mark.asyncio
async def test_streaming_progress_reporter():
    """Test streaming progress reporter yields updates"""
    reporter = StreamingProgressReporter()

    messages = []
    async for update in reporter.report("Deploying...", 50):
        messages.append(update)

    assert len(messages) == 1
    assert messages[0]["type"] == "progress"
    assert messages[0]["message"] == "Deploying..."
    assert messages[0]["percent"] == 50


@pytest.mark.asyncio
async def test_logging_progress_reporter(caplog):
    """Test logging progress reporter logs messages"""
    import logging

    # Set caplog to capture INFO level logs
    caplog.set_level(logging.INFO)

    logger = logging.getLogger("test")
    reporter = LoggingProgressReporter(logger)

    await reporter.report("Starting deployment", 10)

    assert "Starting deployment" in caplog.text
    assert "[10%]" in caplog.text


@pytest.mark.asyncio
async def test_streaming_reporter_without_percent():
    """Test progress reporter without percentage"""
    reporter = StreamingProgressReporter()

    messages = []
    async for update in reporter.report("Loading config..."):
        messages.append(update)

    assert len(messages) == 1
    assert messages[0]["percent"] is None
    assert messages[0]["message"] == "Loading config..."


@pytest.mark.asyncio
async def test_logging_reporter_without_percent(caplog):
    """Test logging reporter without percentage"""
    import logging

    # Set caplog to capture INFO level logs
    caplog.set_level(logging.INFO)

    logger = logging.getLogger("test")
    reporter = LoggingProgressReporter(logger)

    await reporter.report("Configuration loaded")

    assert "Configuration loaded" in caplog.text
    assert "[" not in caplog.text  # No percentage bracket
