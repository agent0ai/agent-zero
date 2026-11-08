"""Browser-only pipe protocol: concurrent calls, frames and acknowledged cancellation."""
import asyncio
import contextlib
import inspect
import json
import os
import sys

sys.path.insert(0, '/app')
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/opt/browsers'
from plugins._browser.sandbox.runtime import _BrowserRuntimeCore
from plugins._browser.sandbox import display

MAX_MESSAGE = 128 * 1024 * 1024


async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader(limit=MAX_MESSAGE)
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin.buffer)
    transport, protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout.buffer)
    writer = asyncio.StreamWriter(transport, protocol, None, loop)
    write_lock = asyncio.Lock()
    tasks, frames = {}, {}
    core = None
    methods = {name for name, fn in inspect.getmembers(_BrowserRuntimeCore, inspect.iscoroutinefunction)
               if not name.startswith('_') and name != 'ensure_started'}

    async def send(value):
        data = json.dumps(value, separators=(',', ':')).encode() + b'\n'
        if len(data) > MAX_MESSAGE:
            raise ValueError('Browser response exceeds the IPC limit')
        async with write_lock:
            writer.write(data)
            await writer.drain()

    async def invoke(message):
        nonlocal core
        request_id = message['id']
        try:
            method = message['method']
            if method == 'init':
                if core is not None:
                    raise ValueError('Browser is already initialized')
                options = message['kwargs']
                display._keyboard = options.pop('keyboard')
                core = _BrowserRuntimeCore('shared', **options,
                    on_tabs=lambda tabs: loop.create_task(send({'tabs': tabs})))
                result = True
            else:
                if method not in methods or core is None:
                    raise ValueError('Unsupported browser operation')
                context = core.request_context_id.set(message['context_id'])
                config = core.request_options.set(message.get('options', {}))
                uploads = core.request_uploads.set(message.get('uploads', {}))
                try:
                    args, kwargs = message['args'], message['kwargs']
                    if method == 'attach_screencast_consumer':
                        stream = args[0]
                        async def consume(frame):
                            frame_id = os.urandom(16).hex()
                            future = frames[frame_id] = loop.create_future()
                            try:
                                await send({'stream': stream, 'frame_id': frame_id, 'frame': frame})
                                await asyncio.wait_for(future, 15)
                            finally:
                                frames.pop(frame_id, None)
                        def stopped():
                            loop.create_task(send({'stream': stream, 'stopped': True}))
                        result = await core.attach_screencast_consumer(stream, consume, stopped)
                    else:
                        result = await getattr(core, method)(*args, **kwargs)
                finally:
                    core.request_context_id.reset(context)
                    core.request_options.reset(config)
                    core.request_uploads.reset(uploads)
            await send({'id': request_id, 'result': result})
        except asyncio.CancelledError:
            # _evaluate_page has completed its interruption/recovery before this ack.
            await send({'id': request_id, 'cancelled': True})
        except Exception as exc:
            await send({'id': request_id, 'error': str(exc), 'error_type': type(exc).__name__})
        finally:
            tasks.pop(request_id, None)

    try:
        while line := await reader.readline():
            message = json.loads(line)
            if 'cancel' in message:
                task = tasks.get(message['cancel'])
                if task:
                    task.cancel()
            elif 'frame_ack' in message:
                future = frames.get(message['frame_ack'])
                if future and not future.done():
                    future.set_result(None)
            else:
                request_id = message['id']
                if request_id in tasks:
                    raise ValueError('Duplicate browser request')
                tasks[request_id] = asyncio.create_task(invoke(message))
    finally:
        for task in list(tasks.values()):
            task.cancel()
        await asyncio.gather(*list(tasks.values()), return_exceptions=True)
        if core:
            with contextlib.suppress(Exception):
                await core.close()
            core.interactive_view.close()
        writer.close()


if __name__ == '__main__':
    asyncio.run(main())
