"""Header-based authentication and project routing for the MCP and A2A servers.

Both servers have always taken the API token and the project from the URL
(``/t-<token>/`` and ``/p-<project>/``). URLs end up in proxy, browser and
access logs, so clients may instead send:

* ``Authorization: Bearer <token>`` - the same token as in the URL;
* ``X-A0-Project: <project>`` - the same project name as in the URL.

The URL form keeps working unchanged. Never log the token or the header value.
"""

import hmac

from helpers import projects

PROJECT_HEADER = "X-A0-Project"


class RequestRejected(Exception):
    """The request carries an invalid or conflicting project."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def token_matches(candidate: str | None, expected: str | None) -> bool:
    """Constant-time token comparison; an empty token never matches."""
    if not candidate or not expected:
        return False
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def get_header(scope, name: str) -> str | None:
    """Return the first value of header ``name`` from an ASGI scope, or None."""
    wanted = name.lower().encode("latin-1")
    for key, value in scope.get("headers") or []:
        if key.lower() == wanted:
            return value.decode("latin-1")
    return None


def get_bearer_token(scope) -> str | None:
    """Return the token of an ``Authorization: Bearer <token>`` header, or None."""
    value = get_header(scope, "authorization")
    if not value:
        return None
    scheme, _, token = value.strip().partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token.strip() or None


def resolve_project(url_project: str | None, scope) -> str | None:
    """Return the project from the URL segment or the X-A0-Project header.

    Raises RequestRejected (400) when either is not a valid project name, or
    when both are given and differ.
    """
    if url_project:
        try:
            url_project = projects.validate_project_name(url_project)
        except ValueError:
            raise RequestRejected(400, "Invalid project in URL")

    header_project = None
    header_value = get_header(scope, PROJECT_HEADER)
    if header_value is not None and header_value.strip():
        try:
            header_project = projects.validate_project_name(header_value)
        except ValueError:
            raise RequestRejected(400, f"Invalid project in {PROJECT_HEADER} header")

    if url_project and header_project and url_project != header_project:
        raise RequestRejected(
            400, f"Project in URL and {PROJECT_HEADER} header differ"
        )
    return url_project or header_project
