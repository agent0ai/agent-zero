import asyncio
from dataclasses import dataclass
import threading
from concurrent.futures import Future, InvalidStateError
from typing import Any, Callable, Optional, Coroutine, TypeVar, Awaitable

T = TypeVar("T")

THREAD_BACKGROUND = "Background"

# How long to wait for a loop's pending tasks to finish cancelling before it is
# torn down. Reached only when a task ignores cancellation; the bound is what
# keeps that from wedging the caller.
DRAIN_TIMEOUT = 10.0


class EventLoopThread:
    _instances: dict[str, "EventLoopThread"] = {}
    _lock = threading.Lock()

    loop: Optional[asyncio.AbstractEventLoop]
    thread: Optional[threading.Thread]
    # How many live ``DeferredTask``s share this thread. Instances are keyed by
    # name, so the count is what decides whether a task may stop the loop.
    _users: int

    def __init__(self, thread_name: str = THREAD_BACKGROUND) -> None:
        """Initialize the event loop thread."""
        self.thread_name = thread_name
        self._start()

    def __new__(cls, thread_name: str = THREAD_BACKGROUND):
        with cls._lock:
            if thread_name not in cls._instances:
                instance = super(EventLoopThread, cls).__new__(cls)
                # Set here rather than in ``__init__``: instances are shared by
                # name, so ``__init__`` runs again for every task that joins an
                # existing thread and would reset the count.
                instance._users = 0
                cls._instances[thread_name] = instance
            return cls._instances[thread_name]

    def acquire(self) -> None:
        """Registers a task as a user of this shared thread."""
        with self.__class__._lock:
            self._users += 1

    def release(self, terminate: bool) -> bool:
        """Drops a user, reporting whether the caller may tear the loop down.

        Only the last user may: the instance is shared by name, so stopping the
        loop while another task still runs on it would cancel that task's work.

        Unregistering happens under the same lock that makes the decision, so a
        task created after this point gets a fresh thread rather than one that
        is on its way out.
        """
        with self.__class__._lock:
            if self._users > 0:
                self._users -= 1
            if not (terminate and self._users == 0):
                return False
            if self.__class__._instances.get(self.thread_name) is self:
                del self.__class__._instances[self.thread_name]
            return True

    def _start(self):
        loop = getattr(self, "loop", None)
        thread = getattr(self, "thread", None)
        # A closed loop counts as absent, not just a null one: ``terminate()``
        # called from the loop's own thread cannot null these attributes out --
        # it is running inside the callback the loop still has to return from --
        # so a torn-down instance keeps a stale loop and thread attached.
        #
        # Both are rebuilt together. Replacing only the loop would leave it
        # unattended, since the surviving thread runs the loop it was handed.
        if loop is None or loop.is_closed() or thread is None or not thread.is_alive():
            self.loop = loop = asyncio.new_event_loop()
            self.thread = threading.Thread(
                target=self._run_event_loop,
                args=(loop,),
                daemon=True,
                name=self.thread_name,
            )
            self.thread.start()

    def _run_event_loop(self, loop: asyncio.AbstractEventLoop):
        # The loop is passed in rather than read from ``self.loop``: a restarted
        # instance replaces that attribute, and this thread must keep running
        # the loop it was created for.
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        finally:
            # Closed here rather than by ``terminate()``, which may itself be
            # running *on* this thread, where ``close()`` would raise because
            # the loop is still running.
            if not loop.is_closed():
                loop.close()

    def terminate(self):
        loop = getattr(self, "loop", None)
        thread = getattr(self, "thread", None)

        if not loop:
            return

        # ``terminate()`` can reach here from inside its own loop, via a task's
        # done-callback killing a child that shares this thread. Joining would
        # then wait on the current thread and deadlock.
        on_own_thread = thread is not None and thread is threading.current_thread()

        # Scheduled rather than conditional on ``is_running()``: a thread that
        # has started but not yet entered ``run_forever`` reports False, and
        # joining it would block for the full timeout.
        if on_own_thread:
            loop.call_soon(loop.stop)
        else:
            try:
                loop.call_soon_threadsafe(loop.stop)
            except RuntimeError:
                # Already closed.
                pass
            if thread is not None and thread.is_alive():
                thread.join(timeout=DRAIN_TIMEOUT)

        with self.__class__._lock:
            if self.__class__._instances.get(self.thread_name) is self:
                del self.__class__._instances[self.thread_name]

        if not on_own_thread:
            self.loop = None
            self.thread = None

    def run_coroutine(self, coro):
        self._start()
        if not self.loop:
            raise RuntimeError("Event loop is not initialized")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)


@dataclass
class ChildTask:
    task: "DeferredTask"
    terminate_thread: bool


class DeferredTask:
    def __init__(
        self,
        thread_name: str = THREAD_BACKGROUND,
    ):
        self.event_loop_thread = EventLoopThread(thread_name)
        self.event_loop_thread.acquire()
        self._released = False
        self._future: Optional[Future] = None
        self.children: list[ChildTask] = []
        self.func: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
        self.args: tuple[Any, ...] = ()
        self.kwargs: dict[str, Any] = {}

    def start_task(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._start_task()
        return self

    def add_done_callback(self, callback: Callable[[Future], Any]) -> None:
        if not self._future:
            raise RuntimeError("Task hasn't been started")
        self._future.add_done_callback(callback)

    def __del__(self):
        self.kill()

    def _start_task(self):
        if self.func is None:
            raise RuntimeError("Task callable is no longer available")

        if self._released:
            # ``restart()`` goes through ``kill()``, which drops this task's
            # claim on the thread. Re-register before using it again, or a
            # sibling's later ``kill(terminate_thread=True)`` would see a count
            # that no longer includes this task and stop the loop under it.
            self._released = False
            self.event_loop_thread.acquire()

        self._future = self.event_loop_thread.run_coroutine(
            self._run(self.func, self.args, self.kwargs)
        )
        if self._future:
            self._future.add_done_callback(self._on_task_done)

    def _on_task_done(self, future: Future):
        # Ensure child background tasks are always cleaned up once the parent finishes
        if future is self._future:
            self.kill_children()
            self._clear_call()

    def _clear_call(self) -> None:
        self.func = None
        self.args = ()
        self.kwargs = {}

    @staticmethod
    async def _run(func, args, kwargs):
        return await func(*args, **kwargs)

    def is_ready(self) -> bool:
        return self._future.done() if self._future else False

    def result_sync(self, timeout: Optional[float] = None) -> Any:
        if not self._future:
            raise RuntimeError("Task hasn't been started")
        try:
            return self._future.result(timeout)
        except TimeoutError:
            raise TimeoutError(
                "The task did not complete within the specified timeout."
            )

    async def result(self, timeout: Optional[float] = None) -> Any:
        if not self._future:
            raise RuntimeError("Task hasn't been started")

        loop = asyncio.get_running_loop()

        def _get_result():
            try:
                result = self._future.result(timeout)  # type: ignore
                # self.kill()
                return result
            except TimeoutError:
                raise TimeoutError(
                    "The task did not complete within the specified timeout."
                )

        return await loop.run_in_executor(None, _get_result)

    def kill(self, terminate_thread: bool = False) -> None:
        """Kill the task and optionally terminate its thread.

        ``terminate_thread`` is honoured only once this is the *last* task using
        the thread. ``EventLoopThread`` instances are shared by name, so
        stopping the loop while a sibling task still runs on it would cancel
        that sibling's work -- silently, since the cancellation surfaces only on
        the abandoned task's own future.
        """
        self.kill_children()
        if self._future and not self._future.done():
            self._future.cancel()
        self._clear_call()

        # ``release`` is idempotent per task: killing twice must not drop the
        # count twice and let the thread go while a sibling still needs it.
        may_terminate = False
        if not self._released:
            self._released = True
            may_terminate = self.event_loop_thread.release(terminate_thread)

        if not may_terminate:
            return

        event_loop_thread = self.event_loop_thread
        loop = event_loop_thread.loop
        if loop is None:
            return

        if event_loop_thread.thread is threading.current_thread():
            # Waiting on the drain from inside the loop would deadlock: the
            # coroutine can only advance on this thread, which the wait would be
            # occupying. The drain and the teardown are chained into a task
            # instead, so the loop is not stopped out from under the drain.
            # ``release()`` has already unregistered the instance, so a task
            # created before this finishes gets a fresh thread rather than this
            # one on its way out.
            async def drain_then_terminate() -> None:
                try:
                    await self._drain_event_loop_tasks()
                finally:
                    event_loop_thread.terminate()

            loop.create_task(drain_then_terminate())
            return

        if loop.is_running():
            try:
                cleanup_future = asyncio.run_coroutine_threadsafe(
                    self._drain_event_loop_tasks(), loop
                )
                # Bounded: an unbounded wait hangs the caller outright if a task
                # swallows cancellation, and this runs on the request thread
                # that serves chat deletion and task deletion.
                cleanup_future.result(timeout=DRAIN_TIMEOUT)
            except Exception:
                pass

        event_loop_thread.terminate()

    def kill_children(self) -> None:
        for child in self.children:
            child.task.kill(terminate_thread=child.terminate_thread)
        self.children = []

    def is_alive(self) -> bool:
        return self._future and not self._future.done()  # type: ignore

    def restart(self, terminate_thread: bool = False) -> None:
        if self.func is None:
            raise RuntimeError("Completed task cannot be restarted")
        func, args, kwargs = self.func, self.args, self.kwargs
        self.kill(terminate_thread=terminate_thread)
        self.start_task(func, *args, **kwargs)

    def add_child_task(
        self, task: "DeferredTask", terminate_thread: bool = False
    ) -> None:
        self.children.append(ChildTask(task, terminate_thread))

    async def _execute_in_task_context(
        self, func: Callable[..., T], *args, **kwargs
    ) -> T:
        """Execute a function in the task's context and return its result."""
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def execute_inside(self, func: Callable[..., T], *args, **kwargs) -> Awaitable[T]:
        if not self.event_loop_thread.loop:
            raise RuntimeError("Event loop is not initialized")

        future: Future = Future()

        def set_result(result: Any) -> None:
            try:
                future.set_result(result)
            except InvalidStateError:
                pass

        def set_exception(exception: BaseException) -> None:
            try:
                future.set_exception(exception)
            except InvalidStateError:
                pass

        async def wrapped():
            if not self.event_loop_thread.loop:
                raise RuntimeError("Event loop is not initialized")
            try:
                result = await self._execute_in_task_context(func, *args, **kwargs)
                # Keep awaiting until we get a concrete value
                while isinstance(result, Awaitable):
                    result = await result
                self.event_loop_thread.loop.call_soon_threadsafe(
                    set_result, result
                )
            except Exception as e:
                self.event_loop_thread.loop.call_soon_threadsafe(
                    set_exception, e
                )

        asyncio.run_coroutine_threadsafe(wrapped(), self.event_loop_thread.loop)
        return asyncio.wrap_future(future)

    @staticmethod
    async def _drain_event_loop_tasks():
        """Cancel and await all pending tasks on the current event loop."""
        loop = asyncio.get_running_loop()
        current_task = asyncio.current_task(loop=loop)
        pending = [
            task
            for task in asyncio.all_tasks(loop=loop)
            if task is not current_task
        ]
        if not pending:
            return
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
