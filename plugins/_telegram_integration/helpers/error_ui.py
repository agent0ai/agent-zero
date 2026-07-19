from __future__ import annotations

import re


MAX_DETAIL_CHARS = 500


def friendly_error_message(exception: BaseException) -> str:
    summary = _error_summary(exception)
    category = _classify_error(exception, summary)

    if category == "auth":
        return (
            "**Agent Zero hit a provider setup issue.**\n\n"
            "The model provider rejected the request because an API key or credential is missing, invalid, or unauthorized.\n\n"
            f"Details: `{summary}`\n\n"
            "Please check the model/API key settings, then send the message again."
        )

    if category == "rate_limit":
        return (
            "**Agent Zero was rate limited by the model provider.**\n\n"
            "The provider is asking us to slow down before trying again.\n\n"
            f"Details: `{summary}`"
        )

    if category == "timeout":
        return (
            "**Agent Zero did not get a response in time.**\n\n"
            "The provider or tool call timed out before the agent could finish this request.\n\n"
            f"Details: `{summary}`"
        )

    if category == "provider":
        return (
            "**Agent Zero could not complete the model request.**\n\n"
            "The model provider returned an error before the agent could finish.\n\n"
            f"Details: `{summary}`"
        )

    return (
        "**Agent Zero ran into an error while working on this.**\n\n"
        f"Details: `{summary}`"
    )


def _classify_error(exception: BaseException, summary: str) -> str:
    text = f"{type(exception).__name__} {summary}".lower()

    if any(
        marker in text
        for marker in (
            "api key",
            "api_key",
            "apikey",
            "auth",
            "credential",
            "unauthorized",
            "forbidden",
            "invalid key",
            "missing key",
            "permission denied",
            "401",
            "403",
        )
    ):
        return "auth"

    if any(marker in text for marker in ("rate limit", "ratelimit", "too many requests", "429")):
        return "rate_limit"

    if any(marker in text for marker in ("timeout", "timed out", "deadline", "read timed out")):
        return "timeout"

    if any(
        marker in text
        for marker in (
            "litellm",
            "openai",
            "anthropic",
            "model",
            "provider",
            "badrequest",
            "service unavailable",
            "overloaded",
            "503",
        )
    ):
        return "provider"

    return "generic"


def _error_summary(exception: BaseException) -> str:
    text = str(exception).strip() or type(exception).__name__
    text = re.sub(r"\s+", " ", text)
    if len(text) > MAX_DETAIL_CHARS:
        text = f"{text[: MAX_DETAIL_CHARS - 3].rstrip()}..."
    return text
