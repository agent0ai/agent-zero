from contextvars import ContextVar
from typing import Any, TypeVar, cast, Optional, Dict

T = TypeVar("T")

# no mutable default — None is safe
_context_data: ContextVar[Optional[Dict[str, Any]]] = ContextVar("_context_data", default=None)


def _ensure_context() -> Dict[str, Any]:
    """Make sure a context dict exists, and return it."""
    data = _context_data.get()
    if data is None:
        data = {}
        _context_data.set(data)
    return data


def set_context_data(key: str, value: Any):
    """Set context data for the current async/task context."""
    data = _ensure_context()
    if data.get(key) == value:
        return
    data[key] = value
    _context_data.set(data)


def delete_context_data(key: str):
    """Delete a key from the current async/task context."""
    data = _ensure_context()
    if key in data:
        del data[key]
        _context_data.set(data)


def get_context_data(key: Optional[str] = None, default: T = None) -> T:
    """Get a key from the current context, or the full dict if key is None."""
    data = _ensure_context()
    if key is None:
        return cast(T, data)
    return cast(T, data.get(key, default))


def clear_context_data():
    """Completely clear the context dict."""
    _context_data.set({})
