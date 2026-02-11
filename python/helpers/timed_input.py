import sys

from inputimeout import TimeoutOccurred, inputimeout


def timeout_input(prompt, timeout=10):
    try:
        if sys.platform != "win32":
            import readline  # noqa: F401 — side-effect import: enables line editing for input()
        user_input = inputimeout(prompt=prompt, timeout=timeout)
        return user_input
    except TimeoutOccurred:
        return ""
