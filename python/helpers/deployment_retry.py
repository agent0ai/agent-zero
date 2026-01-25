from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class TransientDeploymentError(Exception):
    """Errors that should be retried with exponential backoff"""

    pass


class PermanentDeploymentError(Exception):
    """Errors that should fail immediately without retry"""

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
        OSError,
    )

    transient_messages = [
        "timeout",
        "temporarily unavailable",
        "rate limit",
        "throttl",
        "503",
        "connection reset",
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

    # Check exception type first (more reliable than message matching)
    if isinstance(exception, permanent_types):
        return PermanentDeploymentError(str(exception))

    if isinstance(exception, transient_types):
        return TransientDeploymentError(str(exception))

    # Check error message patterns
    error_msg = str(exception).lower()

    # Check permanent patterns first (fail fast on auth/config errors)
    for pattern in permanent_messages:
        if pattern in error_msg:
            return PermanentDeploymentError(str(exception))

    for pattern in transient_messages:
        if pattern in error_msg:
            return TransientDeploymentError(str(exception))

    # Default to transient (safer to retry)
    return TransientDeploymentError(str(exception))


@retry(
    retry=retry_if_exception_type(TransientDeploymentError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def with_retry(func, *args, **kwargs):
    """
    Execute async function with smart retry logic.

    Retries transient errors up to 3 times with exponential backoff.
    Fails immediately on permanent errors.
    """
    try:
        return await func(*args, **kwargs)
    except (TransientDeploymentError, PermanentDeploymentError):
        # Already classified, re-raise as-is
        raise
    except Exception as e:
        # Classify unknown exceptions
        platform = kwargs.get("platform", "unknown")
        classified = classify_error(e, platform)
        raise classified
