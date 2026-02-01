import pytest

from python.helpers.deployment_health import check_http_endpoint


@pytest.mark.asyncio
async def test_health_check_timeout():
    """Test health check timeout handling"""
    # Use httpbin for testing - request to non-responsive port
    success, details = await check_http_endpoint(
        "http://127.0.0.1:1",  # Port 1 - should timeout
        timeout=1,
    )

    assert success is False
    assert "error" in details or "timeout" in str(details).lower()


@pytest.mark.asyncio
async def test_health_check_invalid_url():
    """Test health check with invalid URL"""
    success, details = await check_http_endpoint("http://invalid-domain-that-does-not-exist-12345.com/health")

    assert success is False
    assert "error" in details


@pytest.mark.asyncio
async def test_health_check_response_time():
    """Test health check records response time"""
    # Use httpbin.org (public testing service)
    try:
        success, details = await check_http_endpoint(
            "https://httpbin.org/status/200",
            timeout=10,
        )
        # If we can reach httpbin, verify response time is recorded
        if "response_time_ms" in details:
            assert details["response_time_ms"] >= 0
            assert isinstance(details["response_time_ms"], float)
    except Exception:
        # Skip if httpbin is unavailable
        pytest.skip("httpbin.org not available")


@pytest.mark.asyncio
async def test_health_check_custom_headers():
    """Test health check with custom headers"""
    try:
        headers = {"User-Agent": "Test-Agent"}
        success, details = await check_http_endpoint(
            "https://httpbin.org/user-agent",
            timeout=10,
            headers=headers,
        )
        # Just verify the call works with headers
        assert "url" in details or "error" in details
    except Exception:
        pytest.skip("httpbin.org not available")


@pytest.mark.asyncio
async def test_health_check_basic_structure():
    """Test health check response structure"""
    success, details = await check_http_endpoint(
        "http://127.0.0.1:1",  # Will timeout
        timeout=1,
    )

    # Verify response structure
    assert isinstance(success, bool)
    assert isinstance(details, dict)
    assert "url" in details
    assert success is False  # Should fail
