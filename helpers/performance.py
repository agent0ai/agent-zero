import functools
import inspect
from pyinstrument import Profiler

def trace_performance(*, show_all=False, color=True, unicode=True):
    """
    Decorator that profiles a function and prints a call tree when it finishes.

    Works with both synchronous and asynchronous functions.
    """

    def decorator(func):
        is_coro = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            profiler = Profiler()
            profiler.start()
            try:
                return await func(*args, **kwargs)
            finally:
                profiler.stop()
                print(f"\n=== Performance trace: {func.__module__}.{func.__qualname__} (async) ===")
                print(
                    profiler.output_text(
                        color=color,
                        unicode=unicode,
                        show_all=show_all,
                    )
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            profiler = Profiler()
            profiler.start()
            try:
                return func(*args, **kwargs)
            finally:
                profiler.stop()
                print(f"\n=== Performance trace: {func.__module__}.{func.__qualname__} ===")
                print(
                    profiler.output_text(
                        color=color,
                        unicode=unicode,
                        show_all=show_all,
                    )
                )

        return async_wrapper if is_coro else sync_wrapper

    return decorator