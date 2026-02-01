"""Smart retry logic for deployment operations with error classification."""

from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


class TransientDeploymentError(Exception):
    """Errors that should be retried with exponential backoff."""

    pass


class PermanentDeploymentError(Exception):
    """Errors that should fail immediately without retry."""

    pass


def classify_error(exception: Exception, platform: str) -> Exception:
    """
    Classify exception as transient or permanent.

    Args:
        exception: The caught exception
        platform: Platform name (kubernetes, aws, gcp, ssh)

    Returns:
        TransientDeploymentError or PermanentDeploymentError
    """
    # Transient error patterns (network, timeouts, rate limits)
    transient_types = (
        ConnectionError,
        TimeoutError,
    )

    transient_messages = [
        "timeout",
        "temporarily unavailable",
        "rate limit",
        "throttl",
        "503",
        "connection reset",
        "temporarily",
    ]

    # Permanent error patterns (auth, config, not found)
    permanent_types = (
        PermissionError,
        ValueError,
        FileNotFoundError,
    )

    permanent_messages = [
        "permission denied",
        "access denied",
        "not found",
        "invalid",
        "unauthorized",
        "forbidden",
        "401",
        "403",
        "404",
    ]

    # Check exception type
    if isinstance(exception, transient_types):
        return TransientDeploymentError(str(exception))

    if isinstance(exception, permanent_types):
        return PermanentDeploymentError(str(exception))

    # Check error message
    error_msg = str(exception).lower()

    for pattern in transient_messages:
        if pattern in error_msg:
            return TransientDeploymentError(str(exception))

    for pattern in permanent_messages:
        if pattern in error_msg:
            return PermanentDeploymentError(str(exception))

    # Default to transient (safer to retry)
    return TransientDeploymentError(str(exception))


async def with_retry(func, *args, **kwargs):
    """
    Execute async function with smart retry logic.

    Retries transient errors up to 3 times with exponential backoff.
    Fails immediately on permanent errors.

    Args:
        func: Async function to execute
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Result from function

    Raises:
        PermanentDeploymentError: On permanent errors (no retry)
        TransientDeploymentError: After 3 retries of transient errors
    """
    from tenacity import AsyncRetrying

    retry_config = AsyncRetrying(
        retry=retry_if_exception_type(TransientDeploymentError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )

    async for attempt in retry_config:
        with attempt:
            try:
                return await func(*args, **kwargs)
            except PermanentDeploymentError:
                # Don't classify, just re-raise immediately
                raise
            except Exception as e:
                platform = kwargs.get("platform", "unknown")
                classified = classify_error(e, platform)
                raise classified
