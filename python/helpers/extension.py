from abc import abstractmethod
from typing import Any
from python.helpers import extract_tools, files
from python.helpers import cache
from typing import TYPE_CHECKING
from functools import wraps
import asyncio
import inspect

if TYPE_CHECKING:
    from agent import Agent


DEFAULT_EXTENSIONS_FOLDER = "python/extensions"
USER_EXTENSIONS_FOLDER = "usr/extensions"

_CACHE_AREA = "extension_folder_classes(extensions)(plugins)"
cache.toggle_area(_CACHE_AREA, False) # cache off for now

_guard_cache: list | None = None


class _Unset:
    pass


_UNSET = _Unset()


# decorator to enable implicit extension points in existing functions
def extensible(func):
    """Make a function emit two implicit extension points around its execution.

    The decorator derives two extension point names from the wrapped function:

    - ``{func.__module__}.{func.__name__}-start``
    - ``{func.__module__}.{func.__name__}-end``

    When the wrapped function is called, the decorator builds a mutable ``data``
    payload and passes it to both extension points via ``call_extensions``:

    - ``data["args"]``: the original positional arguments tuple
    - ``data["kwargs"]``: the original keyword arguments dict
    - ``data["result"]``: initialized to an internal sentinel; extensions may
      set this to short-circuit the wrapped function
    - ``data["exception"]``: initialized to an internal sentinel; extensions may
      set this to a ``BaseException`` instance to force-raise

    Behavior:

    - ``-start`` extensions run first and may mutate ``data["args"]`` /
      ``data["kwargs"]``, set ``data["result"]`` to skip calling ``func``, or set
      ``data["exception"]`` to abort by raising.
    - If ``data["result"]`` is still unset, the decorator calls ``func`` (awaiting
      it if it is async) and stores either the return value into ``data["result"]``
      or the raised error into ``data["exception"]``.
    - ``-end`` extensions run last and may further transform the outcome by
      rewriting ``data["result"]`` or replacing/clearing ``data["exception"]``.

    Finally, if ``data["exception"]`` contains an exception it is raised;
    otherwise ``data["result"]`` is returned.
    """
    @wraps(func)
    async def _inner_async(*args, **kwargs):
        from agent import Agent

        # prepare extension points data
        module_name = getattr(func, "__module__", "")
        qual_name = getattr(func, "__qualname__", "")

        # skip if extension point cannot be determined
        if not module_name or not qual_name:
            return await func(*args, **kwargs)

        start_point = f"{module_name}.{qual_name}-start"
        end_point = f"{module_name}.{qual_name}-end"

        def _get_agent() -> "Agent|None":
            candidate = kwargs.get("agent")
            if isinstance(candidate, Agent) and bool(getattr(candidate, "__dict__", None)):
                return candidate

            for a in args:
                if isinstance(a, Agent) and bool(getattr(a, "__dict__", None)):
                    return a

            return None

        # try to find agent instance for better extension determination
        agent = _get_agent()

        # build extension data object - func input/output
        data = {
            "args": args,
            "kwargs": kwargs,
            "result": _UNSET,
            "exception": _UNSET,
        }

        # call start extensions, these can modify inputs, produce output or exception
        await call_extensions(start_point, agent=agent, data=data)

        # if there is an explicit exception set, raise it
        exc = data.get("exception")
        if isinstance(exc, BaseException):
            raise exc

        # if there is no result set, call the original function
        if data.get("result") is _UNSET:
            try:
                if inspect.iscoroutinefunction(func):
                    data["result"] = await func(*args, **kwargs)
                else:
                    data["result"] = func(*args, **kwargs)
            except Exception as e:
                data["exception"] = e

        # call end extensions, these can modify outputs or exception
        agent = _get_agent()
        await call_extensions(end_point, agent=agent, data=data)

        # if there's an exception, raise it
        exc = data.get("exception")
        if isinstance(exc, BaseException):
            raise exc

        # if there's a result, return it
        result = data.get("result")
        return None if result is _UNSET else result

    if inspect.iscoroutinefunction(func):
        return _inner_async

    @wraps(func)
    def _inner_sync(*args, **kwargs):
        return asyncio.run(_inner_async(*args, **kwargs))

    return _inner_sync


class Extension:

    def __init__(self, agent: "Agent|None", **kwargs):
        self.agent: "Agent|None" = agent
        self.kwargs = kwargs

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass


def _get_guard_handlers() -> list:
    global _guard_cache
    if _guard_cache is not None:
        return _guard_cache
    from importlib.metadata import entry_points

    eps = entry_points(group="agent_zero.guards")
    _guard_cache = []
    for ep in eps:
        try:
            _guard_cache.append(ep.load())
        except Exception:
            from python.helpers.print_style import PrintStyle
            PrintStyle.warning(f"Failed to load guard entry_point: {ep.name}")
    return _guard_cache


async def call_extensions(
    extension_point: str, agent: "Agent|None" = None, **kwargs
) -> Any:
    from python.helpers import projects, subagents, plugins

    # build mutable event dict from kwargs
    event: dict[str, Any] = dict(**kwargs)
    event.setdefault("extension_point", extension_point)
    event.setdefault("agent", agent)

    # search for extension folders in all agent's paths
    paths = subagents.get_paths(
        agent, "extensions", extension_point, default_root="python"
    )

    # Add plugin backend extension paths (plugins/*/extensions/python/{extension_point})
    plugin_paths = plugins.get_enabled_plugin_paths(
        agent, "extensions", "python", extension_point
    )
    paths.extend(p for p in plugin_paths if p not in paths)

    all_exts = [cls for path in paths for cls in _get_extensions(path)]

    # merge: first ocurrence of file name is the override
    unique = {}
    for cls in all_exts:
        file = _get_file_from_module(cls.__module__)
        if file not in unique:
            unique[file] = cls
    classes = sorted(
        unique.values(), key=lambda cls: _get_file_from_module(cls.__module__)
    )

    # execute unique file-based extensions (no fault isolation — preserve existing behavior)
    for cls in classes:
        await cls(agent=agent).execute(_event=event, **kwargs)

    # execute entry_point guard handlers (with fault isolation per handler)
    for handler in _get_guard_handlers():
        try:
            await handler(event, agent=agent)
        except Exception:
            from python.helpers.print_style import PrintStyle
            PrintStyle.error(f"Guard handler {handler!r} failed for '{extension_point}'")

    return event


def _get_file_from_module(module_name: str) -> str:
    return module_name.split(".")[-1]


def _get_extensions(folder: str):
    folder = files.get_abs_path(folder)
    cached = cache.get(_CACHE_AREA, folder)
    if cached is not None:
        return cached

    if not files.exists(folder):
        return []

    classes = extract_tools.load_classes_from_folder(folder, "*", Extension)
    cache.add(_CACHE_AREA, folder, classes)
    return classes
