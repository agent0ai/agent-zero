import pytest

from python.helpers.deployment_retry import (
    PermanentDeploymentError,
    TransientDeploymentError,
    classify_error,
    with_retry,
)


def test_classify_transient_network_error():
    """Network errors should be classified as transient"""
    error = ConnectionError("Connection timeout")
    classified = classify_error(error, "kubernetes")
    assert isinstance(classified, TransientDeploymentError)


def test_classify_permanent_auth_error():
    """Auth errors should be classified as permanent"""
    error = PermissionError("Access denied")
    classified = classify_error(error, "kubernetes")
    assert isinstance(classified, PermanentDeploymentError)


def test_classify_kubernetes_api_exception():
    """Test platform-specific Kubernetes errors"""
    # Simulate kubernetes.client.exceptions.ApiException behavior
    error = Exception("ApiException: (503) Service Unavailable")
    classified = classify_error(error, "kubernetes")
    assert isinstance(classified, TransientDeploymentError)


def test_classify_aws_throttling():
    """Test AWS throttling as transient"""
    error = Exception("ClientError: An error occurred (Throttling) when calling...")
    classified = classify_error(error, "aws")
    assert isinstance(classified, TransientDeploymentError)


def test_classify_permission_as_permanent():
    """Permission errors should never retry"""
    error = Exception("403 Forbidden: Insufficient permissions")
    classified = classify_error(error, "gcp")
    assert isinstance(classified, PermanentDeploymentError)


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_transient_errors():
    """Test retry decorator retries transient errors"""
    call_count = 0

    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientDeploymentError("Temporary failure")
        return "success"

    result = await with_retry(flaky_function)
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retry_fails_immediately_on_permanent():
    """Test retry decorator doesn't retry permanent errors"""
    call_count = 0

    async def broken_function():
        nonlocal call_count
        call_count += 1
        raise PermanentDeploymentError("Auth failure")

    with pytest.raises(PermanentDeploymentError):
        await with_retry(broken_function)

    assert call_count == 1  # Only called once
