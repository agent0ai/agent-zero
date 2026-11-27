"""Private browser sink and a capture pipe whose stdin owns its lifetime."""
import asyncio
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

DIRECTORY = Path('/run/a0-browser-audio')
LIBRARY = '/usr/local/lib/tuxee-audio/lib'


def environment():
    return {'PULSE_SERVER': f'unix:{DIRECTORY}/native', 'PULSE_COOKIE': str(DIRECTORY / 'cookie'),
            'LD_LIBRARY_PATH': f'{LIBRARY}:{LIBRARY}/pulseaudio'}


class BrowserAudio:
    def __init__(self):
        self.process = None

    def start(self):
        if self.process and self.process.poll() is None:
            return
        self.close()
        DIRECTORY.mkdir(parents=True, mode=0o700)
        cookie = DIRECTORY / 'cookie'
        cookie.write_bytes(secrets.token_bytes(256))
        cookie.chmod(0o600)
        config = DIRECTORY / 'default.pa'
        # Monitor capture cannot retract samples when Chromium rewinds a sink.
        config.write_text('load-module module-null-sink sink_name=browser format=s16le channels=2 rate=48000 norewinds=true\n'
                          'set-default-sink browser\nset-default-source browser.monitor\n'
                          f'load-module module-native-protocol-unix socket={DIRECTORY}/native auth-cookie={cookie}\n')
        try:
            with (DIRECTORY / 'audio.log').open('ab') as log:
                self.process = subprocess.Popen([
                    'tuxee-pulseaudio', '--daemonize=no', '--exit-idle-time=-1', '--use-pid-file=no',
                    '--disable-shm', '--high-priority=no', '--realtime=no', '--resample-method=ffmpeg', '-n', '-F', str(config),
                ], env={**os.environ, 'PULSE_RUNTIME_PATH': str(DIRECTORY), 'PULSE_STATE_PATH': str(DIRECTORY)},
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log)
            deadline = time.monotonic() + 5
            while self.process.poll() is None and time.monotonic() < deadline:
                if (DIRECTORY / 'native').is_socket():
                    return
                time.sleep(.02)
            raise RuntimeError('Browser audio server did not become ready')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process = None
        shutil.rmtree(DIRECTORY, ignore_errors=True)


async def capture():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin.buffer)
    process = None
    tasks = []
    try:
        process = await asyncio.create_subprocess_exec(
            'tuxee-pacat', '--record', '--raw', '--format=s16le', '--rate=48000', '--channels=2',
            '--latency-msec=20', '--process-time-msec=10', '--device=browser.monitor',
            env={**os.environ, **environment()}, stdin=asyncio.subprocess.DEVNULL, stdout=sys.stdout.buffer)
        tasks = [asyncio.create_task(reader.read(1)), asyncio.create_task(process.wait())]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        transport.close()
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), 2)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(capture())
