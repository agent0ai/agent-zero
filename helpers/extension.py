from abc import abstractmethod
from typing import Any, Awaitable, Type, cast
from helpers import extract_tools, files
from helpers import cache, subagents
from typing import TYPE_CHECKING
from functools import wraps
import inspect

if TYPE_CHECKING:
    from agent import Agent


DEFAULT_EXTENSIONS_FOLDER = "python/extensions"
USER_EXTENSIONS_FOLDER = "usr/extensions"

_CACHE_AREA = "extension_folder_classes(extensions)(plugins)"
cache.toggle_area(_CACHE_AREA, False)  # cache off for now


class _Unset:
    pass


_UNSET = _Unset()


# decorator to enable implicit extension points in existing functions
def extensible(func):
    """Make a function emit two implicit extension points around its execution.

    The decorator derives two extension point names from the wrapped function:

    - ``{func.__module__}_{func.__qualname__}_start`` with `.` replaced by `_`
    - ``{func.__module__}_{func.__qualname__}_end`` with `.` replaced by `_`

    When the wrapped function is called, the decorator builds a mutable ``data``
    payload and passes it to both extension points:

    - ``data["args"]``: positional args (extensions may replace/mutate)
    - ``data["kwargs"]``: keyword args (extensions may replace/mutate)
    - ``data["result"]``: initialized to an internal sentinel; extensions may set
      this to short-circuit the wrapped function
    - ``data["exception"]``: initialized to an internal sentinel; extensions may
      set this to a ``BaseException`` instance to force-raise

    Sync functions call ``call_extensions_sync``. Async functions call
    ``call_extensions_async``.

    Behavior:

    - ``-start`` extensions run first and may mutate inputs or set
      ``data["result"]`` / ``data["exception"]``.
    - If ``data["result"]`` is still unset, the decorator calls the wrapped
      function using the possibly modified ``data["args"]`` / ``data["kwargs"]``.
    - ``-end`` extensions run last and may rewrite ``data["result"]`` or replace /
      clear ``data["exception"]``.

    Finally, if ``data["exception"]`` contains an exception it is raised;
    otherwise ``data["result"]`` is returned.
    """

    def _get_agent(args, kwargs):
        from agent import Agent

        candidate = kwargs.get("agent")
        if isinstance(candidate, Agent) and bool(getattr(candidate, "__dict__", None)):
            return candidate

        for a in args:
            if isinstance(a, Agent) and bool(getattr(a, "__dict__", None)):
                return a

        return None

    def _prepare_inputs(args, kwargs):
        module_name = getattr(func, "__module__", "").replace(".", "_")
        qual_name = getattr(func, "__qualname__", "").replace(".", "_")
        if not module_name or not qual_name:
            return None

        start_point = f"{module_name}_{qual_name}_start"
        end_point = f"{module_name}_{qual_name}_end"
        agent = _get_agent(args, kwargs)

        data = {
            "args": args,
            "kwargs": kwargs,
            "result": _UNSET,
            "exception": None,
        }

        return start_point, end_point, agent, data

    def _process_result(data):
        exc = data.get("exception")
        if isinstance(exc, BaseException):
            raise exc

        return data.get("result")

    def _call_original(data):
        call_args = data.get("args")
        call_kwargs = data.get("kwargs")

        if not isinstance(call_args, tuple):
            call_args = (call_args,)
        if not isinstance(call_kwargs, dict):
            call_kwargs = {}

        try:
            data["result"] = func(*call_args, **call_kwargs)
        except Exception as e:
            data["exception"] = e
            return _UNSET

    async def _run_async(*args, **kwargs):
        prepared = _prepare_inputs(args, kwargs)
        if prepared is None:
            return await func(*args, **kwargs)

        start_point, end_point, agent, data = prepared

        # call pre-extensions
        await call_extensions_async(start_point, agent=agent, data=data)

        # call the original if pre-extensions don't return a result
        if (result := _process_result(data)) is _UNSET:
            _call_original(data)
            try:
                data["result"] = await data["result"]
            except Exception as e:
                data["exception"] = e

        # call post-extensions
        await call_extensions_async(end_point, agent=agent, data=data)

        result = _process_result(data)
        return None if result is _UNSET else result

    def _run_sync(*args, **kwargs):
        prepared = _prepare_inputs(args, kwargs)
        if prepared is None:
            return func(*args, **kwargs)

        start_point, end_point, agent, data = prepared

        # call pre-extensions
        call_extensions_sync(start_point, agent=agent, data=data)

        # call the original if pre-extensions don't return a result
        if (result := _process_result(data)) is _UNSET:
            _call_original(data)

        # call post-extensions
        call_extensions_sync(end_point, agent=agent, data=data)

        result = _process_result(data)
        return None if result is _UNSET else result

    if inspect.iscoroutinefunction(func):
        return wraps(func)(_run_async)

    return wraps(func)(_run_sync)


class Extension:

    def __init__(self, agent: "Agent|None", **kwargs):
        self.agent: "Agent|None" = agent
        self.kwargs = kwargs

    @abstractmethod
    def execute(self, **kwargs) -> None | Awaitable[None]:
        pass


async def call_extensions_async(
    extension_point: str, agent: "Agent|None" = None, **kwargs
):
    # fetch classes for this extension point and agent
    classes = _get_extension_classes(extension_point, agent=agent, **kwargs)

    # execute unique extensions
    for cls in classes:
        result = cls(agent=agent).execute(**kwargs)
        if isinstance(result, Awaitable):
            await result


def call_extensions_sync(extension_point: str, agent: "Agent|None" = None, **kwargs):
    # fetch classes for this extension point and agent
    classes = _get_extension_classes(extension_point, agent=agent, **kwargs)

    # execute unique extensions
    for cls in classes:
        result = cls(agent=agent).execute(**kwargs)
        if isinstance(result, Awaitable):
            raise ValueError(
                f"Extension {cls.__name__} returned awaitable in sync mode"
            )


def get_webui_extensions(
    agent: "Agent | None", extension_point: str, filters: list[str] | None = None
):
    entries: list[str] = []
    effective_filters = filters or ["*"]

    # search for extension folders in all agent's paths
    folders = subagents.get_paths(
        agent,
        "extensions/webui",
        extension_point,
    )

    extensions = []

    for folder in folders:
        for filter in effective_filters:
            pattern = files.get_abs_path(folder, filter)
            extensions.extend(files.find_existing_paths_by_pattern(pattern))

    for extension in extensions:
        rel_path = files.deabsolute_path(extension)
        entries.append(rel_path)

    return entries


def _get_extension_classes(
    extension_point: str, agent: "Agent|None" = None, **kwargs
) -> list[Type[Extension]]:
    # search for extension folders in all agent's paths
    paths = subagents.get_paths(agent, "extensions/python", extension_point)

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
    return classes


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